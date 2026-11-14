"""Phễu khách: bước để lại số Zalo trước khi tải, lưu khách, email báo, tờ hướng dẫn trong file .zip, trang quản trị."""
import io
import zipfile

import docx
import pytest

import config
from conftest import build_payload, docx_text
from services import auth, kinh_doanh, leads

CSRF = {auth.CSRF_HEADER: auth.CSRF_VALUE}
LEAD = {"name": "Nguyễn Văn Thử", "phone": "0901 234 567", "role": "chu_dn", "delegated": False, "consent": True,
        "source": {"utm_source": "google", "utm_campaign": "mau-ho-so", "ref": "ketoan01", "khac": "bỏ qua"}}


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ADMIN_DB_PATH", tmp_path / "admin.sqlite3")
    monkeypatch.setattr(config, "LEAD_REQUIRED", True)
    sent = []
    monkeypatch.setattr(leads, "notify", lambda rec: sent.append(rec) or True)
    yield sent


def generate(client, name="Thành lập mới công ty TNHH 2 TV", lead=LEAD):
    payload, _, _ = build_payload(name, 2)
    if lead is not None:
        payload["lead"] = lead
    return client.post("/api/documents/generate", json=payload), payload


def test_download_requires_contact_and_consent(client):
    r, _ = generate(client, lead=None)
    assert r.status_code == 422 and r.json()["lead_error"]
    for bad, msg in [({"phone": "123"}, "10 chữ số"), ({"consent": False}, "đồng ý"), ({"name": " "}, "họ tên")]:
        r, _ = generate(client, lead=dict(LEAD, **bad))
        assert r.status_code == 422 and msg in r.json()["detail"], bad


def test_lead_saved_without_personal_documents(client, temp_db):
    r, payload = generate(client)
    assert r.status_code == 200
    rows = leads.list_leads()
    assert len(rows) == 1
    row = rows[0]
    assert (row["name"], row["phone"], row["role"], row["status"]) == ("Nguyễn Văn Thử", "0901234567", "chu_dn", "moi")
    assert row["template_id"] == "thanh-lap-moi-cong-ty-tnhh-2-tv" and row["package"] == "khoi_nghiep"
    assert row["members"] == 2 and row["company_name"] == payload["data"]["ten_cong_ty_vn"]
    assert row["source"] == {"utm_source": "google", "utm_campaign": "mau-ho-so", "ref": "ketoan01"}
    assert "đồng ý" in row["consent_text"] and "0987135358" in row["consent_text"]
    # Không lưu số định danh hay địa chỉ của người trong hồ sơ
    stored = str(row)
    for m in payload["data"]["thanh_vien"]:
        assert m["so_cccd"] not in stored
    assert len(temp_db) == 1 and temp_db[0]["phone"] == "0901234567"


def test_zip_starts_with_guide_and_prices(client):
    r, payload = generate(client)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = z.namelist()
    assert names[0] == leads.COVER_NAME and len(names) > 1
    text = docx_text(z.read(names[0]))
    assert payload["data"]["ten_cong_ty_vn"] in text and "2 thành viên" in text
    assert "Gói Khởi nghiệp – 3.200.000đ" in text and "Gói Cơ bản – 1.200.000đ" in text
    assert "Zalo: 0987135358" in text and "tài khoản định danh điện tử" in text


def test_without_lead_when_not_required_zip_unchanged(client, monkeypatch):
    monkeypatch.setattr(config, "LEAD_REQUIRED", False)
    r, _ = generate(client, lead=None)
    assert r.status_code == 200
    assert leads.COVER_NAME not in zipfile.ZipFile(io.BytesIO(r.content)).namelist()
    assert leads.list_leads() == []


@pytest.mark.parametrize("tid, group, pkg", [
    ("thanh-lap-moi-cong-ty-co-phan", "thanh_lap", "khoi_nghiep"),
    ("thanh-lap-ho-kinh-doanh", "ho_kd", "ho_kd"),
    ("tang-von-cong-ty-tnhh-1-tv", "thay_doi", "thay_doi"),
    ("giai-the-cong-ty-tnhh-1-tv", "giai_the", "khac"),
    ("tam-dung-cong-ty-co-phan", "tam_dung", "khac"),
])
def test_classify_and_score(tid, group, pkg):
    assert leads.classify(tid) == group and leads.GROUPS[group][0] == pkg
    assert leads.score(group, "chu_dn", True) > leads.score(group, "chu_dn", False)


