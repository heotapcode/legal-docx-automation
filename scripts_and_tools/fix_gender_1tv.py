import os
from docx import Document
import re

def update_docx(filepath):
    doc = Document(filepath)
    modified = False
    fname = os.path.basename(filepath)
    
    paragraphs = doc.paragraphs
    for i, p in enumerate(paragraphs):
        if 'Giới tính: Nam' in p.text or 'Giới  tính: Nam' in p.text:
            text = p.text
            prev_text = paragraphs[max(0, i-1)].text if i > 0 else ""
            if '[DDPL_NGAY_SINH]' in text or '[DDPL_NGAY_SINH]' in prev_text:
                p.text = re.sub(r'Giới\s+tính:\s*Nam', 'Giới tính: [DDPL_GIOI_TINH]', p.text)
                modified = True
            elif '[DDPL_CU_NGAY_SINH]' in text or '[DDPL_CU_NGAY_SINH]' in prev_text:
                p.text = re.sub(r'Giới\s+tính:\s*Nam', 'Giới tính: [DDPL_CU_GIOI_TINH]', p.text)
                modified = True
            elif '001089021350' in text or '001089021350' in prev_text:
                p.text = re.sub(r'Giới\s+tính:\s*Nam', 'Giới tính: [NGUOI_DUOC_UY_QUYEN_GIOI_TINH]', p.text)
                modified = True
            else:
                p.text = re.sub(r'Giới\s+tính:\s*Nam', 'Giới tính: [DDPL_GIOI_TINH]', p.text)
                modified = True

    for table in doc.tables:
        for r_idx, row in enumerate(table.rows):
            if r_idx > 0:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        if p.text.strip() == 'Giới tính':
                            if "Danh sách chủ sở hữu" in fname:
                                p.text = '[CSHHL_GIOI_TINH]'
                                modified = True
                            
    if modified:
        doc.save(filepath)

base_dir = 'Mẫu Chuyển nhượng công ty TNHH 1 TV'
for f in os.scandir(base_dir):
    if f.name.endswith('.docx') and not f.name.startswith('~'):
        update_docx(f.path)
