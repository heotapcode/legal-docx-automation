import docx
import os
import re
from pathlib import Path

BASE_DIR = Path(r'C:\Users\Pc\Desktop\Hermes\Điền thông tin file word')
TPL_DIRS = [
    BASE_DIR / 'webapp_v2' / 'templates' / 'Chuyển đổi loại hình 1TV sang 2 TV',
    BASE_DIR / 'Mẫu Chuyển đổi loại hình 1TV sang 2 TV'
]

def replace_in_doc(doc, replacements):
    # Paragraphs
    for p in doc.paragraphs:
        for old, new in replacements.items():
            if old in p.text:
                p.text = p.text.replace(old, new)
                
    # Tables
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for old, new in replacements.items():
                    if old in cell.text:
                        cell.text = cell.text.replace(old, new)

for target_dir in TPL_DIRS:
    if not target_dir.exists():
        continue
    print(f"\n--- Standardizing templates in: {target_dir} ---")
    
    # 1. 01. Quyết định.docx
    qd_path = target_dir / '01. Quyết định.docx'
    if qd_path.exists():
        doc_qd = docx.Document(str(qd_path))
        
        # Table 2: Co cau von cu (CSH cu)
        if len(doc_qd.tables) > 1 and len(doc_qd.tables[1].rows) >= 2:
            r = doc_qd.tables[1].rows[1]
            r.cells[1].text = "{{ csh_ho_ten }}"
            r.cells[2].text = "{{ csh_dia_chi_so_nha }}, {{ csh_dia_chi_xa_phuong }}, {{ csh_dia_chi_tinh_thanh }}"
            r.cells[3].text = "{{ von_cu_so }}"
            r.cells[4].text = "100"
            r.cells[5].text = "{{ csh_so_cccd }}"
            
        # Table 3: Co cau von moi (Row 2 = TV1, Row 3 = TV2)
        if len(doc_qd.tables) > 2 and len(doc_qd.tables[2].rows) >= 2:
            r = doc_qd.tables[2].rows[1]
            r.cells[1].text = "{{ tv1_ho_ten }}"
            r.cells[2].text = "{{ tv1_dia_chi_so_nha }}, {{ tv1_dia_chi_xa_phuong }}, {{ tv1_dia_chi_tinh_thanh }}"
            r.cells[3].text = "{{ tv1_von_so }}"
            r.cells[4].text = "{{ tv1_ty_le }}"
            r.cells[5].text = "{{ tv1_so_cccd }}"
            
        # Table 7: Danh sach thanh vien moi (Row 2 = TV1, Row 3 = TV2)
        if len(doc_qd.tables) > 6 and len(doc_qd.tables[6].rows) >= 2:
            r = doc_qd.tables[6].rows[1]
            r.cells[1].text = "{{ tv1_ho_ten }}"
            r.cells[2].text = "{{ tv1_dia_chi_so_nha }}, {{ tv1_dia_chi_xa_phuong }}, {{ tv1_dia_chi_tinh_thanh }}"
            r.cells[3].text = "{{ tv1_von_so }}"
            r.cells[4].text = "{{ tv1_ty_le }}"
            r.cells[5].text = "{{ tv1_so_cccd }}"
            
        # Table 8: Chu ky CSH cu
        if len(doc_qd.tables) > 7 and len(doc_qd.tables[7].rows) >= 1:
            c = doc_qd.tables[7].rows[0].cells[1]
            c.text = "CHỦ SỞ HỮU CÔNG TY\n\n\n\n\n\n{{ csh_ho_ten }}"
            
        # Paragraph replacements in QD
        repl_qd = {
            'từ {{ "ông" if ddpl_gioi_tinh == "Nam" else "bà" }} {{ ddpl_ho_ten }}': 'từ {{ "ông" if csh_gioi_tinh == "Nam" else "bà" }} {{ csh_ho_ten }}'
        }
        replace_in_doc(doc_qd, repl_qd)
        doc_qd.save(str(qd_path))
        print(" -> 01. Quyết định.docx standardized successfully.")
        
    # 2. 02. Điều lệ.docx
    dl_path = target_dir / '02. Điều lệ.docx'
    if dl_path.exists():
        doc_dl = docx.Document(str(dl_path))
        
        # P34 to P42: Thanh vien thu nhat (tv1)
        # P43 to P49: Thanh vien thu hai (tv2)
        for i in range(33, min(len(doc_dl.paragraphs), 50)):
            p = doc_dl.paragraphs[i]
            if i < 42: # Section TV1
                p.text = p.text.replace('{{ tv2_', '{{ tv1_')
                p.text = p.text.replace('{{ tv1_von_cu_so }}', '{{ tv1_von_so }}')
            elif i >= 43: # Section TV2
                p.text = p.text.replace('{{ ddpl_', '{{ tv2_')
                p.text = p.text.replace('{{ tv2_von_cu_so }}', '{{ tv2_von_cu_so }}')
                
        # Table 3: Signatures in Dieu Le
        if len(doc_dl.tables) >= 3:
            t3 = doc_dl.tables[2]
            if len(t3.rows) >= 1 and len(t3.rows[0].cells) >= 2:
                t3.rows[0].cells[0].text = "{{ tv1_ho_ten }}"
                t3.rows[0].cells[1].text = "{{ tv2_ho_ten }}"
                
        doc_dl.save(str(dl_path))
        print(" -> 02. Điều lệ.docx standardized successfully.")

print("\nStandardization complete!")
