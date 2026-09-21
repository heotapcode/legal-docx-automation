import sys, zipfile, io, docx
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")
sys.path.insert(0, str(BASE_DIR))
from services.render_service import render_documents

def test_giai_the_2tv():
    raw_2tv = {
        "ten_cong_ty_vn": "CÔNG TY TNHH MINH PHÁT",
        "ma_so_thue": "0109112233",
        "dia_chi_so_nha": "Số 12 Phố Huế",
        "dia_chi_xa_phuong": "Phường Hàng Bài",
        "dia_chi_tinh_thanh": "Thành phố Hà Nội",
        "ddpl": {
            "ho_ten": "NGUYỄN VĂN MINH",
            "so_cccd": "001080001234",
            "ngay_sinh": "01/01/1980",
            "gioi_tinh": "Nam",
            "dia_chi_day_du": "Số 12 Phố Huế, P. Hàng Bài, Hà Nội"
        },
        "thanh_vien": [
            {"ho_ten": "NGUYỄN VĂN MINH", "gioi_tinh": "Nam", "von_gop": "1200000000", "ty_le": "60"},
            {"ho_ten": "TRẦN VĂN PHÁT", "gioi_tinh": "Nam", "von_gop": "800000000", "ty_le": "40"}
        ]
    }
    zip_bytes = render_documents("Giải thể công ty TNHH 2 TV", raw_2tv)
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    assert "01. Quyết định giải thể.docx" in z.namelist()
    assert "02. Biên bản họp.docx" in z.namelist()
    
    # Check 02 paragraphs
    doc_02 = docx.Document(io.BytesIO(z.read("02. Biên bản họp.docx")))
    txt = "\n".join([p.text for p in doc_02.paragraphs])
    assert "NGUYỄN VĂN MINH" in txt
    assert "TRẦN VĂN PHÁT" in txt
    print("test_giai_the_2tv: SUCCESS")

def test_giai_the_cp():
    raw_cp = {
        "ten_cong_ty_vn": "CÔNG TY CỔ PHẦN ĐẠI NAM",
        "ma_so_thue": "0108776655",
        "dia_chi_so_nha": "Số 99 Bà Triệu",
        "dia_chi_xa_phuong": "Phường Hàng Bài",
        "dia_chi_tinh_thanh": "Thành phố Hà Nội",
        "ddpl": {
            "ho_ten": "NGUYỄN ĐẠI NAM",
            "so_cccd": "001082005678",
            "ngay_sinh": "12/12/1982",
            "gioi_tinh": "Nam"
        },
        "thanh_vien": [
            {"ho_ten": "NGUYỄN ĐẠI NAM", "von_gop": "5000000000", "ty_le": "50"},
            {"ho_ten": "LÊ THỊ HỒNG", "von_gop": "3000000000", "ty_le": "30"},
            {"ho_ten": "VŨ VĂN HÙNG", "von_gop": "2000000000", "ty_le": "20"}
        ]
    }
    zip_bytes = render_documents("Giải thể công ty Cổ Phần", raw_cp)
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    assert "01. Biên bản họp + Quyết định.docx" in z.namelist()
    assert "03. Thông báo giải thể.docx" in z.namelist()
    
    doc_01 = docx.Document(io.BytesIO(z.read("01. Biên bản họp + Quyết định.docx")))
    t2 = doc_01.tables[1]
    # Check rows in table 2
    shareholder_names = [r.cells[1].text for r in t2.rows[1:-1]]
    assert "NGUYỄN ĐẠI NAM" in shareholder_names
    assert "LÊ THỊ HỒNG" in shareholder_names
    assert "VŨ VĂN HÙNG" in shareholder_names
    print("test_giai_the_cp: SUCCESS")

if __name__ == "__main__":
    test_giai_the_2tv()
    test_giai_the_cp()
    print("ALL GIẢI THỂ TESTS PASSED!")
