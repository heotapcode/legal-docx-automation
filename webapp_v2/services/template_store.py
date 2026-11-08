"""Quản lý bộ mẫu từ trang quản trị (Mục 10.2, 10.4, 10.5): bản nháp, quét, sinh thử, xuất bản, phiên bản.

Luồng làm việc:
    tạo bản nháp (sao chép bộ mẫu đang dùng)  ->  thay/thêm/xóa file .docx, sửa _schema.json
    ->  quét mẫu (tools/template_lint)  ->  sinh thử với dữ liệu mẫu  ->  xuất bản

Thư mục:
    config.TEMPLATES_DIR/<tên>/           bộ mẫu đang dùng (wizard và API đọc ở đây)
    config.TEMPLATE_DRAFTS_DIR/<draft>/   bản nháp
    config.TEMPLATE_VERSIONS_DIR/<id>/v<n>/  nội dung đầy đủ của từng phiên bản đã xuất bản
Thông tin phiên bản (ai, khi nào, ghi chú, căn cứ pháp lý) lưu trong SQLite (services/admin_db.py).

Phiên bản 1 là nội dung bộ mẫu trước lần xuất bản đầu tiên (bản trong git), được lưu tự động.
Xuất bản bị chặn khi: quét mẫu còn lỗi, schema đổi id/tên, hoặc bộ mẫu đã được xuất bản lại sau khi
tạo bản nháp (tránh hai người ghi đè nhau).
"""
import io
import json
import re
import secrets
import shutil
import threading
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import docx

import config
from services import admin_db

MAX_DOCX_BYTES = 5 * 1024 * 1024          # file tải lên
MAX_DOCX_UNZIPPED = 60 * 1024 * 1024      # tổng dung lượng sau giải nén (chống "zip bomb")
DRAFT_ID_RE = re.compile(r"^[0-9a-f]{16}$")

_publish_lock = threading.Lock()


class StoreError(Exception):
    """Lỗi do người dùng (dữ liệu không hợp lệ): trả 400."""


class NotFound(StoreError):
    """Không có bộ mẫu / bản nháp / phiên bản: trả 404."""


class Conflict(StoreError):
    """Bộ mẫu đã đổi sau khi tạo bản nháp: trả 409."""


class PublishBlocked(StoreError):
    """Quét mẫu còn lỗi: trả 422 kèm danh sách lỗi."""

    def __init__(self, message: str, findings: List[dict]):
        super().__init__(message)
        self.findings = findings


# ---------- Bộ mẫu đang dùng ----------

def _read_schema(tpl_dir: Path) -> dict:
    return json.loads((tpl_dir / "_schema.json").read_text(encoding="utf-8"))


def _live_index() -> Dict[str, Path]:
    out = {}
    root = Path(config.TEMPLATES_DIR)
    for schema_path in sorted(root.glob("*/_schema.json")):
        try:
            tid = json.loads(schema_path.read_text(encoding="utf-8")).get("id")
        except (OSError, ValueError):
            continue
        if isinstance(tid, str) and tid:
            out[tid] = schema_path.parent
    return out


def live_dir(template_id: str) -> Path:
    d = _live_index().get(template_id)
    if d is None:
        raise NotFound(f"Không có bộ mẫu: {template_id}")
    return d


def _docx_files(d: Path) -> List[str]:
    return sorted(f.name for f in d.glob("*.docx") if not f.name.startswith(("~$", "_")))


def current_version(conn, template_id: str) -> int:
    """Số phiên bản đang dùng; 1 nếu chưa từng xuất bản từ trang quản trị (bản trong git)."""
    v = conn.execute("SELECT MAX(version) FROM template_versions WHERE template_id = ?", (template_id,)).fetchone()[0]
    return v or 1


def list_templates() -> List[dict]:
    with admin_db.connect() as conn:
        out = []
        for tid, d in _live_index().items():
            s = _read_schema(d)
            out.append({"id": tid, "name": d.name, "display_name": s.get("display_name", d.name),
                        "category": s.get("category", ""), "version": current_version(conn, tid),
                        "files": _docx_files(d)})
    return sorted(out, key=lambda t: (t["category"], t["display_name"]))


# ---------- Bản nháp ----------

def _drafts_root() -> Path:
    return Path(config.TEMPLATE_DRAFTS_DIR)


