"""Cấu hình chung cho bộ test của webapp_v2.

Chạy từ thư mục webapp_v2:
    pip install -r requirements.txt -r requirements-dev.txt
    pytest
"""
import io
import json
import sys
import zipfile
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import config  # noqa: E402
from config import TEMPLATES_DIR  # noqa: E402

# Bộ test gọi API dồn dập từ một IP: tắt giới hạn tần suất (test riêng bật lại, xem test_api_security.py)
config.RATE_LIMITS = {k: 0 for k in config.RATE_LIMITS}
# Test sinh hồ sơ không qua bước để lại số Zalo (test riêng bật lại, xem test_leads.py)
config.LEAD_REQUIRED = False
from services.sample_data import build_sample_payload, docx_text, sample_person  # noqa: E402,F401


def list_template_names():
    return sorted(d.name for d in TEMPLATES_DIR.iterdir() if d.is_dir() and (d / "_schema.json").exists())


def load_schema(name: str) -> dict:
    return json.loads((TEMPLATES_DIR / name / "_schema.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as c:
        yield c


# ---------- Dữ liệu mẫu (dùng chung với tools/template_lint.py) ----------

def build_payload(name: str, n_members: int = 3):
    """Trả về (payload, markers, members) cho bộ mẫu `name`. Xem services/sample_data.py."""
    return build_sample_payload(load_schema(name), n_members)


# ---------- Đọc kết quả ZIP ----------

def read_zip(content: bytes) -> dict:
    """{tên file: nội dung text} cho mọi file trong ZIP."""
    z = zipfile.ZipFile(io.BytesIO(content))
    out = {}
    for n in z.namelist():
        raw = z.read(n)
        out[n] = docx_text(raw) if n.endswith(".docx") else raw.decode("utf-8", errors="replace")
    return out
