"""Sinh dữ liệu mẫu cố định từ _schema.json.

Dùng chung cho bộ test (tests/) và công cụ quét mẫu (tools/template_lint.py).
Mọi giá trị đều cố định (không ngẫu nhiên) để hồ sơ sinh ra luôn giống nhau giữa các lần chạy.
"""
import io
from typing import Any, Dict, List, Tuple

import docx


def sample_person(i: int, prefix: str = "") -> Dict[str, str]:
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


SAMPLE_VON_CU = "1005000000"    # Một tỷ không trăm linh năm triệu đồng
SAMPLE_VON_MOI = "2105030000"   # Hai tỷ một trăm linh năm triệu không trăm ba mươi nghìn đồng

SAMPLE_NGANH = [
    {"ma": "6201", "ten": "Lập trình máy vi tính", "is_main": True},
    {"ma": "4659", "ten": "Bán buôn máy móc, thiết bị và phụ tùng máy khác", "is_main": False},
]


def build_sample_payload(schema: Dict[str, Any], n_members: int = 3) -> Tuple[dict, Dict[str, str], List[dict]]:
    """Trả về (payload cho /api/documents/generate, markers, members).

    markers: {field_key: giá trị} — các giá trị phải xuất hiện nguyên văn trong bộ hồ sơ sinh ra.
    """
    name = schema["name"]
    data: Dict[str, Any] = {}
    markers: Dict[str, str] = {}
    members: List[dict] = []
    for step in schema.get("steps", []):
        for f in step["fields"]:
            key, typ = f["key"], f["type"]
            if typ in ("text", "mst_lookup"):
                value = "0101234567" if typ == "mst_lookup" else f"GIATRI_{key.upper()}"
                if "ten_cong_ty" in key:
                    value = "CÔNG TY TNHH THỬ NGHIỆM ABC"
                if key == "ngay_lap":
                    # Ngày lập được in dạng "ngày 20 tháng 10 năm 2026"
                    data[key] = "20/10/2026"
                    markers[key] = "ngày 20 tháng 10 năm 2026"
                    continue
                data[key] = value
                # Giới tính được chuyển thành "Ông/Bà" trong văn bản nên không so khớp nguyên văn
                if not key.endswith("gioi_tinh"):
                    markers[key] = value
            elif typ == "money":
                # Số có nhóm 0 ở giữa để đi qua nhánh "không trăm", "linh" khi đọc số thành chữ
                data[key] = SAMPLE_VON_CU if "cu" in key else SAMPLE_VON_MOI
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
                    p.update(stt=i, von_gop=str(int(SAMPLE_VON_MOI) // n_members), ty_le=str(round(100 / n_members, 2)))
                    members.append(p)
            elif typ == "checkbox_group":
                data[key] = [o["value"] for o in f["options"]]
    data["thanh_vien"] = members

    special: Dict[str, Any] = {}
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

    ma_nganh = [dict(n) for n in SAMPLE_NGANH] if schema.get("has_nganh") else []
    payload = {"template_name": name, "data": data, "ma_nganh": ma_nganh, "special_payload": special}
    return payload, markers, members


def docx_text(blob: bytes) -> str:
    """Toàn bộ chữ trong một file .docx: đoạn văn, bảng, header, footer."""
    d = docx.Document(io.BytesIO(blob))
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            parts.extend(cell.text for cell in row.cells)
    for s in d.sections:
        parts.extend(p.text for p in s.header.paragraphs)
        parts.extend(p.text for p in s.footer.paragraphs)
    return "\n".join(parts)
