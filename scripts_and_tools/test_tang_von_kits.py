import sys, zipfile, io, docx
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")
sys.path.insert(0, str(BASE_DIR))
from services.render_service import render_documents

def test_tang_von_cp():
    raw_cp = {
        "ten_cong_ty_vn": "CÔNG TY CỔ PHẦN ĐẦU TƯ MINH ĐỨC",
        "ma_so_thue": "0109876543",
        "dia_chi_so_nha": "Số 88 Phố Huế",
        "dia_chi_xa_phuong": "Phường Hàng Bài",
        "dia_chi_tinh_thanh": "Thành phố Hà Nội",
        "von_cu_so": "10000000000",
        "von_dieu_le_so": "25000000000",
        "sdt_cong_ty": "02439887766",
        "email_cong_ty": "minhduc.corp@gmail.com",
        "ddpl": {
            "ho_ten": "TRẦN MINH ĐỨC",
            "so_cccd": "001085001234",
            "ngay_sinh": "15/05/1985",
            "gioi_tinh": "Nam"
        },
        "thanh_vien": [
            {"ho_ten": "TRẦN MINH ĐỨC", "von_gop": "15000000000", "ty_le": "60"},
            {"ho_ten": "NGUYỄN THỊ MAI", "von_gop": "6250000000", "ty_le": "25"},
            {"ho_ten": "HOÀNG VĂN LONG", "von_gop": "3750000000", "ty_le": "15"}
        ]
    }
    zip_bytes = render_documents("Tăng vốn công ty Cổ Phần", raw_cp)
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    assert "01. Thông báo thay đổi ĐKKD.docx" in z.namelist()
    assert "04. Biên bản họp.docx" in z.namelist()
    print("test_tang_von_cp: SUCCESS")

def test_tang_von_2tv():
    raw_2tv = {
        "ten_cong_ty_vn": "CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ VIỆT NHẬT",
        "ma_so_thue": "0315678910",
        "dia_chi_so_nha": "Tầng 5, Tòa nhà Bitexco, Số 2 Hải Triều",
        "dia_chi_xa_phuong": "Phường Bến Nghé",
        "dia_chi_tinh_thanh": "Thành phố Hồ Chí Minh",
        "von_cu_so": "1000000000",
        "von_dieu_le_so": "3000000000",
        "ddpl": {
            "ho_ten": "NGUYỄN VĂN A",
            "so_cccd": "001080123456",
            "ngay_sinh": "01/01/1980",
            "gioi_tinh": "Nam",
            "dia_chi_day_du": "123 Đường Số 1, P. Bến Nghé, TP.HCM"
        },
        "thanh_vien": [
            {"ho_ten": "NGUYỄN VĂN A", "ngay_sinh": "01/01/1980", "gioi_tinh": "Nam", "so_cccd": "001080123456", "dia_chi_day_du": "123 Đường Số 1, P. Bến Nghé, TP.HCM", "von_gop": "1500000000", "ty_le": "50"},
            {"ho_ten": "TRẦN THỊ B", "ngay_sinh": "02/02/1985", "gioi_tinh": "Nữ", "so_cccd": "001185123456", "dia_chi_day_du": "456 Đường Số 2, P. Đa Kao, TP.HCM", "von_gop": "900000000", "ty_le": "30"},
            {"ho_ten": "LÊ VĂN C", "ngay_sinh": "03/03/1990", "gioi_tinh": "Nam", "so_cccd": "001090123456", "dia_chi_day_du": "789 Đường Số 3, P. Tân Định, TP.HCM", "von_gop": "600000000", "ty_le": "20"}
        ]
    }
    zip_bytes = render_documents("Tăng vốn công ty TNHH 2 TV", raw_2tv)
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    assert "06. Danh sách thành viên.docx" in z.namelist()
    assert "07. Giấy chứng nhận góp vốn_a (NGUYỄN VĂN A).docx" in z.namelist()
    assert "07. Giấy chứng nhận góp vốn_b (TRẦN THỊ B).docx" in z.namelist()
    assert "07. Giấy chứng nhận góp vốn_c (LÊ VĂN C).docx" in z.namelist()
    print("test_tang_von_2tv: SUCCESS")

if __name__ == "__main__":
    test_tang_von_cp()
    test_tang_von_2tv()
    print("ALL TĂNG VỐN TESTS PASSED!")
