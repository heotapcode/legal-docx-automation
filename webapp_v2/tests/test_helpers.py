"""Unit test cho các hàm tiện ích trong services/render_service.py."""
import pytest

from services.render_service import (
    danh_xung,
    fmt_money,
    format_date_vn,
    parse_address_str,
    so_thanh_chu,
)


@pytest.mark.parametrize("value, expected", [
    (0, "0"),
    (1000, "1,000"),
    (1000000, "1,000,000"),
    ("2.500.000.000", "2,500,000,000"),
    ("1,000,000", "1,000,000"),
    (None, ""),
    ("", ""),
    ("abc", "abc"),
])
def test_fmt_money(value, expected):
    assert fmt_money(value) == expected


@pytest.mark.parametrize("value, expected", [
    (0, "Không đồng"),
    (1, "Một đồng"),
    (10, "Mười đồng"),
    (11, "Mười một đồng"),
    (15, "Mười lăm đồng"),
    (21, "Hai mươi mốt đồng"),
    (25, "Hai mươi lăm đồng"),
    (101, "Một trăm linh một đồng"),
    (105, "Một trăm linh năm đồng"),
    (1000, "Một nghìn đồng"),
    (1001, "Một nghìn không trăm linh một đồng"),
    (1005000, "Một triệu không trăm linh năm nghìn đồng"),
    (15000000, "Mười lăm triệu đồng"),
    (100000000, "Một trăm triệu đồng"),
    (1000000000, "Một tỷ đồng"),
    (1000000001, "Một tỷ không trăm linh một đồng"),
    (2500000000, "Hai tỷ năm trăm triệu đồng"),
    (1000000000000, "Một nghìn tỷ đồng"),
    ("1.000.000", "Một triệu đồng"),
    (None, ""),
    ("", ""),
])
def test_so_thanh_chu(value, expected):
    assert so_thanh_chu(value) == expected


@pytest.mark.xfail(strict=True, reason="Lỗi đã biết: dấu âm bị bỏ qua (-500 -> 'Năm trăm đồng')")
def test_so_thanh_chu_negative_is_rejected_or_signed():
    assert so_thanh_chu(-500) != "Năm trăm đồng"


@pytest.mark.parametrize("addr, expected", [
    ("Số 1 Ngõ 2, Phường Cầu Giấy, Thành phố Hà Nội", ("Số 1 Ngõ 2", "Phường Cầu Giấy", "Thành phố Hà Nội")),
    ("Tiên Hội, Xã Đông Anh, Thành phố Hà Nội", ("Tiên Hội", "Xã Đông Anh", "Thành phố Hà Nội")),
    ("", ("", "", "")),
])
def test_parse_address_str(addr, expected):
    assert parse_address_str(addr) == expected


@pytest.mark.xfail(strict=True, reason="Lỗi đã biết: địa chỉ 4 cấp (có Huyện) bị đặt Huyện vào ô Xã/Phường")
def test_parse_address_with_district():
    so_nha, xa, tinh = parse_address_str("Tiên Hội, Xã Đông Anh, Huyện Đông Anh, Hà Nội")
    assert xa.startswith("Xã")


def test_format_date_vn():
    assert format_date_vn("2026-01-05") == "ngày 05 tháng 01 năm 2026"
    assert format_date_vn("05/01/2026") == "ngày 05 tháng 01 năm 2026"
    assert format_date_vn().startswith("ngày ")


@pytest.mark.parametrize("gt, expected", [("Nam", "Ông"), ("Nữ", "Bà"), ("", "Ông/Bà"), (None, "Ông/Bà")])
def test_danh_xung(gt, expected):
    assert danh_xung(gt) == expected
