"""Công cụ sao lưu (tools/backup.py): gom bộ mẫu, phiên bản mẫu, CSDL quản trị; chỉ giữ N bản mới nhất."""
import zipfile

import config
from services import auth
from tools import backup


def test_backup_contents_and_rotation(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ADMIN_DB_PATH", tmp_path / "admin.sqlite3")
    monkeypatch.setattr(config, "TEMPLATE_VERSIONS_DIR", tmp_path / "versions")
    (tmp_path / "versions" / "x" / "v1").mkdir(parents=True)
    (tmp_path / "versions" / "x" / "v1" / "a.txt").write_text("v1", encoding="utf-8")
    auth.create_user("quantri", "mat-khau-thu-nghiem-123")

    dest = tmp_path / "backups"
    out = backup.create_backup(dest, keep=2)
    names = zipfile.ZipFile(out).namelist()
    assert "data/admin.sqlite3" in names and "data/template_versions/x/v1/a.txt" in names
    assert any(n.startswith("templates/") and n.endswith("_schema.json") for n in names)
    assert not any("__pycache__" in n for n in names)

    for stamp in ("20200101-000000", "20200102-000000", "20200103-000000"):
        (dest / f"backup-{stamp}.zip").write_bytes(b"x")
    backup.create_backup(dest, keep=2)
    left = sorted(p.name for p in dest.glob("backup-*.zip"))
    assert len(left) == 2 and "backup-20200101-000000.zip" not in left
