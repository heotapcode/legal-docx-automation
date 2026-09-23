import sys
import io
import zipfile
import re
import docx
from pathlib import Path

sys.path.insert(0, r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")
from services.render_service import render_documents

test_data_3m = {
    "ten_cong_ty_vn": "CÔNG TY TNHH ABC TECH",
    "ma_so_thue": "0109998888",
    "dia_chi_so_nha": "Tầng 5 tòa nhà Landmark",
    "dia_chi_xa_phuong": "Phường Mễ Trì",
    "dia_chi_quan_huyen": "Quận Nam Từ Liêm",
    "dia_chi_tinh_thanh": "Thành phố Hà Nội",
    "von_cu_so": "2.000.000.000",
    "von_cu_chu": "Hai tỷ đồng",
    "von_dieu_le_so": "5.000.000.000",
    "von_dieu_le_chu": "Năm tỷ đồng",
    "ddpl_ho_ten": "NGUYỄN VĂN AN",
    "ddpl_gioi_tinh": "Nam",
    "ddpl_ngay_sinh": "01/01/1980",
    "ddpl_so_cccd": "001080001111",
    "ddpl_dia_chi_day_du": "Số 10 phố Hoa Hồng, Phường Mễ Trì, Hà Nội",
    "thanh_vien": [
        {
            "ho_ten": "NGUYỄN VĂN AN",
            "gioi_tinh": "Nam",
            "ngay_sinh": "01/01/1980",
            "so_cccd": "001080001111",
            "dia_chi_day_du": "Số 10 phố Hoa Hồng, Phường Mễ Trì, Hà Nội",
            "von_gop": "2.500.000.000",
            "ty_le": "50"
        },
        {
            "ho_ten": "TRẦN THỊ BÌNH",
            "gioi_tinh": "Nữ",
            "ngay_sinh": "02/02/1985",
            "so_cccd": "001185002222",
            "dia_chi_day_du": "Số 20 phố Hoa Mai, Phường Mễ Trì, Hà Nội",
            "von_gop": "1.500.000.000",
            "ty_le": "30"
        },
        {
            "ho_ten": "LÊ VĂN CƯỜNG",
            "gioi_tinh": "Nam",
            "ngay_sinh": "03/03/1990",
            "so_cccd": "001090003333",
            "dia_chi_day_du": "Số 30 phố Hoa Lan, Phường Mễ Trì, Hà Nội",
            "von_gop": "1.000.000.000",
            "ty_le": "20"
        }
    ]
}

print("Testing 3 members for Tăng vốn 2TV...")
zip_bytes = render_documents("Tăng vốn công ty TNHH 2 TV", test_data_3m)
zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
names = zf.namelist()
print(f"Files in zip ({len(names)}):")
for n in names:
    print(f"  {n}")

out_3m = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\scripts_and_tools\output_test_3m")
out_3m.mkdir(parents=True, exist_ok=True)
zf.extractall(out_3m)

doc_bbh = docx.Document(out_3m / "02. Biên bản họp.docx")
print("\n--- 02. Biên bản họp: Thành phần dự họp ---")
for p in doc_bbh.paragraphs[11:22]:
    if p.text.strip(): print(f"  {p.text}")

print("\n--- 02. Biên bản họp: Quy ước biểu quyết ---")
for p in doc_bbh.paragraphs:
    if "quy ước" in p.text.lower():
        print(f"  {p.text}")

doc_dstv = docx.Document(out_3m / "06. Danh sách thành viên.docx")
print(f"\n--- 06. Danh sách thành viên: Rows count = {len(doc_dstv.tables[0].rows)} ---")
for r in doc_dstv.tables[0].rows[3:]:
    print(f"  {[c.text.strip().replace(chr(10), ' ') for c in r.cells[:12]]}")
