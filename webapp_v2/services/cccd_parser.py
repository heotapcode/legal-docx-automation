"""Phân tích dữ liệu CCCD/VNeID từ nội dung QR hoặc văn bản OCR. Không phụ thuộc thư viện ảnh.

Kết quả luôn có đủ các khóa mà giao diện đang dùng, cộng thêm:
    nguon        "qr" hoặc "ocr"
    can_kiem_tra danh sách trường người dùng nên rà lại trước khi sinh hồ sơ
"""
import re
import unicodedata
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from services.dia_ban import list_tinh_thanh

ADDRESS_PARTS = ("dia_chi_so_nha", "dia_chi_xa_phuong", "dia_chi_quan_huyen", "dia_chi_tinh_thanh")


def _fold_char(c: str) -> str:
    if c in "đĐ":
        return "d"
    base = unicodedata.normalize("NFD", c)[0]
    return base.lower() if len(base.lower()) == 1 else base


def fold(s: str) -> str:
    """Bỏ dấu, viết thường, giữ nguyên độ dài để dùng lại vị trí khớp trên chuỗi gốc."""
    return "".join(_fold_char(c) for c in s)


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s or "")


def _clean(s: str) -> str:
    return " ".join(s.split()).strip(" ,.;:|-_/\\'\"")


def _valid_date(day: str, month: str, year: str) -> str:
    try:
        d = datetime(int(year), int(month), int(day))
    except ValueError:
        return ""
    return d.strftime("%d/%m/%Y") if 1900 <= d.year <= datetime.now().year else ""


def _normalize_gender(raw: str) -> str:
    words = re.findall(r"[a-z]+", fold(raw))
    if "nu" in words:
        return "Nữ"
    return "Nam" if "nam" in words else ""


