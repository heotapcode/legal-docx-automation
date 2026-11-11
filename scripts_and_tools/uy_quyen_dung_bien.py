"""Thay thông tin người nhận ủy quyền viết cứng trong các mẫu Word bằng biến {{ uq_* }}.

Giá trị lấy từ webapp_v2/data/nguoi_nhan_uy_quyen.json (sửa được trên trang quản trị), xem services/uy_quyen.py.
Chạy từ thư mục gốc repo (chạy lại nhiều lần vẫn an toàn):
    python scripts_and_tools/uy_quyen_dung_bien.py [--dry-run]
Dùng khi thêm bộ mẫu mới có Giấy ủy quyền chép từ hồ sơ cũ.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

import docx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from localize_ha_noi import TEMPLATES, iter_paragraphs, replace_span  # noqa: E402

V = json.loads((TEMPLATES.parent / "data" / "nguoi_nhan_uy_quyen.json").read_text(encoding="utf-8"))
SDT_DIGITS = re.sub(r"\D", "", V["sdt"])
REPLACEMENTS = [  # (mẫu tìm, chuỗi thay)
    (re.compile(re.escape(V["ho_ten"].upper())), "{{ uq_ho_ten | upper }}"),
    (re.compile(re.escape(V["ho_ten"].title())), "{{ uq_ho_ten | title }}"),
    (re.compile(re.escape(V["so_cccd"])), "{{ uq_so_cccd }}"),
    (re.compile(re.escape(V["sdt"])), "{{ uq_sdt }}"),
    (re.compile(re.escape(SDT_DIGITS)), "{{ uq_sdt | replace('.', '') }}"),
    (re.compile(re.escape(V["email"])), "{{ uq_email }}"),
    (re.compile(re.escape(V["dia_chi"])), "{{ uq_dia_chi }}"),
    (re.compile(re.escape(V["ngay_sinh"])), "{{ uq_ngay_sinh }}"),
]
# Chỉ áp dụng trên đoạn đã có biến uq_ (dòng của người nhận ủy quyền)
ON_UQ_LINES = [
    (re.compile(r"\bÔng(?=\s*:)"), "{{ uq_danh_xung }}"),
    (re.compile(r"(?<=Giới tính: )Nam\b"), "{{ uq_gioi_tinh }}"),
]


def fix_paragraph(p) -> int:
    n = 0
    for rules, only_uq in ((REPLACEMENTS, False), (ON_UQ_LINES, True)):
        for rx, new in rules:
            while True:
                text = p.text
                if only_uq and "uq_" not in text:
                    break
                # So khớp trên dạng NFC; chỉ thay khi độ dài trùng (vị trí ký tự giữ nguyên)
                nfc = unicodedata.normalize("NFC", text)
                m = rx.search(nfc if len(nfc) == len(text) else text)
                if not m:
                    break
                replace_span(p, m.start(), m.end(), new)
                n += 1
    return n


def main():
    dry = "--dry-run" in sys.argv
    total = 0
    for f in sorted(TEMPLATES.glob("*/*.docx")):
        doc = docx.Document(str(f))
        n = sum(fix_paragraph(p) for p in iter_paragraphs(doc))
        if n:
            total += n
            print(f"{n:3d}  {f.parent.name}/{f.name}")
            if not dry:
                doc.save(str(f))
    print(f"Tổng: {total} chỗ" + (" (chạy thử, chưa ghi)" if dry else ""))


if __name__ == "__main__":
    main()
