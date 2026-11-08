"""Quản lý bộ mẫu từ trang quản trị (Mục 10.2, 10.4, 10.5): services/template_store.py, routes/admin_templates.py.

Chạy trên một bản sao tạm của bộ mẫu, không đụng vào templates/ thật.
"""
import io
import json
import shutil
import zipfile

import docx
import pytest

import config
from conftest import read_zip
from services import auth, render_service
from services.sample_data import build_sample_payload

NAME = "Tạm dừng công ty TNHH 1 TV"
CSRF = {auth.CSRF_HEADER: auth.CSRF_VALUE}
PASSWORD = "mat-khau-thu-nghiem-123"
MARKER = "NỘI DUNG PHIÊN BẢN MỚI THỬ NGHIỆM"


@pytest.fixture
def env(tmp_path, monkeypatch):
    root = tmp_path / "templates"
    shutil.copytree(config.TEMPLATES_DIR / NAME, root / NAME)
    for mod in (config, render_service):
        monkeypatch.setattr(mod, "TEMPLATES_DIR", root)
    monkeypatch.setattr(config, "TEMPLATE_DRAFTS_DIR", tmp_path / "drafts")
    monkeypatch.setattr(config, "TEMPLATE_VERSIONS_DIR", tmp_path / "versions")
    monkeypatch.setattr(config, "ADMIN_DB_PATH", tmp_path / "admin.sqlite3")
    schema = json.loads((root / NAME / "_schema.json").read_text(encoding="utf-8"))
    return {"root": root, "id": schema["id"], "schema": schema}


@pytest.fixture
def api(client, env):
    auth.create_user("quantri", PASSWORD)
    client.cookies.clear()
    r = client.post("/api/admin/login", json={"username": "quantri", "password": PASSWORD}, headers=CSRF)
    assert r.status_code == 200
    yield client
    client.cookies.clear()


def first_docx(env):
    return sorted(p for p in (env["root"] / NAME).glob("*.docx"))[0]