def cccd_conflicts(so_cccd: str, ngay_sinh: str, gioi_tinh: str) -> List[str]:
    """So số CCCD (chữ số thứ 4: thế kỷ + giới tính; thứ 5-6: năm sinh) với ngày sinh và giới tính."""
    if not re.fullmatch(r"\d{12}", so_cccd or ""):
        return ["so_cccd"]
    code = int(so_cccd[3])
    century = 1900 + 100 * (code // 2)
    conflicts = []
    if ngay_sinh and int(ngay_sinh[-4:]) != century + int(so_cccd[4:6]):
        conflicts += ["so_cccd", "ngay_sinh"]
    if gioi_tinh and gioi_tinh != ("Nữ" if code % 2 else "Nam"):
        conflicts += ["so_cccd", "gioi_tinh"]
    return conflicts


def _gender_from_cccd(so_cccd: str) -> str:
    if re.fullmatch(r"\d{12}", so_cccd or ""):
        return "Nữ" if int(so_cccd[3]) % 2 else "Nam"
    return ""


# ---------- Tách địa chỉ ----------
_XA_RE = re.compile(r"^(?:xa|phuong|thi\s+tran|dac\s+khu)\s|^(?:p|x|tt)\.\s*")
_HUYEN_RE = re.compile(r"^(?:quan|huyen|thi\s+xa|thanh\s+pho)\s|^(?:q|h|tx|tp)\.\s*")
_TINH_PREFIX_RE = re.compile(r"^(?:thanh\s+pho|tinh|tp\.?)\s*")


def _match_province(raw: str) -> Optional[str]:
    key = " ".join(_TINH_PREFIX_RE.sub("", fold(raw)).split())
    if key in ("hcm", "ho chi minh"):
        key = "ho chi minh"
    for t in list_tinh_thanh():
        if " ".join(fold(t["ten"]).split()) == key:
            return f"{t['loai'].title()} {t['ten']}"
    return None


def split_address(address: str) -> Tuple[Dict[str, str], List[str]]:
    """Tách địa chỉ thành số nhà / xã phường / quận huyện / tỉnh thành và các phần chưa chắc chắn."""
    empty = {k: "" for k in ADDRESS_PARTS}
    parts = [p for p in (_clean(x) for x in re.split(r"[,\n;]|\s-\s", _nfc(address))) if p]
    if not parts:
        return empty, list(ADDRESS_PARTS)

    raw_province = parts.pop()
    province = _match_province(raw_province)
    # Tỉnh không thuộc danh mục 34 tỉnh sau sáp nhập (hoặc OCR đọc sai): vẫn giữ để người dùng sửa
    review = [] if province else ["dia_chi_tinh_thanh"]
    result = dict(empty, dia_chi_tinh_thanh=province or raw_province)

    folded = [fold(p) + " " for p in parts]
    xa_idx = next((i for i in range(len(parts) - 1, -1, -1) if _XA_RE.search(folded[i])), None)
    if xa_idx is not None:
        result["dia_chi_xa_phuong"] = parts[xa_idx]
        result["dia_chi_so_nha"] = ", ".join(parts[:xa_idx])
        result["dia_chi_quan_huyen"] = ", ".join(parts[xa_idx + 1:])
        return result, review

    # Không ghi rõ "Xã/Phường": suy theo vị trí, cần người dùng rà lại
    if parts and (len(parts) >= 3 or _HUYEN_RE.search(folded[-1])):
        result["dia_chi_quan_huyen"] = parts.pop()
    if parts:
        result["dia_chi_xa_phuong"] = parts.pop()
    result["dia_chi_so_nha"] = ", ".join(parts)
    return result, review + ["dia_chi_so_nha", "dia_chi_xa_phuong"]


def _build(ho_ten: str, ngay_sinh: str, gioi_tinh: str, so_cccd: str, dia_chi: str,
           nguon: str, review: List[str]) -> Dict:
    parts, address_review = split_address(dia_chi)
    if not gioi_tinh:
        gioi_tinh = _gender_from_cccd(so_cccd)
    values = {"ho_ten": ho_ten, "ngay_sinh": ngay_sinh, "gioi_tinh": gioi_tinh, "so_cccd": so_cccd}
    flagged = set(review) | set(address_review) | set(cccd_conflicts(so_cccd, ngay_sinh, gioi_tinh))
    flagged |= {k for k, v in values.items() if not v}
    return {**values, "dia_chi": dia_chi, **parts, "nguon": nguon, "can_kiem_tra": sorted(flagged)}


# ---------- QR ----------
def parse_qr(text: str) -> Optional[Dict]:
    """Nội dung QR: Số CCCD|Số CMND|Họ tên|Ngày sinh (DDMMYYYY)|Giới tính|Địa chỉ|Ngày cấp."""
    parts = [p.strip() for p in _nfc(text).split("|")]
    if len(parts) < 6 or not re.fullmatch(r"\d{12}", parts[0]):
        return None
    raw_date = parts[3]
    ngay_sinh = _valid_date(raw_date[:2], raw_date[2:4], raw_date[4:]) if re.fullmatch(r"\d{8}", raw_date) else ""
    if not parts[2] or not ngay_sinh:
        return None
    return _build(parts[2].upper(), ngay_sinh, _normalize_gender(parts[4]), parts[0], parts[5], "qr", [])


# ---------- OCR ----------
_NAME_LABEL = re.compile(r"ho\s*(?:,|va)?\s*(?:chu\s+dem\s+va\s+)?ten(?:\s+khai\s+sinh)?|full\s*name|given\s+name")
_DOB_LABEL = re.compile(r"ngay\s*,?\s*(?:thang\s*,?\s*nam\s*)?sinh|date\s+of\s+birth")
_GENDER_LABEL = re.compile(r"gioi\s*tinh|\bsex\b|\bgender\b")
_ID_LABEL = re.compile(r"so\s+dinh\s+danh|personal\s+identification|so\s+cccd|so\s+can\s+cuoc|^\s*so\s*/\s*no\b")
_ADDRESS_LABEL = re.compile(r"noi\s+thuong\s+tru|noi\s+cu\s+tru|thuong\s+tru|place\s+of\s+residence")
_ADDRESS_STOP = re.compile(
    r"que\s*quan|place\s+of\s+origin|noi\s+o\s+hien\s+tai|noi\s+tam\s+tru|nghe\s+nghiep|co\s+gia\s+tri|date\s+of\s+expiry|ngay\s+cap"
    r"|quoc\s*tich|nationality|ngay\s*,?\s*sinh|so\s+dinh\s+danh|dac\s+diem|nhom\s+mau|ton\s+giao"
    r"|dan\s+toc|gioi\s*tinh|noi\s+dang\s+ky|chu\s+ho|quan\s+he"
)
_ENGLISH_REST = re.compile(
    r"^[\s/|]*(?:full\s*name|surname[\sa-z,]*given\s+name|date\s+of\s+birth|sex|gender|no\.?"
    r"|personal\s+identification\s+number|place\s+of\s+residence)?\s*[:.]?\s*"
)
_DATE = re.compile(r"(?<!\d)(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})(?!\d)")
_TWELVE_DIGITS = re.compile(r"(?<!\d)\d{12}(?!\d)")
_NAME_VALUE = re.compile(r"^[^\W\d_]+(?:\s+[^\W\d_]+)+$")


# OCR hay mất dấu ở chữ in hoa; chỉ sửa những cụm hầu như không có cách đọc khác
_SURNAMES = {fold(s): s for s in (
    "NGUYỄN", "TRẦN", "PHẠM", "HOÀNG", "HUỲNH", "VŨ", "VÕ", "ĐẶNG", "BÙI", "ĐỖ", "HỒ", "NGÔ", "DƯƠNG", "LÝ",
)}
_ADDRESS_FIXES = [(re.compile(p), v) for p, v in (
    (r"\bto\s+dan\s+pho\b", "Tổ dân phố"),
    (r"\bkhu\s+pho\b", "Khu phố"),
    (r"\bthi\s+tran\b", "Thị trấn"),
    (r"\bthanh\s+pho\b", "Thành phố"),
    (r"\bthon\b", "Thôn"),
    (r"\bdong\b(?=\s*,)", "Đông"),
    (r"\bpho(?=\s+[a-z])", "Phố"),
    (r"\bso(?=\s+\d)", "Số"),
    (r"\bto(?=\s+\d)", "Tổ"),
    (r"\bngo(?=\s+\d)", "Ngõ"),
    (r"\bngach(?=\s+\d)", "Ngách"),
)]


def _fix_surname(name: str) -> str:
    first, _, rest = name.partition(" ")
    return f"{_SURNAMES.get(fold(first), first)} {rest}"


def _fix_address_words(address: str) -> str:
    for pattern, canonical in _ADDRESS_FIXES:
        def replace(m: "re.Match") -> str:
            # fold() giữ nguyên độ dài nên vị trí khớp dùng được trên chuỗi gốc
            original = address[m.start():m.end()]
            if len(" ".join(original.split())) != len(canonical):
                return original
            if original.isupper():
                return canonical.upper()
            return canonical[0].lower() + canonical[1:] if original[0].islower() else canonical
        address = "".join(_sub_on_folded(address, pattern, replace))
    return address


def _sub_on_folded(text: str, pattern: "re.Pattern", replace) -> List[str]:
    pieces, pos = [], 0
    for m in pattern.finditer(fold(text)):
        pieces += [text[pos:m.start()], replace(m)]
        pos = m.end()
    return pieces + [text[pos:]]


def _rest_after(line: str, end: int) -> str:
    rest, folded = line[end:], fold(line[end:])
    colon = rest[:60].find(":")
    if colon >= 0:
        return rest[colon + 1:].strip()
    return rest[_ENGLISH_REST.match(folded).end():].strip()


def _find_label(lines: List[str], label: "re.Pattern") -> Optional[Tuple[int, str]]:
    for i, line in enumerate(lines):
        m = label.search(fold(line))
        if m:
            return i, _rest_after(line, m.end())
    return None


def _ocr_name(lines: List[str]) -> str:
    found = _find_label(lines, _NAME_LABEL)
    if not found:
        return ""
    i, rest = found
    for candidate in [rest] + lines[i + 1:i + 5]:
        candidate = _name_prefix(candidate.strip().split("\t")[0])  # phần sau khoảng trống lớn là biểu tượng/nhiễu
        if _is_person_name(candidate):
            return _fix_surname(candidate.upper())
    return ""


def _name_prefix(line: str) -> str:
    """Giữ các từ chữ cái ở đầu dòng, dừng ở từ đầu tiên là nhiễu nền (ký hiệu, chữ lẻ)."""
    words = []
    for token in line.split():
        word = token.strip(".,:;'\"`“”‘’")
        if len(word) < 2 or not word.isalpha() or (words and words[0].isupper() and not word.isupper()):
            break
        words.append(word)
    return " ".join(words)


def _is_person_name(value: str) -> bool:
    folded = fold(value)
    return bool(
        _NAME_VALUE.match(value)
        and all(len(word) >= 2 for word in value.split())
        and not any(p.search(folded) for p in (_NAME_LABEL, _DOB_LABEL, _GENDER_LABEL, _ADDRESS_LABEL))
    )


def _ocr_date(lines: List[str]) -> str:
    found = _find_label(lines, _DOB_LABEL)
    if not found:
        return ""
    i, rest = found
    for candidate in [rest] + lines[i + 1:i + 3]:
        m = _DATE.search(candidate)
        if m and _valid_date(*m.groups()):
            return _valid_date(*m.groups())
    return ""


def _ocr_gender(lines: List[str]) -> str:
    found = _find_label(lines, _GENDER_LABEL)
    if not found:
        return ""
    i, rest = found
    for candidate in [rest] + lines[i + 1:i + 2]:
        m = re.search(r"quoc\s*tich|nationality", fold(candidate))  # "Việt Nam" không phải giới tính
        gender = _normalize_gender(candidate[:m.start()] if m else candidate)
        if gender:
            return gender
    return ""


def _twelve_digits(line: str) -> Optional[str]:
    m = _TWELVE_DIGITS.search(re.sub(r"(?<=\d)[ .](?=\d)", "", line))
    return m.group(0) if m else None


def _ocr_id(lines: List[str]) -> str:
    found = _find_label(lines, _ID_LABEL)
    if found:
        i, rest = found
        for candidate in [rest] + lines[i + 1:i + 3]:
            value = _twelve_digits(candidate)
            if value:
                return value
    candidates = {v for v in map(_twelve_digits, lines) if v}
    return candidates.pop() if len(candidates) == 1 else ""


def _ocr_address(lines: List[str]) -> str:
    found = _find_label(lines, _ADDRESS_LABEL)
    if not found:
        return ""
    i, rest = found
    collected = []
    for line in [rest] + lines[i + 1:i + 4]:
        stop = _ADDRESS_STOP.search(fold(line))
        raw = _DATE.sub("", line[:stop.start()] if stop else line)
        part = _clean(raw)
        if re.search(r"[^\W\d_]", part):
            collected.append(part + ("," if raw.rstrip().endswith(",") else ""))  # giữ ranh giới khi địa chỉ xuống dòng
        if stop:
            break
    return _clean(" ".join(collected))


def _build_ocr(ho_ten: str, ngay_sinh: str, gioi_tinh: str, so_cccd: str, dia_chi: str) -> Dict:
    # Số được đối chiếu chéo nên không cần cờ; lỗi dấu trong chữ thì không tự phát hiện được
    review = ["ho_ten"] + ([k for k in ADDRESS_PARTS if k != "dia_chi_quan_huyen"] if dia_chi else [])
    return _build(ho_ten, ngay_sinh, gioi_tinh, so_cccd, dia_chi, "ocr", review)


def parse_ocr_text(text: str) -> Dict:
    lines = [_nfc(x).strip() for x in text.splitlines() if x.strip()]
    return _build_ocr(_ocr_name(lines), _ocr_date(lines), _ocr_gender(lines), _ocr_id(lines),
                      _fix_address_words(_ocr_address(lines)))


def combine_ocr(results: List[Dict]) -> Dict:
    """Gộp nhiều lần đọc: mỗi trường lấy giá trị xuất hiện nhiều nhất, hòa thì lấy bản dài hơn."""
    def vote(key: str) -> str:
        values = [r[key] for r in results if r.get(key)]
        return max(values, key=lambda v: (values.count(v), len(v))) if values else ""

    return _build_ocr(vote("ho_ten"), vote("ngay_sinh"), vote("gioi_tinh"), vote("so_cccd"), vote("dia_chi"))


def ocr_score(data: Dict) -> int:
    """Số trường chính đọc được, dùng để chọn lần OCR tốt nhất."""
    return sum(bool(data.get(k)) for k in ("ho_ten", "ngay_sinh", "so_cccd", "dia_chi"))
