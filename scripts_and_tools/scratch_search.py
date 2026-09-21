import os
from docx import Document

out = open("giotinh.txt", "w", encoding="utf-8")
for f in os.scandir('Mẫu Chuyển nhượng Công ty TNHH 2 TV'):
    if f.name.endswith('.docx') and not f.name.startswith('~'):
        doc = Document(f.path)
        for i, p in enumerate(doc.paragraphs):
            if 'Giới' in p.text or 'giới' in p.text:
                out.write(f"[{f.name}] P{i}: {p.text}\n")
        
        # also search tables
        for t_idx, table in enumerate(doc.tables):
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell in enumerate(row.cells):
                    for i, p in enumerate(cell.paragraphs):
                        if 'Giới' in p.text or 'giới' in p.text:
                            out.write(f"[{f.name}] Table{t_idx} R{r_idx} C{c_idx} P{i}: {p.text}\n")
out.close()
