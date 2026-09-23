import docx
from pathlib import Path

tpl_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV")

# 1. Update 01. Thông báo thay đổi ĐKKD.docx
f1 = tpl_dir / "01. Thông báo thay đổi ĐKKD.docx"
doc1 = docx.Document(f1)
updated1 = False
for p in doc1.paragraphs:
    if "{{ dia_chi_so_nha }}, {{ dia_chi_xa_phuong }}, {{ dia_chi_quan_huyen }}, {{ dia_chi_tinh_thanh }}" in p.text:
        for r in p.runs:
            if "{{ dia_chi_so_nha }}, {{ dia_chi_xa_phuong }}, {{ dia_chi_quan_huyen }}, {{ dia_chi_tinh_thanh }}" in r.text:
                r.text = r.text.replace("{{ dia_chi_so_nha }}, {{ dia_chi_xa_phuong }}, {{ dia_chi_quan_huyen }}, {{ dia_chi_tinh_thanh }}", "{{ dia_chi_day_du }}")
                updated1 = True
if updated1:
    doc1.save(f1)
    print(f"Updated 01. Thông báo thay đổi ĐKKD.docx: {updated1}")
else:
    print("Warning: 01. Thông báo placeholder not found in runs, checking full paragraph replacement...")
    for p in doc1.paragraphs:
        if "Địa chỉ trụ sở chính:" in p.text:
            p.text = "Địa chỉ trụ sở chính: {{ dia_chi_day_du }}"
            doc1.save(f1)
            print("Replaced P text in 01. Thông báo")
            break

# 2. Update 02. Biên bản họp.docx
f2 = tpl_dir / "02. Biên bản họp.docx"
doc2 = docx.Document(f2)
updated2 = False
for p in doc2.paragraphs:
    if "{{ dia_chi_so_nha }}, {{ dia_chi_xa_phuong }}, {{ dia_chi_quan_huyen }}, {{ dia_chi_tinh_thanh }}" in p.text:
        for r in p.runs:
            if "{{ dia_chi_so_nha }}, {{ dia_chi_xa_phuong }}, {{ dia_chi_quan_huyen }}, {{ dia_chi_tinh_thanh }}" in r.text:
                r.text = r.text.replace("{{ dia_chi_so_nha }}, {{ dia_chi_xa_phuong }}, {{ dia_chi_quan_huyen }}, {{ dia_chi_tinh_thanh }}", "{{ dia_chi_day_du }}")
                updated2 = True
if updated2:
    doc2.save(f2)
    print(f"Updated 02. Biên bản họp.docx: {updated2}")
else:
    print("Warning: 02. Biên bản họp placeholder not found in runs, checking full paragraph replacement...")
    for p in doc2.paragraphs:
        if "Trụ sở chính công ty tại" in p.text:
            p.text = "2.Địa điểm: Trụ sở chính công ty tại \t{{ dia_chi_day_du }}"
            doc2.save(f2)
            print("Replaced P text in 02. Biên bản họp")
            break
