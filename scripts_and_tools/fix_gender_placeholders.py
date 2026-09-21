import os
from docx import Document

def update_docx(filepath):
    doc = Document(filepath)
    modified = False
    
    fname = os.path.basename(filepath)
    
    for p in doc.paragraphs:
        if 'Giới tính: Nam' in p.text:
            p.text = p.text.replace('Giới tính: Nam', 'Giới tính: [DDPL_MOI_GIOI_TINH]')
            modified = True
        elif 'Giới tính: Nữ' in p.text:
            p.text = p.text.replace('Giới tính: Nữ', 'Giới tính: [TV_MOI_1_GIOI_TINH]')
            modified = True

    for table in doc.tables:
        for r_idx, row in enumerate(table.rows):
            if r_idx > 0: # skip header
                for cell in row.cells:
                    for p in cell.paragraphs:
                        if p.text.strip() == 'Giới tính':
                            if "Danh sách chủ sở hữu" in fname:
                                if r_idx == 1:
                                    p.text = '[CSHHL_1_GIOI_TINH]'
                                    modified = True
                                elif r_idx == 2:
                                    p.text = '[CSHHL_2_GIOI_TINH]'
                                    modified = True
                            else:
                                if r_idx == 1:
                                    p.text = '[TV_MOI_1_GIOI_TINH]'
                                    modified = True
                                elif r_idx == 2:
                                    p.text = '[TV_MOI_2_GIOI_TINH]'
                                    modified = True
    
    if modified:
        doc.save(filepath)
        print(f"Updated")

base_dir = 'Mẫu Chuyển nhượng Công ty TNHH 2 TV'
for f in os.scandir(base_dir):
    if f.name.endswith('.docx') and not f.name.startswith('~'):
        update_docx(f.path)
