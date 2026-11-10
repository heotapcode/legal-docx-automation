"""Sao lưu dữ liệu chỉ có trên máy chủ: bộ mẫu đang dùng, các phiên bản đã xuất bản, CSDL quản trị, yêu cầu tư vấn.

Trang quản trị ghi thẳng vào templates/ nên nội dung trên máy chủ có thể mới hơn git; chạy lệnh này định kỳ
(vd mỗi đêm bằng Task Scheduler / cron), từ thư mục webapp_v2:
    python -m tools.backup                 # tạo data/backups/backup-YYYYmmdd-HHMMSS.zip, giữ 14 bản mới nhất
    python -m tools.backup --keep 30 --dir "D:/SaoLuu"
Khôi phục: giải nén file zip, chép templates/ và data/ về đúng chỗ khi máy chủ đang tắt.
"""
import argparse
import sqlite3
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import config  # noqa: E402

PREFIX = "backup-"


def _add_dir(zf: zipfile.ZipFile, src: Path, arc_root: str) -> int:
    n = 0
    if not src.is_dir():
        return n
    for f in sorted(src.rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts and not f.name.startswith("~$"):
            zf.write(str(f), arcname=f"{arc_root}/{f.relative_to(src).as_posix()}")
            n += 1
    return n


def create_backup(dest_dir: Path, keep: int = 14) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / f"{PREFIX}{datetime.now():%Y%m%d-%H%M%S}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        _add_dir(zf, Path(config.TEMPLATES_DIR), "templates")
        _add_dir(zf, Path(config.TEMPLATE_VERSIONS_DIR), "data/template_versions")
        db = Path(config.ADMIN_DB_PATH)
        if db.exists():
            # Bản chụp nhất quán của SQLite kể cả khi máy chủ đang chạy
            with tempfile.TemporaryDirectory() as tmp:
                snap = Path(tmp) / db.name
                src, dst = sqlite3.connect(str(db)), sqlite3.connect(str(snap))
                try:
                    src.backup(dst)
                finally:
                    src.close()
                    dst.close()
                zf.write(str(snap), arcname=f"data/{db.name}")
        inquiries = Path(config.DATA_DIR) / "inquiries.json"
        if inquiries.exists():
            zf.write(str(inquiries), arcname="data/inquiries.json")
    if keep > 0:
        for old in sorted(dest_dir.glob(f"{PREFIX}*.zip"))[:-keep]:
            old.unlink()
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Sao lưu bộ mẫu, phiên bản mẫu và CSDL quản trị")
    ap.add_argument("--dir", default=str(Path(config.DATA_DIR) / "backups"), help="Thư mục chứa file sao lưu")
    ap.add_argument("--keep", type=int, default=14, help="Số bản mới nhất giữ lại (0 = giữ tất cả)")
    args = ap.parse_args(argv)
    out = create_backup(Path(args.dir), args.keep)
    print(f"Đã sao lưu: {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