def _draft_row(conn, draft_id: str):
    if not DRAFT_ID_RE.match(draft_id or ""):
        raise NotFound("Không có bản nháp")
    row = conn.execute("SELECT * FROM template_drafts WHERE id = ?", (draft_id,)).fetchone()
    if not row or not (_drafts_root() / draft_id).is_dir():
        raise NotFound("Không có bản nháp")
    return row


def draft_dir(draft_id: str) -> Path:
    with admin_db.connect() as conn:
        _draft_row(conn, draft_id)
    return _drafts_root() / draft_id


def create_draft(template_id: str, user: dict) -> dict:
    src = live_dir(template_id)
    draft_id = secrets.token_hex(8)
    dst = _drafts_root() / draft_id
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("~$*"))
    with admin_db.connect() as conn:
        base = current_version(conn, template_id)
        conn.execute("INSERT INTO template_drafts(id, template_id, base_version, created_by, created_at) "
                     "VALUES (?, ?, ?, ?, ?)", (draft_id, template_id, base, user["id"], admin_db.now_iso()))
        admin_db.audit(conn, user["id"], "draft.create", f"{template_id} -> {draft_id}")
    return get_draft(draft_id)


def get_draft(draft_id: str) -> dict:
    with admin_db.connect() as conn:
        row = _draft_row(conn, draft_id)
    d = _drafts_root() / draft_id
    return {"id": draft_id, "template_id": row["template_id"], "base_version": row["base_version"],
            "created_at": row["created_at"], "files": _docx_files(d), "schema": _read_schema(d)}


def list_drafts(template_id: Optional[str] = None) -> List[dict]:
    with admin_db.connect() as conn:
        rows = conn.execute(
            "SELECT d.id, d.template_id, d.base_version, d.created_at, u.username FROM template_drafts d "
            "LEFT JOIN users u ON u.id = d.created_by WHERE (? IS NULL OR d.template_id = ?) ORDER BY d.created_at",
            (template_id, template_id)).fetchall()
    return [dict(r) for r in rows if (_drafts_root() / r["id"]).is_dir()]


def discard_draft(draft_id: str, user: dict) -> None:
    with admin_db.connect() as conn:
        row = _draft_row(conn, draft_id)
        conn.execute("DELETE FROM template_drafts WHERE id = ?", (draft_id,))
        admin_db.audit(conn, user["id"], "draft.discard", f"{row['template_id']} / {draft_id}")
    shutil.rmtree(_drafts_root() / draft_id, ignore_errors=True)


def _check_docx_name(filename: str) -> str:
    name = (filename or "").strip()
    if (not name or Path(name).name != name or "\\" in name or name in (".", "..")
            or not name.lower().endswith(".docx") or name.startswith(("~$", "_"))
            or len(name) > 150 or any(ord(c) < 32 for c in name)):
        raise StoreError("Tên file không hợp lệ: chỉ nhận file .docx, không chứa đường dẫn, không bắt đầu bằng '~$' hoặc '_'")
    return name


def check_docx_bytes(data: bytes) -> None:
    """File .docx hợp lệ: đúng cấu trúc Word, không chứa macro, không quá lớn khi giải nén."""
    if len(data) > MAX_DOCX_BYTES:
        raise StoreError(f"File quá lớn (tối đa {MAX_DOCX_BYTES // (1024 * 1024)} MB)")
    if not zipfile.is_zipfile(io.BytesIO(data)):
        raise StoreError("Không phải file Word (.docx)")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = set(z.namelist())
        if "[Content_Types].xml" not in names or "word/document.xml" not in names:
            raise StoreError("Không phải file Word (.docx)")
        if any(n.lower().endswith("vbaproject.bin") for n in names):
            raise StoreError("File chứa macro, không được phép")
        if sum(i.file_size for i in z.infolist()) > MAX_DOCX_UNZIPPED:
            raise StoreError("File giải nén quá lớn")
    try:
        docx.Document(io.BytesIO(data))
    except Exception as e:  # noqa: BLE001 - python-docx ném nhiều loại lỗi khác nhau
        raise StoreError(f"Word không mở được file: {e}")


