import os
import sys
import io
import zipfile
import re
import docx
from pathlib import Path

sys.path.insert(0, r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")
from services.render_service import render_documents

test_data = {
    "ten_cong_ty_vn": "CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ AN BÌNH",
    "ma_so_thue": "0109876543",
    "dia_chi_so_nha": "Số 123 đường Giải Phóng",
    "dia_chi_xa_phuong": "Phường Đồng Tâm",
    "dia_chi_quan_huyen": "Quận Hai Bà Trưng",
    "dia_chi_tinh_thanh": "Thành phố Hà Nội",
    "von_cu_so": "1.000.000.000",
    "von_cu_chu": "Một tỷ đồng",
    "von_dieu_le_so": "3.000.000.000",
    "von_dieu_le_chu": "Ba tỷ đồng",
    "ddpl_ho_ten": "NGUYỄN VĂN AN",
    "ddpl_gioi_tinh": "Nam",
    "ddpl_ngay_sinh": "15/05/1985",
    "ddpl_so_cccd": "001085001234",
    "ddpl_dia_chi_so_nha": "Số 10 ngõ 5 phố Vọng",
    "ddpl_dia_chi_xa_phuong": "Phường Đồng Tâm",
    "ddpl_dia_chi_tinh_thanh": "Thành phố Hà Nội",
    "thanh_vien": [
        {
            "ho_ten": "NGUYỄN VĂN AN",
            "gioi_tinh": "Nam",
            "ngay_sinh": "15/05/1985",
            "so_cccd": "001085001234",
            "dia_chi_so_nha": "Số 10 ngõ 5 phố Vọng",
            "dia_chi_xa_phuong": "Phường Đồng Tâm",
            "dia_chi_tinh_thanh": "Thành phố Hà Nội",
            "von_gop": "1.800.000.000",
            "ty_le": "60"
        },
        {
            "ho_ten": "TRẦN THỊ BÌNH",
            "gioi_tinh": "Nữ",
            "ngay_sinh": "20/10/1990",
            "so_cccd": "001190005678",
            "dia_chi_so_nha": "Số 45 phố Lê Thanh Nghị",
            "dia_chi_xa_phuong": "Phường Bách Khoa",
            "dia_chi_tinh_thanh": "Thành phố Hà Nội",
            "von_gop": "1.200.000.000",
            "ty_le": "40"
        }
    ]
}

print("Running render_documents for 'Tăng vốn công ty TNHH 2 TV'...")
zip_bytes = render_documents("Tăng vốn công ty TNHH 2 TV", test_data)

zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
file_names = zf.namelist()
print(f"\nExtracted {len(file_names)} files from ZIP:")
for fn in file_names:
    print(f"  - {fn}")

placeholder_regex = re.compile(r"\{\{([^}]+)\}\}|<<([^>]+)>>|\[\[([^\]]+)\]\]|«([^»]+)»")

out_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\scripts_and_tools\output_test_tang_von")
out_dir.mkdir(parents=True, exist_ok=True)
zf.extractall(out_dir)

print("\n=== CHECKING FOR UNRESOLVED PLACEHOLDERS IN GENERATED DOCX ===")
for doc_path in sorted(out_dir.glob("*.docx")):
    doc = docx.Document(doc_path)
    unresolved = []
    
    for p_idx, p in enumerate(doc.paragraphs):
        for m in placeholder_regex.finditer(p.text):
            unresolved.append((f"P{p_idx+1}", m.group(0)))
            
    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                for p in cell.paragraphs:
                    for m in placeholder_regex.finditer(p.text):
                        unresolved.append((f"T{t_idx+1}_R{r_idx+1}_C{c_idx+1}", m.group(0)))
                        
    if unresolved:
        print(f"\n[FAIL] File: {doc_path.name}")
        for loc, tag in unresolved:
            print(f"   {loc}: {tag}")
    else:
        print(f"[OK] File: {doc_path.name} - No unresolved placeholders!")
