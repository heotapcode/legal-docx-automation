import os
from docx import Document

d = 'Mẫu Chuyển đổi loại hình 1TV sang 2 TV'
with open('_check_tv2.txt', 'w', encoding='utf-8') as f:
    doc = Document(os.path.join(d, '01. Quyết định.docx'))
    for p in doc.paragraphs:
        if 'TV2_HO_TEN' in p.text:
            f.write(p.text + '\n')
    f.write('--- ĐIỀU LỆ ---\n')
    doc2 = Document(os.path.join(d, '02. Điều lệ.docx'))
    for p in doc2.paragraphs:
        if 'TV2_HO_TEN' in p.text:
            f.write(p.text + '\n')
