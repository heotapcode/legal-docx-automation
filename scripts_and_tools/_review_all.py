import os
from docx import Document

done = [
    'Mẫu Chuyển nhượng Công ty TNHH 2 TV',
    'Mẫu Chuyển nhượng công ty TNHH 1 TV'
]

dirs = sorted([d for d in os.listdir('.') if os.path.isdir(d) and d.startswith('Mẫu') and d not in done])

out = open('_review_all.txt', 'w', encoding='utf-8')

for d in dirs:
    out.write(f"\n{'='*80}\n")
    out.write(f"FOLDER: {d}\n")
    out.write(f"{'='*80}\n")
    
    files = [f for f in os.listdir(d) if f.endswith('.docx') and not f.startswith('~')]
    
    for fname in sorted(files):
        filepath = os.path.join(d, fname)
        try:
            doc = Document(filepath)
        except Exception as e:
            out.write(f"  [ERROR] {fname}: {e}\n")
            continue
        
        found_para = []
        found_table = []
        
        # Check paragraphs
        for i, p in enumerate(doc.paragraphs):
            txt = p.text
            if 'Giới tính' in txt or 'giới tính' in txt or 'GIOI_TINH' in txt:
                found_para.append((i, txt.strip()))
        
        # Check tables
        for t_idx, table in enumerate(doc.tables):
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell in enumerate(row.cells):
                    for p in cell.paragraphs:
                        txt = p.text
                        if 'Giới tính' in txt or 'giới tính' in txt or 'GIOI_TINH' in txt:
                            found_table.append((t_idx, r_idx, c_idx, txt.strip()))
        
        if found_para or found_table:
            out.write(f"\n  FILE: {fname}\n")
            for i, txt in found_para:
                has_placeholder = '[' in txt and 'GIOI_TINH' in txt
                status = 'OK' if has_placeholder else 'HARDCODED'
                out.write(f"    [PARA {i}] [{status}] {txt}\n")
            for t, r, c, txt in found_table:
                has_placeholder = '[' in txt and 'GIOI_TINH' in txt
                status = 'OK' if has_placeholder else 'HARDCODED'
                out.write(f"    [TABLE{t} R{r} C{c}] [{status}] {txt}\n")

out.close()
