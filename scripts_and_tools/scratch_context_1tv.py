import os
from docx import Document

out = open("giotinh_1tv_context.txt", "w", encoding="utf-8")
for f in os.scandir('Mẫu Chuyển nhượng công ty TNHH 1 TV'):
    if f.name.endswith('.docx') and not f.name.startswith('~'):
        doc = Document(f.path)
        for i, p in enumerate(doc.paragraphs):
            if 'Giới' in p.text or 'giới' in p.text:
                out.write(f"\n--- {f.name} P{i} ---\n")
                if i > 0: out.write(f"Prev: {doc.paragraphs[i-1].text}\n")
                out.write(f"Curr: {p.text}\n")
        
        # also search tables
        for t_idx, table in enumerate(doc.tables):
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell in enumerate(row.cells):
                    for i, p in enumerate(cell.paragraphs):
                        if 'Giới' in p.text or 'giới' in p.text:
                            out.write(f"\n--- {f.name} Table{t_idx} R{r_idx} C{c_idx} P{i} ---\n")
                            out.write(f"Curr: {p.text}\n")
out.close()
