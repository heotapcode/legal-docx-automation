import sys, zipfile, io, docx
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")
sys.path.insert(0, str(BASE_DIR))
from services.render_service import render_documents

def test_tlm_2tv():
    raw_2tv = {
        "ten_cong_ty_vn": "CÔNG TY TNHH ABC TECHNOLOGY",
        "ten_cong_ty_en": "ABC TECHNOLOGY CO., LTD",
        "ten_cong_ty_viet_tat": "ABC TECH",
        "dia_chi_so_nha": "123 Đường Số 1",
        "dia_chi_xa_phuong": "Phường Bến Nghé",
        "dia_chi_tinh_thanh": "Thành phố Hồ Chí Minh",
        "von_dieu_le_so": "1000000000",
        "sdt_cong_ty": "0901234567",
        "email_cong_ty": "contact@abctech.vn",
        "ddpl": {
            "ho_ten": "NGUYỄN VĂN A",
            "so_cccd": "001080123456",
            "ngay_sinh": "01/01/1980",
            "gioi_tinh": "Nam",
            "dia_chi_so_nha": "123 Đường Số 1",
            "dia_chi_xa_phuong": "Phường Bến Nghé",
            "dia_chi_tinh_thanh": "Thành phố Hồ Chí Minh"
        },
        "thanh_vien": [
            {"ho_ten": "NGUYỄN VĂN A", "ngay_sinh": "01/01/1980", "gioi_tinh": "Nam", "so_cccd": "001080123456", "dia_chi_day_du": "123 Đường Số 1, P. Bến Nghé, TP.HCM", "von_gop": "500000000", "ty_le": "50"},
            {"ho_ten": "TRẦN THỊ B", "ngay_sinh": "02/02/1985", "gioi_tinh": "Nữ", "so_cccd": "001185123456", "dia_chi_day_du": "456 Đường Số 2, P. Đa Kao, TP.HCM", "von_gop": "300000000", "ty_le": "30"},
            {"ho_ten": "LÊ VĂN C", "ngay_sinh": "03/03/1990", "gioi_tinh": "Nam", "so_cccd": "001090123456", "dia_chi_day_du": "789 Đường Số 3, P. Tân Định, TP.HCM", "von_gop": "200000000", "ty_le": "20"}
        ]
    }
    zip_bytes = render_documents("Thành lập mới công ty TNHH 2 TV", raw_2tv)
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    assert "02. Điều lệ.docx" in z.namelist()
    assert "03. Danh sách thành viên.docx" in z.namelist()
    print("test_tlm_2tv: SUCCESS")

def test_tlm_cp():
    raw_cp = {
        "ten_cong_ty_vn": "CÔNG TY CỔ PHẦN ĐẦU TƯ XYZ",
        "ten_cong_ty_en": "XYZ INVESTMENT JSC",
        "ten_cong_ty_viet_tat": "XYZ INVEST",
        "dia_chi_so_nha": "88 Đại lộ Lê Lợi",
        "dia_chi_xa_phuong": "Phường Bến Nghé",
        "dia_chi_quan_huyen": "Quận 1",
        "dia_chi_tinh_thanh": "Thành phố Hồ Chí Minh",
        "von_dieu_le_so": "10000000000",
        "sdt_cong_ty": "0912345678",
        "email_cong_ty": "contact@xyzinvest.vn",
        "ddpl": {
            "ho_ten": "NGUYỄN VĂN A",
            "so_cccd": "001080123456",
            "ngay_sinh": "01/01/1980",
            "gioi_tinh": "Nam",
            "dia_chi_so_nha": "88 Đại lộ Lê Lợi",
            "dia_chi_xa_phuong": "Phường Bến Nghé",
            "dia_chi_quan_huyen": "Quận 1",
            "dia_chi_tinh_thanh": "Thành phố Hồ Chí Minh"
        },
        "thanh_vien": [
            {"ho_ten": "NGUYỄN VĂN A", "ngay_sinh": "01/01/1980", "gioi_tinh": "Nam", "so_cccd": "001080123456", "dia_chi_day_du": "88 Lê Lợi, Q.1, TP.HCM", "von_gop": "4000000000", "ty_le": "40"},
            {"ho_ten": "TRẦN THỊ B", "ngay_sinh": "02/02/1985", "gioi_tinh": "Nữ", "so_cccd": "001185123456", "dia_chi_day_du": "456 Hai Bà Trưng, Q.3, TP.HCM", "von_gop": "3000000000", "ty_le": "30"},
            {"ho_ten": "LÊ VĂN C", "ngay_sinh": "03/03/1990", "gioi_tinh": "Nam", "so_cccd": "001090123456", "dia_chi_day_du": "789 Nguyễn Trãi, Q.5, TP.HCM", "von_gop": "2000000000", "ty_le": "20"},
            {"ho_ten": "PHẠM VĂN D", "ngay_sinh": "04/04/1992", "gioi_tinh": "Nam", "so_cccd": "001092123456", "dia_chi_day_du": "101 Nguyễn Thị Thập, Q.7, TP.HCM", "von_gop": "1000000000", "ty_le": "10"}
        ]
    }
    zip_bytes = render_documents("Thành lập mới công ty Cổ Phần", raw_cp)
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    assert "02. Điều lệ.docx" in z.namelist()
    assert "03. Danh sách cổ đông sáng lập.docx" in z.namelist()
    print("test_tlm_cp: SUCCESS")

if __name__ == "__main__":
    test_tlm_2tv()
    test_tlm_cp()
    print("ALL TESTS PASSED!")
