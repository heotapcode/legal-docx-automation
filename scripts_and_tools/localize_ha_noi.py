"""Thay chữ "Hà Nội" viết cứng trong các mẫu Word bằng biến theo ô chọn tỉnh/thành phố.

Chạy từ thư mục gốc repo (chạy lại nhiều lần vẫn an toàn):
    python scripts_and_tools/localize_ha_noi.py            # sửa file
    python scripts_and_tools/localize_ha_noi.py --dry-run  # chỉ liệt kê

Hai nhóm được thay:
  A. Nơi lập văn bản:  "Hà Nội, ngày ..."                       -> "{{ noi_lap }}, ngày ..."
  B. Cơ quan đăng ký:  "Phòng Đăng ký kinh doanh ... TP/thành phố Hà Nội"
                       "Phòng ĐKKD TP Hà Nội", "Cơ quan ĐKKD TP Hà Nội",
                       "Sở Kế hoạch và Đầu tư Hà Nội"                  -> "... {{ tinh_thanh_dkkd }}"
  Cơ quan đăng ký đang dùng tỉnh trong địa chỉ cá nhân ({{ ddpl_dia_chi_tinh_thanh }}) cũng được sửa.
KHÔNG thay địa chỉ cá nhân (vd "TK Đường, Phú Xuyên, Hà Nội") vì đó là dữ liệu của một người.
"""
import re
import sys
from pathlib import Path

import docx

TEMPLATES = Path(__file__).resolve().parent.parent / "webapp_v2" / "templates"

# A: "Hà Nội," đứng trước "ngày" hoặc ở cuối đoạn (dòng ngày nằm ở đoạn/ô kế tiếp)
# (\0 = vị trí của một thẻ Jinja đã che, vd "Hà Nội, {{ ngay_lap }}")
PLACE_RE = re.compile(r"Hà\s*[Nn]ội(?=\s*,\s*(?:ngày|\0|$))")
# B: chỉ thay phần địa danh sau tên cơ quan đăng ký (nhóm 1 = tên cơ quan, giữ nguyên)
AUTHORITY_LONG_RE = re.compile(
    r"([Pp]hòng [Đđ]ăng ký [Kk]inh doanh và [Tt]ài chính doanh nghiệp )(?:[Tt]hành phố|TP\.?) Hà Nội"
)
AUTHORITY_SHORT_RE = re.compile(
    r"((?:[Pp]hòng [Đđ]ăng ký [Kk]inh doanh|Phòng ĐKKD|Cơ quan ĐKKD) )(?:[Tt]hành phố|TP\.?) Hà Nội"
    r"|(Sở Kế hoạch và Đầu tư )Hà Nội"
)
JINJA_RE = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.S)
# Cơ quan đăng ký lấy nhầm tỉnh trong địa chỉ cá nhân (vd {{ ddpl_dia_chi_tinh_thanh }})
AUTHORITY_PERSONAL_VAR_RE = re.compile(
    r"((?:[Pp]hòng [Đđ]ăng ký [Kk]inh doanh(?: và [Tt]ài chính doanh nghiệp)?|Phòng ĐKKD|Cơ quan ĐKKD) )"
    r"\{\{\s*\w+_dia_chi_tinh_thanh\s*\}\}"
)


def iter_paragraphs(doc):
    def walk(container):
        for p in container.paragraphs:
            yield p
        for t in getattr(container, "tables", []):
            for row in t.rows:
                for cell in row.cells:
                    yield from walk(cell)
    yield from walk(doc)
    for s in doc.sections:
        for part in (s.header, s.footer):
            yield from walk(part)


def replace_span(p, start: int, end: int, new: str):
    """Thay p.text[start:end] bằng `new`, kể cả khi đoạn đó trải qua nhiều run."""
    pos = 0
    first = None
    for r in p.runs:
        r_start, r_end = pos, pos + len(r.text)
        pos = r_end
        if r_end <= start or r_start >= end:
            continue
        a, b = max(start, r_start) - r_start, min(end, r_end) - r_start
        if first is None:
            first = r
            r.text = r.text[:a] + new + r.text[b:]
        else:
            r.text = r.text[:a] + r.text[b:]
    assert first is not None, "không tìm thấy run chứa đoạn cần thay"


def matches(text: str):
    """Các (start, end, new) cần thay trong đoạn, bỏ qua phần nằm trong thẻ Jinja."""
    masked = JINJA_RE.sub(lambda m: "\0" * len(m.group(0)), text)
    found = []
    for rx in (AUTHORITY_LONG_RE, AUTHORITY_SHORT_RE):
        for m in rx.finditer(masked):
            prefix = next(g for g in m.groups() if g is not None)
            s = m.start() + len(prefix)
            if all(not (s < e2 and m.end() > s2) for s2, e2, _ in found):
                found.append((s, m.end(), "{{ tinh_thanh_dkkd }}"))
    for m in AUTHORITY_PERSONAL_VAR_RE.finditer(text):
        found.append((m.start() + len(m.group(1)), m.end(), "{{ tinh_thanh_dkkd }}"))
    for m in PLACE_RE.finditer(masked):
        if all(not (m.start() < e2 and m.end() > s2) for s2, e2, _ in found):
            found.append((m.start(), m.end(), "{{ noi_lap }}"))
    return sorted(found, reverse=True)  # thay từ cuối về đầu để vị trí không lệch


def process(path: Path, dry_run: bool) -> int:
    doc = docx.Document(str(path))
    n = 0
    for p in iter_paragraphs(doc):
        text = p.text
        for start, end, new in matches(text):
            if dry_run:
                print(f"  {path.parent.name[:30]:30} | {path.name[:34]:34} | «{text[max(0, start-25):end+8]}» -> {new}")
            else:
                replace_span(p, start, end, new)
            n += 1
    if n and not dry_run:
        doc.save(str(path))
    return n


def main():
    dry = "--dry-run" in sys.argv
    total = 0
    for f in sorted(TEMPLATES.glob("*/*.docx")):
        if f.name.startswith("~$"):
            continue
        total += process(f, dry)
    print(f"{'Sẽ thay' if dry else 'Đã thay'} {total} chỗ")


if __name__ == "__main__":
    main()
