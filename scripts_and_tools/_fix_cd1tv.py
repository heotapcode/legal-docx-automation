import os, re
from docx import Document

d = 'Mẫu Chuyển đổi loại hình 1TV sang 2 TV'
count = 0

# 1. 03. Giấy đề nghị.docx - PARA 52: "Giới tính: Nữ" in DDPL section → [DDPL_GIOI_TINH]
fp = os.path.join(d, '03. Giấy đề nghị.docx')
doc = Document(fp)
for i, p in enumerate(doc.paragraphs):
    # Context: P50 = "8. Người đại diện theo pháp luật:", P51 = DDPL_HO_TEN, P52 = "Giới tính: Nữ"
    if p.text.strip() == 'Giới tính: Nữ' and i > 0 and 'DDPL_HO_TEN' in doc.paragraphs[i-1].text:
        p.text = p.text.replace('Giới tính: Nữ', 'Giới tính: [DDPL_GIOI_TINH]')
        count += 1
doc.save(fp)

# 2. Giấy chứng nhận góp vốn.docx - PARA 5: "Giới tính: Nam" in TV2 section → [TV2_GIOI_TINH]
fp = os.path.join(d, 'Giấy chứng nhận góp vốn.docx')
doc = Document(fp)
for i, p in enumerate(doc.paragraphs):
    if 'TV2_NGAY_SINH' in p.text and 'Giới tính: Nam' in p.text:
        p.text = p.text.replace('Giới tính: Nam', 'Giới tính: [TV2_GIOI_TINH]')
        count += 1
doc.save(fp)

with open('_fix_result.txt', 'w', encoding='utf-8') as f:
    f.write(f"Fixed {count} positions\n")
