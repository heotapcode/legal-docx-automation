"""Danh mục tỉnh/thành phố (data/tinh_thanh.json) và các giá trị địa danh dùng trong mẫu Word.

Mẫu Word dùng:
    {{ noi_lap }}          nơi lập văn bản, đứng trước "ngày":  "Hà Nội", "TP. Hồ Chí Minh", "Bắc Ninh"
    {{ tinh_thanh_dkkd }}  địa danh của cơ quan đăng ký kinh doanh:  "thành phố Hà Nội", "tỉnh Bắc Ninh"
    {{ phong_dkkd }}       tên đầy đủ của phòng đăng ký kinh doanh:
                           "Phòng Đăng ký kinh doanh và tài chính doanh nghiệp thành phố Hà Nội",
                           "Phòng Đăng ký kinh doanh tỉnh Bắc Ninh" (tỉnh khác: mặc định theo mẫu này)
Giá trị chọn trên form nằm ở trường `tinh_dang_ky` (là `ten` trong danh mục, vd "Bắc Ninh").
"""
import json
import unicodedata
from functools import lru_cache
from typing import Dict, List, Optional

from config import DATA_DIR

TINH_THANH_JSON = DATA_DIR / "tinh_thanh.json"
FIELD_KEY = "tinh_dang_ky"


@lru_cache(maxsize=1)
def _load() -> dict:
    with open(TINH_THANH_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "").strip().lower()
    for prefix in ("thành phố ", "tp. ", "tp ", "tỉnh "):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return " ".join(s.split())


def list_tinh_thanh() -> List[Dict[str, str]]:
    """Danh sách cho ô chọn: value = ten, label = 'Thành phố Hà Nội' / 'Tỉnh Bắc Ninh'."""
    return [
        {"value": t["ten"], "label": f"{t['loai'].capitalize()} {t['ten']}", **t}
        for t in _load()["tinh_thanh"]
    ]


def default_tinh() -> str:
    return _load()["mac_dinh"]


def find_tinh(value: Optional[str]) -> Optional[dict]:
    """Tra theo tên, chấp nhận có/không tiền tố 'Thành phố', 'TP.', 'Tỉnh' và khác hoa/thường."""
    key = _norm(value or "")
    if not key:
        return None
    return next((t for t in _load()["tinh_thanh"] if _norm(t["ten"]) == key), None)


def context_values(value: Optional[str]) -> Dict[str, str]:
    """Các biến địa danh cho mẫu. Để trống -> tỉnh mặc định.

    Tên không có trong danh mục (vd tỉnh cũ trước sáp nhập 2025) -> ValueError, để API trả lỗi 400
    thay vì lặng lẽ in sai địa danh vào hồ sơ.
    """
    if value is None or not str(value).strip():
        tinh = find_tinh(default_tinh())
    else:
        tinh = find_tinh(str(value))
        if tinh is None:
            raise ValueError(
                f"Tỉnh/thành phố không hợp lệ: '{value}'. Chọn một trong: "
                + ", ".join(t["ten"] for t in _load()["tinh_thanh"])
            )
    tinh_thanh_dkkd = f"{tinh['loai']} {tinh['ten']}"
    return {
        FIELD_KEY: tinh["ten"],
        "noi_lap": tinh["noi_lap"],
        "tinh_thanh_dkkd": tinh_thanh_dkkd,
        "phong_dkkd": tinh.get("phong_dkkd") or f"Phòng Đăng ký kinh doanh {tinh_thanh_dkkd}",
    }


def co_quan_dk_ho_kinh_doanh(xa_phuong: Optional[str]) -> str:
    """Cơ quan đăng ký hộ kinh doanh cấp xã, theo xã/phường/đặc khu của trụ sở hộ kinh doanh.

    "Phường Đại Mỗ" -> "Phòng Kinh tế, Hạ tầng và Đô thị Phường Đại Mỗ"
    "Xã Phú Xuyên"  -> "Phòng Kinh tế Xã Phú Xuyên"   (xã và đặc khu)
    Mẫu Word dùng: {{ hkd_dia_chi_xa_phuong | co_quan_hkd }}
    """
    s = " ".join(unicodedata.normalize("NFC", xa_phuong or "").split())
    if not s:
        return ""
    s = s[0].upper() + s[1:]
    if s.lower().startswith("phường"):
        return f"Phòng Kinh tế, Hạ tầng và Đô thị {s}"
    return f"Phòng Kinh tế {s}"
