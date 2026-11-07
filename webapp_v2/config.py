import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
TEMPLATES_DIR = BASE_DIR / "templates"
DATA_DIR = BASE_DIR / "data"

# Tự động nạp file .env từ BASE_DIR hoặc ROOT_DIR
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv(dotenv_path=ROOT_DIR / ".env")

MA_NGANH_JSON = ROOT_DIR / "ma_nganh_nghe.json"
COMBO_NGANH_JSON = DATA_DIR / "combo_nganh.json"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8002"))


def _parse_origins(raw: str) -> list:
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


# CORS: danh sách origin được phép gọi API từ trình duyệt, phân tách bằng dấu phẩy.
# Mặc định chỉ cho phép chính ứng dụng (localhost). Frontend được phục vụ cùng
# origin với API nên KHÔNG cần CORS; chỉ thêm origin khi có frontend chạy ở domain khác.
# Đặt CORS_ORIGINS=* để mở cho mọi origin (khi đó cookie/credential bị tắt).
CORS_ORIGINS = _parse_origins(
    os.environ.get("CORS_ORIGINS", f"http://localhost:{PORT},http://127.0.0.1:{PORT}")
)

# ---------- Quản trị (Mục 10) ----------
# CSDL SQLite lưu tài khoản quản trị, phiên đăng nhập, nhật ký và phiên bản mẫu. Không commit file này.
ADMIN_DB_PATH = Path(os.environ.get("ADMIN_DB_PATH", str(DATA_DIR / "admin.sqlite3")))
# Thời hạn một phiên đăng nhập quản trị (giờ)
ADMIN_SESSION_HOURS = int(os.environ.get("ADMIN_SESSION_HOURS", "12"))
# Đặt ADMIN_COOKIE_SECURE=1 khi chạy qua HTTPS để cookie phiên chỉ được gửi qua HTTPS
ADMIN_COOKIE_SECURE = os.environ.get("ADMIN_COOKIE_SECURE", "0").lower() in ("1", "true", "yes")
# Bản nháp và các phiên bản đã xuất bản của bộ mẫu (Mục 10.2, 10.4). Không commit.
TEMPLATE_DRAFTS_DIR = Path(os.environ.get("TEMPLATE_DRAFTS_DIR", str(DATA_DIR / "template_drafts")))
TEMPLATE_VERSIONS_DIR = Path(os.environ.get("TEMPLATE_VERSIONS_DIR", str(DATA_DIR / "template_versions")))
