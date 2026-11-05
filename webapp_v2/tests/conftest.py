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

import docx
import pytest

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import TEMPLATES_DIR  # noqa: E402


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


# ---------- Sinh dữ liệu mẫu từ _schema.json ----------

def sample_person(i: int, prefix: str = "") -> dict:
    return {
        f"{prefix}ho_ten": f"NGUYỄN VĂN THỬ{i}",
        f"{prefix}gioi_tinh": "Nam" if i % 2 else "Nữ",
        f"{prefix}ngay_sinh": f"{i % 28 + 1:02d}/01/1990",
        f"{prefix}so_cccd": f"00109000{i:04d}",
        f"{prefix}ngay_cap": "01/01/2021",
        f"{prefix}noi_cap": "Cục Cảnh sát QLHC về TTXH",
        f"{prefix}dia_chi_so_nha": f"Số {i} Ngõ Thử Nghiệm",
        f"{prefix}dia_chi_xa_phuong": "Phường Cầu Giấy",
        f"{prefix}dia_chi_tinh_thanh": "Thành phố Hà Nội",
        f"{prefix}chuc_danh": "Giám đốc",
        f"{prefix}dan_toc": "Kinh",
        f"{prefix}quoc_tich": "Việt Nam",
    }


def build_payload(name: str, n_members: int = 3):
    """Trả về (payload, markers, members).

    markers: {field_key: giá trị} — các giá trị phải xuất hiện trong bộ hồ sơ sinh ra.
    """
    schema = load_schema(name)
    data, markers, members = {}, {}, []
    for step in schema.get("steps", []):
        for f in step["fields"]:
            key, typ = f["key"], f["type"]
            if typ in ("text", "mst_lookup"):
                value = "0101234567" if typ == "mst_lookup" else f"GIATRI_{key.upper()}"
                if "ten_cong_ty" in key:
                    value = "CÔNG TY TNHH THỬ NGHIỆM ABC"
                data[key] = value
                # Giới tính được chuyển thành "Ông/Bà" trong văn bản nên không so khớp nguyên văn
                if not key.endswith("gioi_tinh"):
                    markers[key] = value
            elif typ == "money":
                data[key] = "1000000000" if "cu" in key else "2000000000"
            elif typ == "phone":
                data[key] = "0912345678"
            elif typ == "email":
                data[key] = "test@example.com"
            elif typ == "person":
                data.update(sample_person(90, key + "_"))
                markers[key] = "NGUYỄN VĂN THỬ90"
            elif typ == "person_list":
                for i in range(1, n_members + 1):
                    p = sample_person(i)
                    p.update(stt=i, von_gop=str(2_000_000_000 // n_members), ty_le=str(round(100 / n_members, 2)))
                    members.append(p)
            elif typ == "checkbox_group":
                data[key] = [o["value"] for o in f["options"]]
    data["thanh_vien"] = members

    special = {}
    if "Chuyển nhượng" in name:
        a, b = sample_person(1), sample_person(77)
        transfers = [{
            "ben_a": {"ho_ten": a["ho_ten"], "so_cccd": a["so_cccd"], "dia_chi_day_du": "Hà Nội"},
            "ben_b": {k: b[k] for k in ("ho_ten", "so_cccd", "dia_chi_so_nha", "dia_chi_xa_phuong", "dia_chi_tinh_thanh")},
            "gia_tri_so": "500000000",
            "ty_le": "25",
        }]
        data["chuyen_nhuong"] = transfers
        special["chuyen_nhuong"] = transfers

    ma_nganh = []
    if schema.get("has_nganh"):
        ma_nganh = [
            {"ma": "6201", "ten": "Lập trình máy vi tính", "is_main": True},
            {"ma": "4659", "ten": "Bán buôn máy móc, thiết bị và phụ tùng máy khác", "is_main": False},
        ]
    payload = {"template_name": name, "data": data, "ma_nganh": ma_nganh, "special_payload": special}
    return payload, markers, members


# ---------- Đọc kết quả ZIP ----------

def docx_text(blob: bytes) -> str:
    d = docx.Document(io.BytesIO(blob))
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            parts.extend(cell.text for cell in row.cells)
    for s in d.sections:
        parts.extend(p.text for p in s.header.paragraphs)
        parts.extend(p.text for p in s.footer.paragraphs)
    return "\n".join(parts)


def read_zip(content: bytes) -> dict:
    """{tên file: nội dung text} cho mọi file trong ZIP."""
    z = zipfile.ZipFile(io.BytesIO(content))
    out = {}
    for n in z.namelist():
        raw = z.read(n)
        out[n] = docx_text(raw) if n.endswith(".docx") else raw.decode("utf-8", errors="replace")
    return out
