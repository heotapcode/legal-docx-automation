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
    try:
        out["ty_le_coc"] = int(data.get("ty_le_coc") if data.get("ty_le_coc") not in (None, "") else 50)
    except (TypeError, ValueError):
        raise ValueError("Tỷ lệ đặt cọc phải là số phần trăm")
    if not 0 <= out["ty_le_coc"] <= 100:
        raise ValueError("Tỷ lệ đặt cọc từ 0 đến 100%")
    out["dia_chi_nhan_ho_so"] = " ".join(str(data.get("dia_chi_nhan_ho_so") or "").split())
    nh = data.get("ngan_hang") or {}
    from services import vietqr
    bank = {"ma_bin": str(nh.get("ma_bin") or ""), "so_tk": re.sub(r"\s", "", str(nh.get("so_tk") or "")),
            "chu_tk": vietqr.ascii_content(str(nh.get("chu_tk") or "")).upper()}
    if bank["ma_bin"] not in vietqr.BANKS:
        raise ValueError("Chọn ngân hàng nhận tiền")
    if not re.fullmatch(r"[0-9A-Za-z]{4,19}", bank["so_tk"]):
        raise ValueError("Số tài khoản gồm 4–19 chữ số")
    if not bank["chu_tk"]:
        raise ValueError("Thiếu tên chủ tài khoản")
    out["ngan_hang"] = bank
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


def gia_so(g: Dict[str, str]) -> int:
    """Giá gói thành số đồng ("3.200.000đ" -> 3200000); 0 khi giá là "Báo giá theo hồ sơ"."""
    digits = re.sub(r"[^\d]", "", str(g.get("gia") or ""))
    return int(digits) if digits else 0


def tien_coc(amount: int, cfg: Dict[str, Any] = None) -> int:
    cfg = cfg or get()
    pct = int(cfg.get("ty_le_coc", 50))
    return int(round(amount * pct / 100 / 1000) * 1000)


def public_view(template_id: str = "") -> Dict[str, Any]:
    """Phần được đưa ra trang công khai (không có email nhận báo)."""
    from services import leads, vietqr
    cfg = get()
    bank = cfg.get("ngan_hang") or {}
    out = {"ten_don_vi": cfg.get("ten_don_vi", ""), "zalo": cfg["zalo"], "cam_ket": cfg.get("cam_ket", ""),
           "goi": [dict(g, gia_so=gia_so(g)) for g in cfg["goi"]], "loi_dong_y": loi_dong_y(cfg),
           "ty_le_coc": cfg.get("ty_le_coc", 50), "dia_chi_nhan_ho_so": cfg.get("dia_chi_nhan_ho_so", ""),
           "ngan_hang": {"ten": vietqr.BANKS.get(bank.get("ma_bin"), ""), "so_tk": bank.get("so_tk", ""),
                         "chu_tk": bank.get("chu_tk", "")}}
    if template_id:
        first, second, _ = leads.GROUPS[leads.classify(template_id)]
        out["goi_goi_y"] = [m for m in (first, second) if m]
    return out
