"""Thành lập hộ kinh doanh (cá nhân): Giấy đề nghị + Giấy ủy quyền, trình bày theo hồ sơ đã điền anh gửi."""
import re
import unicodedata

import pytest

from services.dia_ban import co_quan_dk_ho_kinh_doanh

NAME = "Thành lập hộ kinh doanh"
NGANH = [
    {"ma": "8230", "ten": "Tổ chức giới thiệu và xúc tiến thương mại", "is_main": False},
    {"ma": "9621", "ten": "Dịch vụ làm tóc", "is_main": True},
]


def data(**extra):
    d = {
        "chu_ho_ho_ten": "Trần Thị Thử", "chu_ho_ngay_sinh": "20/11/1995", "chu_ho_gioi_tinh": "Nữ",
        "chu_ho_so_cccd": "001195000001", "chu_ho_dia_chi_so_nha": "Số 9 Ngõ Liên Hệ",
        "chu_ho_dia_chi_xa_phuong": "Phường Tây Mỗ", "chu_ho_dia_chi_tinh_thanh": "Hà Nội",
        "ten_hkd": "Hộ kinh doanh Thử Beauty", "hkd_dia_chi_so_nha": "Số 17 Ngõ 63 Đại Mỗ",
        "hkd_dia_chi_xa_phuong": "Phường Đại Mỗ", "hkd_dia_chi_tinh_thanh": "Hà Nội", "tinh_dang_ky": "Hà Nội",
        "hkd_sdt": "0912345678", "hkd_email": "thu@example.com", "kd_tai_tru_so": "co",
        "von_kinh_doanh_so": "40.000.000", "so_lao_dong": "1", "pp_thue_gtgt": "ke_khai",
    }
    d.update(extra)
    return d


def ho_so(client, nganh=NGANH, **extra):
    from conftest import read_zip

    r = client.post("/api/documents/generate", json={"template_name": NAME, "data": data(**extra), "ma_nganh": nganh})
    assert r.status_code == 200, r.text[:500]
    return {k: unicodedata.normalize("NFC", v) for k, v in read_zip(r.content).items()}


def test_dossier_files(client):
    assert sorted(ho_so(client)) == ["01. Giấy đề nghị đăng ký hộ kinh doanh.docx", "02. Giấy ủy quyền.docx"]


def test_application_matches_filled_sample(client):
    gdn = ho_so(client)["01. Giấy đề nghị đăng ký hộ kinh doanh.docx"]
    for s in ("Hà Nội, ngày ...... tháng ...... năm ",
              "Kính gửi: Phòng Kinh tế, Hạ tầng và Đô thị Phường Đại Mỗ",
              "Tôi là: TRẦN THỊ THỬ", "Sinh ngày: 20/11/1995", "Giới tính: Nữ", "Số định danh cá nhân: 001195000001",
              "Tên hộ kinh doanh viết bằng tiếng Việt: HỘ KINH DOANH THỬ BEAUTY",
              "Số nhà/phòng, ngách/hẻm, ngõ/kiệt, đường/phố/đại lộ, tổ/xóm/ấp/thôn: Số 17 Ngõ 63 Đại Mỗ",
              "Xã/Phường/Đặc khu: Phường Đại Mỗ", "Điện thoại: 0912345678", "Thư điện tử: thu@example.com",
              "Kinh doanh tại trụ sở: Có", "Bằng số: 40.000.000 VNĐ;", "Bằng chữ: Bốn mươi triệu đồng",
              "5.3. Tổng số lao động (dự kiến): 1", "5.4. Phương pháp tính thuế GTGT: Phương pháp kê khai",
              "6. Chủ thể thành lập hộ kinh doanh: Cá nhân", "CHỦ HỘ KINH DOANH"):
        assert s in gdn, s
    # Bảng ngành 3 cột, ngành chính ghi "(Chính)" sau mã
    assert "1\nTổ chức giới thiệu và xúc tiến thương mại\n8230\n" in gdn
    assert "2\nDịch vụ làm tóc\n9621 (Chính)\n" in gdn
    # Không còn chú thích của form mẫu, mục 7 (thành viên hộ gia đình), ô đánh dấu, dấu chấm điền tay
    for s in ("(ghi họ tên bằng chữ in hoa)", "(nếu có)", "7. Thông tin về các thành viên", "☐", "Ký và ghi họ tên",
              "........", "……", "{{", "{%"):
        assert s not in gdn, s


def test_application_options(client):
    gdn = ho_so(client, kd_tai_tru_so="khong", pp_thue_gtgt="khoan", hkd_dia_chi_xa_phuong="Xã Phú Xuyên",
                ngay_bat_dau_hd="01/12/2026", thue_dia_chi_so_nha="Số 1 Ngõ Thuế")[
        "01. Giấy đề nghị đăng ký hộ kinh doanh.docx"]
    assert "Kính gửi: Phòng Kinh tế Xã Phú Xuyên" in gdn
    assert "Kinh doanh tại trụ sở: Không" in gdn and "Phương pháp khoán" in gdn
    assert "không cần kê khai nội dung này): 01/12/2026" in gdn and "thôn: Số 1 Ngõ Thuế" in gdn


def test_power_of_attorney_uses_owner_contact_address(client):
    uq = ho_so(client)["02. Giấy ủy quyền.docx"]
    assert "Ông/Bà: \tTRẦN THỊ THỬ" in uq
    assert "Địa chỉ liên hệ: Số 9 Ngõ Liên Hệ, Phường Tây Mỗ, Hà Nội" in uq
    assert "tên dự kiến là HỘ KINH DOANH THỬ BEAUTY" in uq
    assert "được lập và ký vào ngày ...... tháng ...... năm " in uq
    assert "ĐỖ QUANG HIẾU" in uq  # Bên B: nhân viên viết sẵn (anh xác nhận)
    # Không còn số định danh nào khác ngoài của chủ hộ (dữ liệu thử) và nhân viên nhận ủy quyền
    assert set(re.findall(r"\b\d{12}\b", uq)) == {"001195000001", "001089021350"}


@pytest.mark.parametrize("field, value", [("hkd_dia_chi_xa_phuong", "Đại Mỗ"), ("ten_hkd", "Minh Châu Beauty")])
def test_format_is_checked(client, field, value):
    r = client.post("/api/documents/generate", json={"template_name": NAME, "data": data(**{field: value}),
                                                     "ma_nganh": NGANH})
    assert r.status_code == 422 and field in r.text


@pytest.mark.parametrize("xa_phuong, co_quan", [
    ("Phường Đại Mỗ", "Phòng Kinh tế, Hạ tầng và Đô thị Phường Đại Mỗ"),
    ("phường  Cầu Giấy", "Phòng Kinh tế, Hạ tầng và Đô thị Phường Cầu Giấy"),
    ("Xã Phú Xuyên", "Phòng Kinh tế Xã Phú Xuyên"),
    ("Đặc khu Phú Quốc", "Phòng Kinh tế Đặc khu Phú Quốc"),
    ("", ""),
])
def test_registration_office_by_ward(xa_phuong, co_quan):
    assert co_quan_dk_ho_kinh_doanh(xa_phuong) == co_quan