def test_email_text_and_no_smtp(monkeypatch):
    rec = leads.build(leads.parse_lead(dict(LEAD, delegated=True)), "thanh-lap-moi-cong-ty-tnhh-1-tv",
                      "Thành lập mới công ty TNHH 1 TV", {"ten_cong_ty_vn": "CÔNG TY TNHH THỬ"})
    subject, body = leads.email_text(rec, kinh_doanh.get())
    assert "Nguyễn Văn Thử" in subject and "95/100" in subject
    assert "https://zalo.me/0901234567" in body and "Nhờ nộp trọn gói" in body and "Gói Khởi nghiệp" in body
    monkeypatch.setattr(config, "SMTP_HOST", "")
    import importlib
    real = importlib.reload(leads)  # notify thật (fixture đã thay bằng hàm giả)
    assert real.notify(rec) is False


def test_notify_sends_email(monkeypatch):
    import importlib
    real = importlib.reload(leads)
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            sent["host"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def login(self, u, p):
            sent["login"] = u

        def send_message(self, msg):
            sent["to"], sent["subject"] = msg["To"], msg["Subject"]

    monkeypatch.setattr(config, "SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setattr(config, "SMTP_PORT", 465)
    monkeypatch.setattr(config, "SMTP_USER", "guibao@example.com")
    monkeypatch.setattr(config, "SMTP_PASSWORD", "x")
    monkeypatch.setattr(config, "SMTP_FROM", "guibao@example.com")
    monkeypatch.setattr(real.smtplib, "SMTP_SSL", FakeSMTP)
    rec = real.build(real.parse_lead(LEAD), "tang-von-cong-ty-tnhh-1-tv", "Tăng vốn công ty TNHH 1 TV", {})
    assert real.notify(rec) is True
    assert sent["to"] == "dohieu52th@gmail.com" and sent["login"] == "guibao@example.com"


# ---------- Trang quản trị ----------

@pytest.fixture
def admin(client):
    client.cookies.clear()
    auth.create_user("quantri", "mat-khau-thu-nghiem-123")
    r = client.post("/api/admin/login", json={"username": "quantri", "password": "mat-khau-thu-nghiem-123"},
                    headers=CSRF)
    assert r.status_code == 200
    yield client
    client.cookies.clear()


def test_admin_lists_updates_and_deletes_leads(admin):
    generate(admin)
    assert admin.get("/api/admin/leads").status_code == 200
    lead_id = admin.get("/api/admin/leads").json()["leads"][0]["id"]
    r = admin.patch(f"/api/admin/leads/{lead_id}", json={"status": "da_mua", "revenue": "3.200.000", "note": "Gói KN"},
                    headers=CSRF)
    assert r.status_code == 200 and r.json()["lead"]["revenue"] == 3200000
    assert admin.patch(f"/api/admin/leads/{lead_id}", json={"status": "xyz"}, headers=CSRF).status_code == 400
    assert admin.delete(f"/api/admin/leads/{lead_id}", headers=CSRF).status_code == 200
    assert admin.get("/api/admin/leads").json()["leads"] == []


def test_leads_need_login(client):
    client.cookies.clear()
    assert client.get("/api/admin/leads").status_code == 401


def test_business_settings(admin):
    cfg = admin.get("/api/admin/settings/kinh-doanh").json()["value"]
    cfg["goi"][0]["gia"] = "3.500.000đ"
    cfg["ten_don_vi"] = "Văn phòng Thử"
    r = admin.put("/api/admin/settings/kinh-doanh", json=cfg, headers=CSRF)
    assert r.status_code == 200
    pub = admin.get("/api/public/kinh-doanh").json()
    assert pub["goi"][0]["gia"] == "3.500.000đ" and "Văn phòng Thử" in pub["loi_dong_y"]
    assert "email_nhan_bao" not in pub
    bad = dict(cfg, zalo="123")
    assert admin.put("/api/admin/settings/kinh-doanh", json=bad, headers=CSRF).status_code == 400
