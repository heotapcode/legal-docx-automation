"""Hồi quy: Biên bản họp HĐTV phải lấy thành viên, vốn góp và số phiếu từ dữ liệu nhập,
không được còn dữ liệu viết cứng của khách hàng cũ."""
import pytest

from conftest import read_zip

MEMBERS = [
    {"ho_ten": "Trần Văn An", "gioi_tinh": "Nam", "ngay_sinh": "01/02/1980", "so_cccd": "001080000111",
     "von_gop": "600000000", "ty_le": "60", "so_gcn": "01/2024/GCN", "ngay_gcn": "10/03/2024"},
    {"ho_ten": "Lê Thị Bình", "gioi_tinh": "Nữ", "ngay_sinh": "05/06/1985", "so_cccd": "001185000222",
     "von_gop": "300000000", "ty_le": "30", "so_gcn": "02/2024/GCN", "ngay_gcn": "10/03/2024"},
    {"ho_ten": "Phạm Văn Cường", "gioi_tinh": "Nam", "ngay_sinh": "09/09/1990", "so_cccd": "001090000333",
     "von_gop": "100000000", "ty_le": "10", "so_gcn": "03/2024/GCN", "ngay_gcn": "12/04/2024"},
]
DDPL = {"ddpl_ho_ten": "Trần Văn An", "ddpl_so_cccd": "001080000111", "ddpl_ngay_sinh": "01/02/1980"}

# Dữ liệu của khách hàng cũ từng bị viết cứng trong mẫu
LEAKED = ["NGUYỄN NHƯ HÙNG", "LƯU ĐỨC KIÊN", "TRẦN ĐĂNG HÀO", "001090014685", "001090017798",
          "017094000488", "Logistics CMC", "22 tháng 10 năm 2026", "3.000 phiếu", "2.000 phiếu",
          "5000 phiếu", "01/2025/GCN cấp ngày 30/09/2025"]


def generate(client, name, extra):
    data = {"ten_cong_ty_vn": "CÔNG TY TNHH KIỂM THỬ XYZ", "ma_so_thue": "0109999999",
            **DDPL, **extra, "thanh_vien": [dict(m) for m in MEMBERS]}
    r = client.post("/api/documents/generate", json={"template_name": name, "data": data})
    assert r.status_code == 200, r.text
    files = read_zip(r.content)
    assert "_CANH_BAO_LOI_HO_SO.txt" not in files, files.get("_CANH_BAO_LOI_HO_SO.txt")
    return files


def bbh(files):
    return next(v for k, v in files.items() if "Biên bản họp" in k)


@pytest.mark.parametrize("name, extra", [
    ("Thay đổi địa chỉ và thuế TNHH 2 TV", {"dia_chi_cu": "Số 1 Phố A", "dia_chi_moi": "Số 2 Phố B",
                                            "ktt_ho_ten": "Đỗ Thị Kế", "ngay_lap": "03/11/2026"}),
    ("Giải thể công ty TNHH 2 TV", {"dia_chi_so_nha": "Số 5", "dia_chi_xa_phuong": "Phường Láng",
                                    "dia_chi_tinh_thanh": "Thành phố Hà Nội"}),
])
def test_no_leaked_hardcoded_data(client, name, extra):
    all_text = "\n".join(generate(client, name, extra).values())
    leaks = [s for s in LEAKED if s in all_text]
    assert not leaks, f"Còn dữ liệu viết cứng: {leaks}"


def test_thay_doi_dia_chi_bbh_uses_members(client):
    text = bbh(generate(client, "Thay đổi địa chỉ và thuế TNHH 2 TV", {
        "dia_chi_cu": "Số 1 Phố A", "dia_chi_moi": "Số 2 Phố B", "ktt_ho_ten": "Đỗ Thị Kế", "ngay_lap": "03/11/2026"}))
    assert "1. Ông TRẦN VĂN AN — Sinh ngày: 01/02/1980 — CCCD số: 001080000111" in text
    assert "2. Bà LÊ THỊ BÌNH" in text
    assert "3. Ông PHẠM VĂN CƯỜNG" in text
    assert "Tổng số thành viên dự họp: 03/03 thành viên" in text
    assert "ngày 03 tháng 11 năm 2026, tại trụ sở chính CÔNG TY TNHH KIỂM THỬ XYZ" in text
    assert "Hà Nội, ngày 03 tháng 11 năm 2026" in text
    assert "Chủ tọa cuộc họp: Ông TRẦN VĂN AN" in text
    # Thư ký mặc định: thành viên kế tiếp khác Chủ tọa, danh xưng theo giới tính
    assert "Thư ký cuộc họp: Bà LÊ THỊ BÌNH" in text
    # Bảng chữ ký: đủ mọi thành viên
    for m in MEMBERS:
        assert m["ho_ten"].upper() in text


def test_giai_the_bbh_votes_follow_capital(client):
    files = generate(client, "Giải thể công ty TNHH 2 TV", {
        "dia_chi_so_nha": "Số 5", "dia_chi_xa_phuong": "Phường Láng", "dia_chi_tinh_thanh": "Thành phố Hà Nội"})
    text = bbh(files)
    assert "Tham gia cuộc họp có tất cả 03/03 thành viên" in text
    assert "- Ông TRẦN VĂN AN có 600 phiếu biểu quyết, tương ứng với 60% vốn điều lệ;" in text
    assert "- Bà LÊ THỊ BÌNH có 300 phiếu biểu quyết, tương ứng với 30% vốn điều lệ;" in text
    assert "- Ông PHẠM VĂN CƯỜNG có 100 phiếu biểu quyết, tương ứng với 10% vốn điều lệ;" in text
    assert "Công ty có tổng 1.000 phiếu biểu quyết" in text
    assert text.count("1.000 phiếu") == 5  # câu tổng + 4 dòng kết quả biểu quyết
    assert "Giấy chứng nhận đăng ký vốn góp số: 02/2024/GCN cấp ngày 10/03/2024" in text
    assert "Chủ tọa cuộc họp: Ông TRẦN VĂN AN" in text
    assert "Thư ký cuộc họp: Bà LÊ THỊ BÌNH" in text

    thanh_ly = next(v for k, v in files.items() if "Báo cáo thanh lý" in k)
    assert "tiền mặt còn lại là 1,000,000,000 đồng" in thanh_ly
    assert "+ LÊ THỊ BÌNH: 300,000,000 đồng" in thanh_ly
