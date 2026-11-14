"""Thông tin kinh doanh dùng cho phễu khách: số Zalo, email nhận báo khách mới, bảng giá các gói, lời cam kết.

Giá trị mặc định ở data/kinh_doanh.json; trang quản trị lưu giá trị sửa vào bảng `settings` của CSDL quản trị
(cùng cách với services/uy_quyen.py).
"""
import json
import re
from typing import Any, Dict, List

from config import DATA_DIR

DEFAULT_JSON = DATA_DIR / "kinh_doanh.json"
SETTING_KEY = "kinh_doanh"
TEXT_FIELDS = ("ten_don_vi", "zalo", "email_nhan_bao", "cam_ket")
GOI_FIELDS = ("ma", "ten", "gia", "mo_ta")


def defaults() -> Dict[str, Any]:
    data = json.loads(DEFAULT_JSON.read_text(encoding="utf-8"))
    data.pop("_ghi_chu", None)
    return data


def get() -> Dict[str, Any]:
    out = defaults()
    try:
        from services import admin_db
        saved = admin_db.get_setting(SETTING_KEY)
    except Exception:  # CSDL quản trị chưa sẵn sàng: dùng mặc định
        saved = None
    if saved:
        out.update(json.loads(saved))
    return out


def validate(data: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {k: " ".join(str(data.get(k, "") or "").split()) for k in TEXT_FIELDS}
    zalo = re.sub(r"[\s.]", "", out["zalo"])
    if not re.fullmatch(r"0\d{9}", zalo):
        raise ValueError("Số Zalo gồm 10 chữ số, bắt đầu bằng 0")
    out["zalo"] = zalo
    if out["email_nhan_bao"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", out["email_nhan_bao"]):
        raise ValueError("Email nhận báo khách mới không hợp lệ")
    try:
        out["thoi_gian_luu_thang"] = int(data.get("thoi_gian_luu_thang") or 24)
    except (TypeError, ValueError):
        raise ValueError("Thời gian lưu thông tin khách phải là số tháng")
    if not 1 <= out["thoi_gian_luu_thang"] <= 120:
        raise ValueError("Thời gian lưu thông tin khách từ 1 đến 120 tháng")
    goi: List[Dict[str, str]] = []
    known = {g["ma"] for g in defaults()["goi"]}
    for g in data.get("goi") or []:
        item = {k: " ".join(str(g.get(k, "") or "").split()) for k in GOI_FIELDS}
        if item["ma"] not in known:
            raise ValueError(f"Gói không hợp lệ: {item['ma']}")
        if not item["ten"] or not item["gia"]:
            raise ValueError(f"Gói {item['ma']}: thiếu tên hoặc giá")
        goi.append(item)
    if {g["ma"] for g in goi} != known:
        raise ValueError("Phải có đủ các gói: " + ", ".join(sorted(known)))
    out["goi"] = goi
    return out


def save(data: Dict[str, Any], user_id=None) -> Dict[str, Any]:
    from services import admin_db
    clean = validate(data)
    admin_db.set_setting(SETTING_KEY, json.dumps(clean, ensure_ascii=False), user_id)
    return clean


def goi_by_ma(cfg: Dict[str, Any] = None) -> Dict[str, Dict[str, str]]:
    cfg = cfg or get()
    return {g["ma"]: g for g in cfg["goi"]}


def ten_don_vi(cfg: Dict[str, Any] = None) -> str:
    cfg = cfg or get()
    return cfg.get("ten_don_vi") or "chúng tôi"


def loi_dong_y(cfg: Dict[str, Any] = None) -> str:
    """Câu đồng ý xử lý dữ liệu cá nhân hiện ở bước giữ khách (lưu kèm từng khách)."""
    cfg = cfg or get()
    return (f"Tôi đồng ý để {ten_don_vi(cfg)} lưu họ tên, số điện thoại và tên thủ tục tôi vừa tạo để liên hệ tư vấn "
            f"về hồ sơ này. Thông tin được lưu tối đa {cfg.get('thoi_gian_luu_thang', 24)} tháng; tôi có thể yêu cầu "
            f"xóa bất cứ lúc nào qua Zalo {cfg['zalo']}.")


def public_view() -> Dict[str, Any]:
    """Phần được đưa ra trang công khai (không có email nhận báo)."""
    cfg = get()
    return {"ten_don_vi": cfg.get("ten_don_vi", ""), "zalo": cfg["zalo"], "cam_ket": cfg.get("cam_ket", ""),
            "goi": cfg["goi"], "loi_dong_y": loi_dong_y(cfg)}
