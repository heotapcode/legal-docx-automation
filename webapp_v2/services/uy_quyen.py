"""Người nhận ủy quyền (Bên B) in trong các Giấy ủy quyền.

Giá trị mặc định ở data/nguoi_nhan_uy_quyen.json; trang quản trị lưu giá trị sửa vào bảng `settings` của CSDL quản trị.
Mẫu Word dùng: {{ uq_ho_ten }}, {{ uq_danh_xung }} (Ông/Bà), {{ uq_gioi_tinh }}, {{ uq_ngay_sinh }}, {{ uq_so_cccd }},
{{ uq_dia_chi }}, {{ uq_sdt }}, {{ uq_email }}.
"""
import json
import re
from typing import Dict

from config import DATA_DIR

DEFAULT_JSON = DATA_DIR / "nguoi_nhan_uy_quyen.json"
SETTING_KEY = "nguoi_nhan_uy_quyen"
FIELDS = ("ho_ten", "gioi_tinh", "ngay_sinh", "so_cccd", "dia_chi", "sdt", "email")
REQUIRED = ("ho_ten", "so_cccd")


def defaults() -> Dict[str, str]:
    data = json.loads(DEFAULT_JSON.read_text(encoding="utf-8"))
    return {k: str(data.get(k, "")) for k in FIELDS}


def get() -> Dict[str, str]:
    """Giá trị đang dùng: mặc định, đè bởi giá trị đã lưu trên trang quản trị (nếu có)."""
    out = defaults()
    try:
        from services import admin_db
        saved = admin_db.get_setting(SETTING_KEY)
    except Exception:  # CSDL quản trị chưa sẵn sàng: dùng mặc định
        saved = None
    if saved:
        out.update({k: str(v) for k, v in json.loads(saved).items() if k in FIELDS})
    return out


def validate(data: dict) -> Dict[str, str]:
    """Chuẩn hóa và kiểm tra dữ liệu gửi từ trang quản trị. Sai -> ValueError."""
    out = {k: " ".join(str(data.get(k, "") or "").split()) for k in FIELDS}
    for k in REQUIRED:
        if not out[k]:
            raise ValueError(f"Thiếu {k}")
    if not re.fullmatch(r"\d{12}", out["so_cccd"]):
        raise ValueError("Số định danh cá nhân phải gồm 12 chữ số")
    if out["gioi_tinh"] not in ("Nam", "Nữ"):
        raise ValueError("Giới tính phải là Nam hoặc Nữ")
    if out["ngay_sinh"] and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", out["ngay_sinh"]):
        raise ValueError("Ngày sinh theo dạng DD/MM/YYYY")
    if out["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", out["email"]):
        raise ValueError("Thư điện tử không hợp lệ")
    return out


def save(data: dict, user_id=None) -> Dict[str, str]:
    from services import admin_db
    clean = validate(data)
    admin_db.set_setting(SETTING_KEY, json.dumps(clean, ensure_ascii=False), user_id)
    return clean


def context_values() -> Dict[str, str]:
    """Biến uq_* cho mẫu Word."""
    v = get()
    ctx = {f"uq_{k}": v[k] for k in FIELDS}
    ctx["uq_danh_xung"] = "Bà" if v["gioi_tinh"] == "Nữ" else "Ông"
    return ctx