def docx_with_marker(path, marker=MARKER):
    d = docx.Document(str(path))
    d.add_paragraph(marker)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def upload(api, draft_id, name, data):
    return api.post(f"/api/admin/drafts/{draft_id}/files", headers=CSRF,
                    files={"file": (name, data, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})


def render_live(api, env):
    payload, _, _ = build_sample_payload(env["schema"], 3)
    r = api.post("/api/documents/generate", json=payload)
    assert r.status_code == 200, r.text[:300]
    return "\n".join(read_zip(r.content).values())


def new_draft(api, env):
    r = api.post(f"/api/admin/templates/{env['id']}/drafts", headers=CSRF)
    assert r.status_code == 200, r.text
    return r.json()


# ---------- Quyền ----------

def test_requires_login(client, env):
    client.cookies.clear()
    assert client.get("/api/admin/templates").status_code == 401
    assert client.post(f"/api/admin/templates/{env['id']}/drafts", headers=CSRF).status_code == 401


def test_mutations_require_csrf(api, env):
    assert api.post(f"/api/admin/templates/{env['id']}/drafts").status_code == 403


# ---------- Luồng chính: nháp -> sinh thử -> xuất bản -> quay lại ----------

def test_full_publish_and_rollback_flow(api, env):
    templates = api.get("/api/admin/templates").json()["templates"]
    assert [(t["id"], t["version"]) for t in templates] == [(env["id"], 1)]

    draft = new_draft(api, env)
    assert draft["files"] == sorted(p.name for p in (env["root"] / NAME).glob("*.docx"))
    target = first_docx(env)
    assert upload(api, draft["id"], target.name, docx_with_marker(target)).status_code == 200

    lint = api.get(f"/api/admin/drafts/{draft['id']}/lint").json()
    assert lint["summary"]["error"] == 0

    # Sinh thử: thấy nội dung mới; bộ mẫu đang dùng chưa đổi
    r = api.post(f"/api/admin/drafts/{draft['id']}/preview", headers=CSRF)
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    assert MARKER in "\n".join(read_zip(r.content).values())
    assert MARKER not in render_live(api, env)

    # Xuất bản cần ghi chú
    assert api.post(f"/api/admin/drafts/{draft['id']}/publish", json={"note": " "}, headers=CSRF).status_code == 400
    r = api.post(f"/api/admin/drafts/{draft['id']}/publish", headers=CSRF,
                 json={"note": "Cập nhật mẫu theo thông tư mới", "legal_basis": "Thông tư thử nghiệm",
                       "effective_from": "2026-12-01"})
    assert r.status_code == 200 and r.json() == {"version": 2}
    assert MARKER in render_live(api, env)
    live_schema = json.loads((env["root"] / NAME / "_schema.json").read_text(encoding="utf-8"))
    assert (live_schema["version"], live_schema["legal_basis"], live_schema["effective_from"]) == \
        (2, "Thông tư thử nghiệm", "2026-12-01")
    assert api.get(f"/api/admin/drafts/{draft['id']}").status_code == 404, "Bản nháp được dọn sau khi xuất bản"

    versions = api.get(f"/api/admin/templates/{env['id']}/versions").json()["versions"]
    assert [(v["version"], v["source"], v["current"], v["username"]) for v in versions] == \
        [(2, "publish", True, "quantri"), (1, "initial", False, "quantri")]

    # Quay lại bản 1: thành phiên bản 3, nội dung như bản ban đầu
    r = api.post(f"/api/admin/templates/{env['id']}/rollback", json={"version": 1}, headers=CSRF)
    assert r.status_code == 200 and r.json() == {"version": 3}
    assert MARKER not in render_live(api, env)
    versions = api.get(f"/api/admin/templates/{env['id']}/versions").json()["versions"]
    assert [(v["version"], v["source"], v["note"]) for v in versions][0] == (3, "rollback", "Quay lại phiên bản 1")
    assert api.post(f"/api/admin/templates/{env['id']}/rollback", json={"version": 9}, headers=CSRF).status_code == 404


def test_lint_errors_block_publish(api, env):
    draft = new_draft(api, env)
    # File .docx chưa khai báo trong khối documents -> E003
    assert upload(api, draft["id"], "99. File thêm.docx", docx_with_marker(first_docx(env))).status_code == 200
    r = api.post(f"/api/admin/drafts/{draft['id']}/publish", json={"note": "thử"}, headers=CSRF)
    assert r.status_code == 422
    assert any(e["code"] == "E003" for e in r.json()["errors"])
    assert not (env["root"] / NAME / "99. File thêm.docx").exists(), "Bộ mẫu đang dùng không bị đổi"
    # Xóa file thừa thì xuất bản được
    assert api.delete(f"/api/admin/drafts/{draft['id']}/files/99. File thêm.docx", headers=CSRF).status_code == 200
    assert api.post(f"/api/admin/drafts/{draft['id']}/publish", json={"note": "thử"}, headers=CSRF).status_code == 200


def test_stale_draft_cannot_overwrite_newer_publish(api, env):
    a, b = new_draft(api, env), new_draft(api, env)
    assert api.post(f"/api/admin/drafts/{a['id']}/publish", json={"note": "A"}, headers=CSRF).status_code == 200
    r = api.post(f"/api/admin/drafts/{b['id']}/publish", json={"note": "B"}, headers=CSRF)
    assert r.status_code == 409 and "bản nháp mới" in r.json()["detail"]


# ---------- Kiểm tra file tải lên ----------

@pytest.mark.parametrize("name", ["../thoat.docx", "a/b.docx", "mau.doc", "mau.txt", "~$khoa.docx", "_an.docx", ""])
def test_rejects_bad_file_names(api, env, name):
    draft = new_draft(api, env)
    r = upload(api, draft["id"], name or "x", docx_with_marker(first_docx(env))) if name else \
        api.post(f"/api/admin/drafts/{draft['id']}/files", headers=CSRF, files={"file": ("", b"x")})
    assert r.status_code in (400, 422)
    assert not any(p.name.startswith("thoat") for p in config.TEMPLATE_DRAFTS_DIR.parent.rglob("thoat*"))


def test_rejects_bad_docx_content(api, env):
    draft = new_draft(api, env)
    assert upload(api, draft["id"], "a.docx", b"khong phai docx").status_code == 400
    # Có macro
    good = docx_with_marker(first_docx(env))
    buf = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(good)) as src, zipfile.ZipFile(buf, "w") as dst:
        for item in src.infolist():
            dst.writestr(item, src.read(item.filename))
        dst.writestr("word/vbaProject.bin", b"macro")
    r = upload(api, draft["id"], "a.docx", buf.getvalue())
    assert r.status_code == 400 and "macro" in r.json()["detail"]
    # Quá lớn
    from services import template_store
    r = upload(api, draft["id"], "a.docx", b"0" * (template_store.MAX_DOCX_BYTES + 1))
    assert r.status_code == 400 and "quá lớn" in r.json()["detail"]


def test_schema_edit_cannot_change_identity(api, env):
    draft = new_draft(api, env)
    schema = dict(draft["schema"], id="bo-mau-khac")
    r = api.put(f"/api/admin/drafts/{draft['id']}/schema", json=schema, headers=CSRF)
    assert r.status_code == 400 and "id" in r.json()["detail"]
    schema = dict(draft["schema"], description="Mô tả mới")
    r = api.put(f"/api/admin/drafts/{draft['id']}/schema", json=schema, headers=CSRF)
    assert r.status_code == 200 and r.json()["schema"]["description"] == "Mô tả mới"


