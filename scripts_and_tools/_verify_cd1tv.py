import os
from docx import Document

d = 'Mẫu Chuyển đổi loại hình 1TV sang 2 TV'
out = open('_verify_cd1tv.txt', 'w', encoding='utf-8')

for fname in sorted(os.listdir(d)):
    if not fname.endswith('.docx') or fname.startswith('~'):
        continue
    doc = Document(os.path.join(d, fname))
    for i, p in enumerate(doc.paragraphs):
        if 'GIOI_TINH' in p.text or ('Giới tính' in p.text and 'Nam' in p.text) or ('Giới tính' in p.text and 'Nữ' in p.text):
            is_placeholder = '[' in p.text and 'GIOI_TINH' in p.text
            status = 'OK' if is_placeholder else 'HARDCODED'
            out.write(f"[{status}] {fname} P{i}: {p.text.strip()}\n")

out.close()