def put_docx(draft_id: str, filename: str, data: bytes, user: dict) -> dict:
    d = draft_dir(draft_id)
    name = _check_docx_name(filename)
    check_docx_bytes(data)
    (d / name).write_bytes(data)
    with admin_db.connect() as conn:
        admin_db.audit(conn, user["id"], "draft.put_file", f"{draft_id}: {name} ({len(data)} byte)")
    return get_draft(draft_id)


def delete_docx(draft_id: str, filename: str, user: dict) -> dict:
    d = draft_dir(draft_id)
    name = _check_docx_name(filename)
    if not (d / name).is_file():
        raise NotFound(f"Bản nháp không có file {name}")
    (d / name).unlink()
    with admin_db.connect() as conn:
        admin_db.audit(conn, user["id"], "draft.delete_file", f"{draft_id}: {name}")
    return get_draft(draft_id)


def put_schema(draft_id: str, schema: Any, user: dict) -> dict:
    d = draft_dir(draft_id)
    if not isinstance(schema, dict):
        raise StoreError("Schema phải là một đối tượng JSON")
    old = _read_schema(d)
    for key in ("id", "name"):
        if schema.get(key) != old.get(key):
            raise StoreError(f"Không được đổi '{key}' của bộ mẫu (đang là {old.get(key)!r})")
    (d / "_schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with admin_db.connect() as conn:
        admin_db.audit(conn, user["id"], "draft.put_schema", draft_id)
    return get_draft(draft_id)


# ---------- Quét và sinh thử ----------

def lint_dir(d: Path) -> dict:
    from tools.template_lint import lint_template, summarize

    findings = lint_template(d)
    return {"summary": summarize(findings),
            "findings": [{"level": f.level, "code": f.code, "file": f.file, "message": f.message} for f in findings]}


def lint_draft(draft_id: str) -> dict:
    return lint_dir(draft_dir(draft_id))


def preview_draft(draft_id: str) -> bytes:
    """ZIP hồ sơ sinh từ bản nháp với dữ liệu mẫu cố định (services/sample_data.py)."""
    from services.render_service import render_documents
    from services.sample_data import build_sample_payload

    d = draft_dir(draft_id)
    payload, _, _ = build_sample_payload(_read_schema(d), 3)
    return render_documents(payload["template_name"], payload["data"], payload["ma_nganh"],
                            payload["special_payload"], template_dir=d)


def suggest_fields(draft_id: str) -> List[dict]:
    """Gợi ý trường cho các biến trong mẫu Word chưa có nguồn dữ liệu (tools/schema_suggest.py, Mục 10.3)."""
    from tools.schema_suggest import suggest

    return suggest(draft_dir(draft_id))


def apply_suggestions(draft_id: str, keys: List[str], user: dict) -> dict:
    """Thêm các gợi ý được chọn vào bước "Thông tin bổ sung" của _schema.json trong bản nháp."""
    from tools.schema_suggest import apply_to_schema

    wanted = set(keys or [])
    if not wanted:
        raise StoreError("Chưa chọn gợi ý nào")
    chosen = [s for s in suggest_fields(draft_id) if s["key"] in wanted]
    unknown = wanted - {s["key"] for s in chosen}
    if unknown:
        raise StoreError(f"Không có gợi ý: {', '.join(sorted(unknown))}")
    d = draft_dir(draft_id)
    schema = apply_to_schema(_read_schema(d), chosen)
    (d / "_schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with admin_db.connect() as conn:
        admin_db.audit(conn, user["id"], "draft.apply_suggestions", f"{draft_id}: {', '.join(sorted(wanted))}")
    return get_draft(draft_id)


# ---------- Xuất bản và phiên bản ----------

def _versions_root(template_id: str) -> Path:
    return Path(config.TEMPLATE_VERSIONS_DIR) / template_id


def _swap_into_live(live: Path, new_content: Path) -> None:
    """Thay nội dung bộ mẫu đang dùng: chép sang thư mục tạm cạnh nó rồi đổi tên (gần như tức thời)."""
    staging = live.with_name(live.name + ".__new__")
    old = live.with_name(live.name + ".__old__")
    for p in (staging, old):
        if p.exists():
            shutil.rmtree(p)
    shutil.copytree(new_content, staging)
    live.rename(old)
    staging.rename(live)
    shutil.rmtree(old, ignore_errors=True)


def _ensure_initial_version(conn, template_id: str, live: Path, user: dict) -> None:
    """Lần đầu thay bộ mẫu: lưu nội dung hiện tại (bản trong git) làm phiên bản 1 để quay lại được."""
    if conn.execute("SELECT 1 FROM template_versions WHERE template_id = ?", (template_id,)).fetchone():
        return
    dst = _versions_root(template_id) / "v1"
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(live, dst, ignore=shutil.ignore_patterns("~$*"))
    conn.execute("INSERT INTO template_versions(template_id, version, source, note, created_by, created_at) "
                 "VALUES (?, 1, 'initial', 'Bản ban đầu (trước lần xuất bản đầu tiên)', ?, ?)",
                 (template_id, user["id"], admin_db.now_iso()))


def _install_version(conn, template_id: str, content: Path, user: dict, source: str, note: str,
                     legal_basis: str = "", effective_from: str = "") -> int:
    live = live_dir(template_id)
    _ensure_initial_version(conn, template_id, live, user)
    version = current_version(conn, template_id) + 1
    dst = _versions_root(template_id) / f"v{version}"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(content, dst, ignore=shutil.ignore_patterns("~$*"))
    schema = _read_schema(dst)
    schema["version"] = version
    if legal_basis:
        schema["legal_basis"] = legal_basis
    if effective_from:
        schema["effective_from"] = effective_from
    (dst / "_schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _swap_into_live(live, dst)
    conn.execute("INSERT INTO template_versions(template_id, version, source, note, legal_basis, effective_from, "
                 "created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                 (template_id, version, source, note, legal_basis or None, effective_from or None,
                  user["id"], admin_db.now_iso()))
    admin_db.audit(conn, user["id"], f"template.{source}", f"{template_id} v{version}: {note}")
    return version


def publish_draft(draft_id: str, user: dict, note: str, legal_basis: str = "", effective_from: str = "") -> int:
    note = (note or "").strip()
    if not note:
        raise StoreError("Cần ghi chú nội dung thay đổi khi xuất bản")
    if effective_from and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", effective_from):
        raise StoreError("Ngày hiệu lực phải có dạng YYYY-MM-DD")
    with _publish_lock:
        d = draft_dir(draft_id)
        report = lint_dir(d)
        errors = [f for f in report["findings"] if f["level"] == "error"]
        if errors:
            raise PublishBlocked(f"Quét mẫu còn {len(errors)} lỗi, chưa xuất bản được", errors)
        with admin_db.connect() as conn:
            row = _draft_row(conn, draft_id)
            if current_version(conn, row["template_id"]) != row["base_version"]:
                raise Conflict("Bộ mẫu đã được xuất bản lại sau khi tạo bản nháp này. "
                               "Hãy tạo bản nháp mới từ phiên bản hiện tại.")
            version = _install_version(conn, row["template_id"], d, user, "publish", note, legal_basis, effective_from)
            conn.execute("DELETE FROM template_drafts WHERE id = ?", (draft_id,))
    shutil.rmtree(d, ignore_errors=True)
    return version


def list_versions(template_id: str) -> List[dict]:
    live_dir(template_id)
    with admin_db.connect() as conn:
        rows = conn.execute(
            "SELECT v.version, v.source, v.note, v.legal_basis, v.effective_from, v.created_at, u.username "
            "FROM template_versions v LEFT JOIN users u ON u.id = v.created_by "
            "WHERE v.template_id = ? ORDER BY v.version DESC", (template_id,)).fetchall()
        current = current_version(conn, template_id)
    return [dict(r, current=(r["version"] == current)) for r in rows]


def rollback(template_id: str, version: int, user: dict, note: str = "") -> int:
    """Dùng lại nội dung của phiên bản cũ; lưu thành một phiên bản MỚI (lịch sử không bị xóa)."""
    with _publish_lock, admin_db.connect() as conn:
        live_dir(template_id)
        if not conn.execute("SELECT 1 FROM template_versions WHERE template_id = ? AND version = ?",
                            (template_id, int(version))).fetchone():
            raise NotFound(f"Không có phiên bản {version}")
        src = _versions_root(template_id) / f"v{int(version)}"
        if not src.is_dir():
            raise NotFound(f"Thiếu nội dung lưu trữ của phiên bản {version}")
        return _install_version(conn, template_id, src, user, "rollback",
                                (note or "").strip() or f"Quay lại phiên bản {version}")
