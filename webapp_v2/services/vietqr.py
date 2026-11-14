"""Mã QR chuyển khoản chuẩn VietQR (EMVCo, NAPAS): mọi ứng dụng ngân hàng quét được, tự điền số tiền và nội dung.

Tạo ngay trên máy chủ (thư viện segno), không gửi dữ liệu khách ra dịch vụ bên ngoài.
"""
import re
import unicodedata

# Mã ngân hàng (BIN) theo NAPAS
BANKS = {
    "970436": "Vietcombank", "970415": "VietinBank", "970418": "BIDV", "970405": "Agribank",
    "970407": "Techcombank", "970422": "MB Bank", "970416": "ACB", "970432": "VPBank", "970403": "Sacombank",
    "970423": "TPBank", "970441": "VIB", "970443": "SHB", "970437": "HDBank", "970448": "OCB", "970426": "MSB",
    "970440": "SeABank", "970449": "LPBank", "970431": "Eximbank", "970428": "Nam A Bank", "970427": "VietABank",
}


def _tlv(tag: str, value: str) -> str:
    return f"{tag}{len(value):02d}{value}"


def crc16_ccitt(data: str) -> str:
    crc = 0xFFFF
    for byte in data.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"


def ascii_content(text: str, limit: int = 50) -> str:
    """Nội dung chuyển khoản: bỏ dấu tiếng Việt, chỉ giữ chữ, số, khoảng trắng."""
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.sub(r"[^A-Za-z0-9 ]+", " ", text).split())[:limit]


def payload(bin_code: str, account: str, amount: int = 0, content: str = "") -> str:
    if bin_code not in BANKS:
        raise ValueError("Ngân hàng không hợp lệ")
    if not re.fullmatch(r"[0-9A-Za-z]{4,19}", account or ""):
        raise ValueError("Số tài khoản không hợp lệ")
    merchant = _tlv("00", "A000000727") + _tlv("01", _tlv("00", bin_code) + _tlv("01", account)) + _tlv("02", "QRIBFTTA")
    out = _tlv("00", "01") + _tlv("01", "12" if amount else "11") + _tlv("38", merchant) + _tlv("53", "704")
    if amount:
        out += _tlv("54", str(int(amount)))
    out += _tlv("58", "VN")
    content = ascii_content(content)
    if content:
        out += _tlv("62", _tlv("08", content))
    out += "6304"
    return out + crc16_ccitt(out)


def svg(data: str, scale: int = 5) -> str:
    import segno
    return segno.make(data, error="m").svg_inline(scale=scale, dark="#000", light="#fff")
