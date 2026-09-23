import re
import docx
from pathlib import Path
import sys

sys.path.insert(0, r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")
from services.render_service import normalize_context

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

context = normalize_context(test_data)
tpl_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV")
placeholder_regex = re.compile(r"\{\{([^}]+)\}\}")

print("=== AUDIT OF ALL PLACEHOLDERS IN TEMPLATES VS CONTEXT ===")
for f in sorted(tpl_dir.glob("*.docx")):
    doc = docx.Document(f)
    found_tags = set()
    for p in doc.paragraphs:
        for m in placeholder_regex.finditer(p.text):
            found_tags.add(m.group(1).strip())
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs:
                    for m in placeholder_regex.finditer(p.text):
                        found_tags.add(m.group(1).strip())
                        
    print(f"\n--- {f.name} ---")
    for tag in sorted(list(found_tags)):
        val = context.get(tag)
        status = "OK" if val is not None and val != "" else "MISSING / EMPTY"
        print(f"  {tag:<30}: {status} (val={repr(val)})")
