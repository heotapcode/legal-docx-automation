"""Thay tên phòng đăng ký kinh doanh trong mẫu Word bằng biến {{ phong_dkkd }}.

Chạy sau localize_ha_noi.py, từ thư mục gốc repo (chạy lại nhiều lần vẫn an toàn):
    python scripts_and_tools/use_phong_dkkd.py [--dry-run]

Tên phòng khác nhau theo tỉnh (data/tinh_thanh.json):
    Hà Nội:     "Phòng Đăng ký kinh doanh và tài chính doanh nghiệp thành phố Hà Nội"
    tỉnh khác:  "Phòng Đăng ký kinh doanh tỉnh Bắc Ninh" / "... thành phố Đà Nẵng"
nên cả cụm "Phòng Đăng ký kinh doanh [và tài chính doanh nghiệp | - Sở Kế hoạch và Đầu tư] {{ tinh_thanh_dkkd }}"
được thay bằng {{ phong_dkkd }}. Dạng viết tắt trong "Nơi nhận" ("Phòng ĐKKD ...", "Cơ quan ĐKKD ...") giữ nguyên.
"""
import re
import sys
from pathlib import Path

import docx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from localize_ha_noi import TEMPLATES, iter_paragraphs, replace_span  # noqa: E402

PHONG_RE = re.compile(
    r"[Pp]hòng [Đđ]ăng ký [Kk]inh doanh"
    r"(?: và [Tt]ài chính doanh nghiệp| - Sở Kế hoạch và Đầu tư)?"
    r" \{\{\s*tinh_thanh_dkkd\s*\}\}"
)


def main():
    dry = "--dry-run" in sys.argv
    total = 0
    for f in sorted(TEMPLATES.glob("*/*.docx")):
        if f.name.startswith("~$"):
            continue
        doc = docx.Document(str(f))
        n = 0
        for p in iter_paragraphs(doc):
            for m in sorted(PHONG_RE.finditer(p.text), key=lambda m: m.start(), reverse=True):
                if dry:
                    print(f"  {f.parent.name[:30]:30} | {f.name[:34]:34} | «{m.group(0)}»")
                else:
                    replace_span(p, m.start(), m.end(), "{{ phong_dkkd }}")
                n += 1
        if n and not dry:
            doc.save(str(f))
        total += n
    print(f"{'Sẽ thay' if dry else 'Đã thay'} {total} chỗ")


if __name__ == "__main__":
    main()
