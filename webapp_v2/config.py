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

HOST = "0.0.0.0"
PORT = 8002
