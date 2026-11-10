"""Định dạng chữ và số dùng trong hồ sơ: tiền, số thành chữ, danh xưng, ngày tháng.

Tách từ render_service.py; render_service vẫn xuất lại các tên này để mã cũ dùng được.
"""
import re
from datetime import datetime
from typing import Any

VND_PER_VOTE = 1_000_000  # quy ước số tiền tương ứng 1 phiếu biểu quyết

def _is_negative(s: Any) -> bool:
    return str(s).strip().startswith("-")


def fmt_money(s: Any) -> str:
    if s is None:
        return ""
    digits = re.sub(r"[^\d]", "", str(s))
    if digits:
        return ("-" if _is_negative(s) and int(digits) else "") + "{:,}".format(int(digits))
    return str(s)

def so_thanh_chu(s: Any) -> str:
    if s is None:
        return ""
    digits = re.sub(r"[^\d]", "", str(s))
    if not digits:
        return str(s)
    n = int(digits)
    if n == 0:
        return "Không đồng"

    don_vi = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ"]
    chu_so = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

    def doc_ba_chu_so(val: int, co_nhom_cao: bool) -> str:
        tram = val // 100
        chuc = (val % 100) // 10
        dv = val % 10
        res = ""

        if tram > 0:
            res += chu_so[tram] + " trăm "
            if chuc == 0 and dv > 0:
                res += "linh "
        elif co_nhom_cao:
            res += "không trăm "
            if chuc == 0 and dv > 0:
                res += "linh "

        if chuc > 1:
            res += chu_so[chuc] + " mươi "
            if dv == 1:
                res += "mốt "
            elif dv == 5:
                res += "lăm "
            elif dv > 0:
                res += chu_so[dv] + " "
        elif chuc == 1:
            res += "mười "
            if dv == 1:
                res += "một "
            elif dv == 5:
                res += "lăm "
            elif dv > 0:
                res += chu_so[dv] + " "
        else:
            if dv > 0:
                res += chu_so[dv] + " "

        return res.strip()

    chuoi_kq = ""
    i = 0
    temp_n = n
    while temp_n > 0:
        phan_ba = temp_n % 1000
        co_nhom_cao = (temp_n // 1000) > 0
        if phan_ba > 0:
            doc_phan_ba = doc_ba_chu_so(phan_ba, co_nhom_cao)
            if doc_phan_ba:
                prefix = don_vi[i] + " " if don_vi[i] else ""
                chuoi_kq = doc_phan_ba + " " + prefix + chuoi_kq
        temp_n = temp_n // 1000
        i += 1

    chuoi_kq = chuoi_kq.strip()
    if _is_negative(s):
        chuoi_kq = "âm " + chuoi_kq
    return chuoi_kq.capitalize() + " đồng"

def danh_xung(gioi_tinh: Any) -> str:
    if not gioi_tinh:
        return "Ông/Bà"
    gt = str(gioi_tinh).strip().lower()
    if "nam" in gt:
        return "Ông"
    if "nữ" in gt or "nu" in gt:
        return "Bà"
    return "Ông/Bà"

def format_date_vn(d: Any = None) -> str:
    if d:
        from datetime import date
        if isinstance(d, (datetime, date)):
            dt = d
        elif isinstance(d, str):
            try:
                dt = datetime.strptime(d.strip(), "%d/%m/%Y")
            except ValueError:
                try:
                    dt = datetime.strptime(d.strip(), "%Y-%m-%d")
                except ValueError:
                    dt = datetime.now()
        else:
            dt = datetime.now()
    else:
        dt = datetime.now()
    return f"ngày {dt.day:02d} tháng {dt.month:02d} năm {dt.year}"
