import os, re
from docx import Document

d = 'Mẫu Chuyển đổi loại hình 1TV sang 2 TV'
out = open('_placeholders.txt', 'w', encoding='utf-8')

all_ph = set()
for f in os.scandir(d):
    if f.name.endswith('.docx') and not f.name.startswith('~'):
        doc = Document(f.path)
        phs = set()
        for p in doc.paragraphs:
            for m in re.findall(r'\[[A-Z0-9_]+\]', p.text):
                phs.add(m)
                all_ph.add(m)
        out.write(f"{f.name}: {list(phs)}\n")

out.write(f"\nALL: {sorted(list(all_ph))}\n")
out.close()