def test_discard_draft(api, env):
    draft = new_draft(api, env)
    assert api.delete(f"/api/admin/drafts/{draft['id']}", headers=CSRF).status_code == 200
    assert api.get(f"/api/admin/drafts/{draft['id']}").status_code == 404
    assert api.get("/api/admin/drafts/../../etc").status_code == 404


# ---------- Gợi ý trường từ tên biến (Mục 10.3) ----------

@pytest.mark.parametrize("key, typ", [
    ("ngay_ky_hop_dong", "date"), ("ddpl_so_cccd", "cccd"), ("phi_dich_vu_so", "money"), ("von_gop_so", "money"),
    ("ty_le_von", "percent"), ("email_cong_ty", "email"), ("sdt_cong_ty", "phone"), ("ma_so_thue_moi", "mst_lookup"),
    ("so_quyet_dinh", "text"), ("ly_do", "text"),
])
def test_guess_type(key, typ):
    from tools.schema_suggest import guess_type
    assert guess_type(key) == typ


def test_humanize():
    from tools.schema_suggest import humanize
    assert humanize("ngay_ky_hop_dong") == "Ngày ký hợp đồng"
    assert humanize("nguoi_lien_he") == "Người liên hệ"


def docx_with_variables(path, text):
    d = docx.Document(str(path))
    d.add_paragraph(text)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def test_suggest_and_apply_fields(api, env):
    draft = new_draft(api, env)
    assert api.get(f"/api/admin/drafts/{draft['id']}/suggestions").json()["suggestions"] == []
    target = first_docx(env)
    text = ("Liên hệ: {{ nguoi_lien_he_ho_ten }}, CCCD {{ nguoi_lien_he_so_cccd }}. "
            "Phí: {{ phi_dich_vu_so }}. Ký ngày {{ ngay_ky_hop_dong }}. Ghi chú: {{ ghi_chu_them }}")
    assert upload(api, draft["id"], target.name, docx_with_variables(target, text)).status_code == 200
    lint = api.get(f"/api/admin/drafts/{draft['id']}/lint").json()
    assert {f["code"] for f in lint["findings"] if "nguoi_lien_he" in f["message"]} == {"W021"}

    got = api.get(f"/api/admin/drafts/{draft['id']}/suggestions").json()["suggestions"]
    assert [(s["key"], s["type"]) for s in got] == [
        ("ghi_chu_them", "text"), ("ngay_ky_hop_dong", "date"), ("nguoi_lien_he", "person"), ("phi_dich_vu_so", "money")]
    assert next(s for s in got if s["key"] == "nguoi_lien_he")["variables"] == \
        ["nguoi_lien_he_ho_ten", "nguoi_lien_he_so_cccd"]

    r = api.post(f"/api/admin/drafts/{draft['id']}/suggestions/apply", json={"keys": ["khong_co"]}, headers=CSRF)
    assert r.status_code == 400
    r = api.post(f"/api/admin/drafts/{draft['id']}/suggestions/apply", headers=CSRF,
                 json={"keys": ["nguoi_lien_he", "phi_dich_vu_so", "ngay_ky_hop_dong"]})
    assert r.status_code == 200
    step = next(st for st in r.json()["schema"]["steps"] if st["id"] == "bo_sung")
    assert [(f["key"], f["type"]) for f in step["fields"]] == [  # theo thứ tự tên trường
        ("ngay_ky_hop_dong", "date"), ("nguoi_lien_he", "person"), ("phi_dich_vu_so", "money")]

    # Sau khi thêm: các biến đó có nguồn, chỉ còn ghi_chu_them; schema vẫn đúng đặc tả (không có lỗi)
    lint = api.get(f"/api/admin/drafts/{draft['id']}/lint").json()
    w021 = [f["message"] for f in lint["findings"] if f["code"] == "W021"]
    assert len(w021) == 1 and "ghi_chu_them" in w021[0]
    assert lint["summary"]["error"] == 0
    assert [s["key"] for s in api.get(f"/api/admin/drafts/{draft['id']}/suggestions").json()["suggestions"]] == ["ghi_chu_them"]
    # Sinh thử: các ô mới được điền dữ liệu mẫu
    r = api.post(f"/api/admin/drafts/{draft['id']}/preview", headers=CSRF)
    text_out = "\n".join(read_zip(r.content).values())
    assert "Liên hệ: NGUYỄN VĂN THỬ" in text_out and "Ký ngày 01/01/1990" in text_out
