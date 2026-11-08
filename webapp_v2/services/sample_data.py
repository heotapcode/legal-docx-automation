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


LIST_PERSON_BASE = 60  # người trong các `list` là NGUYỄN VĂN THỬ61, THỬ62...


def sample_value(sub: Dict[str, Any], person: Dict[str, str], i: int) -> Any:
    """Giá trị mẫu cho một ô trong phần tử thứ i của `list`."""
    key, typ = sub["key"], sub["type"]
    if key == "dia_chi_day_du":
        return ", ".join(person[k] for k in ("dia_chi_so_nha", "dia_chi_xa_phuong", "dia_chi_tinh_thanh"))
    if key in person:
        return person[key]
    if typ == "select":
        if sub.get("options_from"):
            return ("__ref__", i)  # thay bằng chỉ số thật ở resolve_sample_refs (list nguồn có thể chưa có)
        return sub.get("default") or (sub["options"][0]["value"] if sub.get("options") else "")
    return {"date": "01/01/1990", "cccd": f"00109100{i:04d}", "percent": "25", "money": "500000000",
            "number": "1"}.get(typ, f"GIATRI_{key.upper()}_{i + 1}")


def sample_list(field: Dict[str, Any], data: Dict[str, Any], n_members: int) -> List[dict]:
    n = max(field.get("min", 0), 1)
    items = []
    for i in range(n):
        person = sample_person(LIST_PERSON_BASE + 1 + i)
        items.append({sub["key"]: sample_value(sub, person, i) for sub in field.get("item", [])})
    return items


def resolve_sample_refs(schema: Dict[str, Any], data: Dict[str, Any]) -> None:
    """Ô options_from trong list mẫu: chọn phần tử thứ i (vòng lại) của list nguồn."""
    for step in schema.get("steps", []):
        for f in step["fields"]:
            if f["type"] != "list":
                continue
            for item in data.get(f["key"], []):
                for sub in f.get("item", []):
                    v = item.get(sub["key"])
                    if isinstance(v, tuple) and v[0] == "__ref__":
                        source = data.get(sub["options_from"]) or [None]
                        item[sub["key"]] = str(v[1] % len(source))


def build_sample_payload(schema: Dict[str, Any], n_members: int = 3) -> Tuple[dict, Dict[str, str], List[dict]]:
    """Trả về (payload cho /api/documents/generate, markers, members).

    markers: {field_key: giá trị} — các giá trị phải xuất hiện nguyên văn trong bộ hồ sơ sinh ra.
    """
    name = schema["name"]
    data: Dict[str, Any] = {}
    markers: Dict[str, str] = {}
    members: List[dict] = []
    n_person = 0
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
            elif typ == "percent":
                data[key] = "40"
            elif typ == "number":
                data[key] = "1"
            elif typ == "date":
                data[key] = "01/01/1990"
            elif typ == "cccd":
                data[key] = "001090009999"
            elif typ == "address":
                data[key] = "Số 9 Ngõ Thử Nghiệm, Phường Cầu Giấy, Thành phố Hà Nội"
            elif typ == "phone":
                data[key] = "0912345678"
            elif typ == "email":
                data[key] = "test@example.com"
            elif typ == "person":
                # Mỗi người một tên riêng (THỬ90, THỬ91...); người "cũ" (vd ĐDPL cũ) là THỬ89,
                # khác người mới để hồ sơ có thay đổi người đại diện
                idx = 89 if key.endswith("_cu") else 90 + n_person
                n_person += idx != 89
                data.update(sample_person(idx, key + "_"))
                markers[key] = f"NGUYỄN VĂN THỬ{idx}"
            elif typ == "list":
                data[key] = sample_list(f, data, n_members)
            elif typ == "person_list":
                n_members = max(n_members, f.get("min", 1))  # không ít hơn số tối thiểu của schema
                for i in range(1, n_members + 1):
                    p = sample_person(i)
                    p.update(stt=i, von_gop=str(int(SAMPLE_VON_MOI) // n_members), ty_le=str(round(100 / n_members, 2)))
                    members.append(p)
            elif typ == "select":
                # Giữ giá trị mặc định (vd tỉnh/thành phố = Hà Nội) để hồ sơ mẫu ổn định
                if f.get("default"):
                    data[key] = f["default"]
                elif f.get("options"):
                    data[key] = f["options"][0]["value"]
            elif typ == "checkbox_group":
                data[key] = [o["value"] for o in f["options"]]
    data["thanh_vien"] = members
    resolve_sample_refs(schema, data)
    # Ô bị ẩn theo show_if (vd mệnh giá cổ phần khi không phải công ty cổ phần) không bắt buộc xuất hiện trong hồ sơ
    from services.schema_engine import visible_fields
    shown_fields = list(visible_fields(schema, data))
    shown = {f["key"] for f in shown_fields}
    markers = {k: v for k, v in markers.items() if k in shown}
    if members and not any(f["type"] == "person_list" for f in shown_fields):
        members = []  # bước danh sách thành viên đang ẩn
        data["thanh_vien"] = []

    special: Dict[str, Any] = {}
    has_transfer_field = any(f["key"] == "chuyen_nhuong" for st in schema.get("steps", []) for f in st["fields"])
    if "Chuyển nhượng" in name and not has_transfer_field:
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
