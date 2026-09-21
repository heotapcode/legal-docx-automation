import os
from docx import Document

d = 'Mẫu Chuyển đổi loại hình 1TV sang 2 TV'
out = open('_review_cd1tv.txt', 'w', encoding='utf-8')

for fname in sorted(os.listdir(d)):
    if not fname.endswith('.docx') or fname.startswith('~'):
        continue
    filepath = os.path.join(d, fname)
    doc = Document(filepath)
    
    # Check paragraphs with context
    paras = doc.paragraphs
    for i, p in enumerate(paras):
        if 'HARDCODED' != '':
            txt = p.text
            if 'Giới tính' in txt or 'giới tính' in txt or 'GIOI_TINH' in txt:
                has_placeholder = '[' in txt and 'GIOI_TINH' in txt
                if not has_placeholder:
                    out.write(f"\n--- {fname} PARA {i} ---\n")
                    if i >= 2: out.write(f"  P{i-2}: {paras[i-2].text}\n")
                    if i >= 1: out.write(f"  P{i-1}: {paras[i-1].text}\n")
                    out.write(f"  P{i}: >>> {txt} <<<\n")
                    if i+1 < len(paras): out.write(f"  P{i+1}: {paras[i+1].text}\n")

    # Check tables with context
    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            row_texts = [cell.text.strip() for cell in row.cells]
            for c_idx, cell in enumerate(row.cells):
                for p in cell.paragraphs:
                    if 'Giới tính' in p.text and '[' not in p.text:
                        out.write(f"\n--- {fname} TABLE{t_idx} R{r_idx} ---\n")
                        out.write(f"  Row cells: {row_texts}\n")
                        if r_idx > 0:
                            prev_row_texts = [c.text.strip() for c in table.rows[r_idx-1].cells]
                            out.write(f"  Prev row:  {prev_row_texts}\n")

out.close()
