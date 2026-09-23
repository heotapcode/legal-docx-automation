import sys
import io
import zipfile
import docx
from pathlib import Path

sys.path.insert(0, r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")
from services.render_service import render_documents

test_female_ddpl = {
    "ten_cong_ty_vn": "CÔNG TY TNHH PHỤ NỮ Á ĐÔNG",
    "ma_so_thue": "0107779999",
    "dia_chi_so_nha": "Số 88 phố Huế",
    "dia_chi_xa_phuong": "Phường Hàng Bài",
    "dia_chi_tinh_thanh": "Hà Nội",
    "von_cu_so": "1.000.000.000",
    "von_dieu_le_so": "2.000.000.000",
    "ddpl_ho_ten": "NGUYỄN THỊ MAI",
    "ddpl_gioi_tinh": "Nữ",
    # Intentionally omit ddpl_ngay_sinh to test fallback from member list!
    "ddpl_so_cccd": "001188009999",
    "thanh_vien": [
        {
            "ho_ten": "NGUYỄN THỊ MAI",
            "gioi_tinh": "Nữ",
            "ngay_sinh": "12/12/1988",
            "so_cccd": "001188009999",
            "dia_chi_day_du": "Số 88 phố Huế, Hà Nội",
            "von_gop": "1.400.000.000",
            "ty_le": "70"
        },
        {
            "ho_ten": "LÊ VĂN LONG",
            "gioi_tinh": "Nam",
            "ngay_sinh": "01/01/1992",
            "so_cccd": "001092008888",
            "dia_chi_day_du": "Số 90 phố Huế, Hà Nội",
            "von_gop": "600.000.000",
            "ty_le": "30"
        }
    ]
}

zip_bytes = render_documents("Tăng vốn công ty TNHH 2 TV", test_female_ddpl)
zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
out_f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\scripts_and_tools\output_test_female")
out_f.mkdir(parents=True, exist_ok=True)
zf.extractall(out_f)

doc_uq = docx.Document(out_f / "04. Giấy ủy quyền.docx")
print("=== 04. Giấy ủy quyền.docx (Female DDPL with fallback ngày sinh) ===")
for p in doc_uq.paragraphs[7:14]:
    print(f"  {p.text}")
