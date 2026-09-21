import sys, zipfile, io, docx
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")
sys.path.insert(0, str(BASE_DIR))
from services.render_service import render_documents

def test_cn2tv_with_ddpl_change():
    mock_cn2tv = {
        "company": {
            "TEN_CONG_TY_VN": "CÔNG TY TNHH PHÁT TRIỂN CÔNG NGHỆ Á CHÂU",
            "MA_SO_THUE": "0109988776",
            "VON_DIEU_LE_SO": "2,000,000,000",
            "VON_DIEU_LE_CHU": "Hai tỷ đồng"
        },
        "ddpl_cu": {
            "HO_TEN": "NGUYỄN VĂN CŨ",
            "NGAY_SINH": "10/10/1975",
            "SO_CCCD": "001075001111",
            "GIOI_TINH": "Nam",
            "DIA_CHI": "123 Phố Huế, P. Hàng Bài, TP. Hà Nội"
        },
        "ddpl_moi": {
            "HO_TEN": "TRẦN VĂN MỚI",
            "NGAY_SINH": "20/12/1988",
            "SO_CCCD": "001088002222",
            "GIOI_TINH": "Nam",
            "DIA_CHI": "456 Đường Láng, P. Láng Thượng, TP. Hà Nội"
        },
        "tv_cu": [
            {"HO_TEN": "NGUYỄN VĂN CŨ", "SO_CCCD": "001075001111", "DIA_CHI": "123 Phố Huế", "VON_GOP": "1,200,000,000", "TY_LE": "60"},
            {"HO_TEN": "LÊ THỊ CŨ", "SO_CCCD": "001180003333", "DIA_CHI": "789 Giải Phóng", "VON_GOP": "800,000,000", "TY_LE": "40"}
        ],
        "tv_moi": [
            {"HO_TEN": "TRẦN VĂN MỚI", "NGAY_SINH": "20/12/1988", "SO_CCCD": "001088002222", "GIOI_TINH": "Nam", "DIA_CHI": "456 Đường Láng, P. Láng Thượng, TP. Hà Nội", "VON_GOP": "1,400,000,000", "TY_LE": "70"},
            {"HO_TEN": "PHẠM VĂN MỚI", "NGAY_SINH": "15/08/1992", "SO_CCCD": "001092004444", "GIOI_TINH": "Nam", "DIA_CHI": "101 Cầu Giấy, P. Dịch Vọng, TP. Hà Nội", "VON_GOP": "600,000,000", "TY_LE": "30"}
        ],
        "chuyen_nhuong": [
            {"ben_a": 0, "ben_b": 0, "von": "1,200,000,000", "gia_tri": "1,200,000,000", "ty_le": "60"},
            {"ben_a": 1, "ben_b": 0, "von": "200,000,000", "gia_tri": "200,000,000", "ty_le": "10"},
            {"ben_a": 1, "ben_b": 1, "von": "600,000,000", "gia_tri": "600,000,000", "ty_le": "30"}
        ]
    }

    payload = {"cn2tv_data": mock_cn2tv}
    zip_bytes = render_documents("Chuyển nhượng Công ty TNHH 2 TV", payload["cn2tv_data"], special_payload=payload)
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    
    # Check 3 contracts & 3 liquidations
    assert "06. Hợp đồng chuyển nhượng_a (NGUYỄN VĂN CŨ - TRẦN VĂN MỚI).docx" in z.namelist()
    assert "06. Hợp đồng chuyển nhượng_b (LÊ THỊ CŨ - TRẦN VĂN MỚI).docx" in z.namelist()
    assert "06. Hợp đồng chuyển nhượng_c (LÊ THỊ CŨ - PHẠM VĂN MỚI).docx" in z.namelist()
    assert "07. Biên bản thanh lý_a (NGUYỄN VĂN CŨ - TRẦN VĂN MỚI).docx" in z.namelist()
    assert "07. Biên bản thanh lý_b (LÊ THỊ CŨ - TRẦN VĂN MỚI).docx" in z.namelist()
    assert "07. Biên bản thanh lý_c (LÊ THỊ CŨ - PHẠM VĂN MỚI).docx" in z.namelist()
    
    # Check capital certificates
    assert "09a. Xác nhận góp vốn (TRẦN VĂN MỚI).docx" in z.namelist()
    assert "09b. Xác nhận góp vốn (PHẠM VĂN MỚI).docx" in z.namelist()
    
    # Check DDPL change docs are present
    assert "02. Thông báo thay đổi người đại diện theo pháp luật.docx" in z.namelist()
    assert "08. Quyết định.docx" in z.namelist()
    print("test_cn2tv_with_ddpl_change: SUCCESS")

def test_cn2tv_without_ddpl_change():
    mock_cn2tv = {
        "company": {
            "TEN_CONG_TY_VN": "CÔNG TY TNHH PHÁT TRIỂN CÔNG NGHỆ Á CHÂU",
            "MA_SO_THUE": "0109988776"
        },
        "ddpl_cu": {
            "HO_TEN": "NGUYỄN VĂN A",
            "SO_CCCD": "001080001111",
            "DIA_CHI": "123 Phố Huế, TP. Hà Nội"
        },
        "ddpl_moi": {
            "HO_TEN": "NGUYỄN VĂN A", # Không đổi ĐDPL
            "SO_CCCD": "001080001111",
            "DIA_CHI": "123 Phố Huế, TP. Hà Nội"
        },
        "tv_cu": [
            {"HO_TEN": "NGUYỄN VĂN A", "SO_CCCD": "001080001111", "DIA_CHI": "123 Phố Huế", "VON_GOP": "2,000,000,000", "TY_LE": "100"}
        ],
        "tv_moi": [
            {"HO_TEN": "NGUYỄN VĂN A", "SO_CCCD": "001080001111", "DIA_CHI": "123 Phố Huế", "VON_GOP": "1,000,000,000", "TY_LE": "50"},
            {"HO_TEN": "TRẦN THỊ B", "SO_CCCD": "001085002222", "DIA_CHI": "456 Giải Phóng", "VON_GOP": "1,000,000,000", "TY_LE": "50"}
        ],
        "chuyen_nhuong": [
            {"ben_a": 0, "ben_b": 1, "von": "1,000,000,000", "gia_tri": "1,000,000,000", "ty_le": "50"}
        ]
    }

    payload = {"cn2tv_data": mock_cn2tv, "ddpl_changed": False}
    zip_bytes = render_documents("Chuyển nhượng Công ty TNHH 2 TV", payload["cn2tv_data"], special_payload=payload)
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    
    # When DDPL not changed, 02 and 08 must NOT be generated
    assert "02. Thông báo thay đổi người đại diện theo pháp luật.docx" not in z.namelist()
    assert "08. Quyết định.docx" not in z.namelist()
    assert "03. Danh sách thành viên.docx" in z.namelist()
    assert "06. Hợp đồng chuyển nhượng_a (NGUYỄN VĂN A - TRẦN THỊ B).docx" in z.namelist()
    print("test_cn2tv_without_ddpl_change: SUCCESS")

if __name__ == "__main__":
    test_cn2tv_with_ddpl_change()
    test_cn2tv_without_ddpl_change()
    print("ALL CN2TV TESTS PASSED!")
