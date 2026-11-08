"""Mục 8.2a: Thông báo thay đổi nội dung ĐKDN chỉ in các phần đã chọn (bộ "Thay đổi nội dung ĐKKD")."""
import unicodedata

import pytest

from conftest import build_payload, read_zip, sample_person

NAME = "Thay đổi nội dung ĐKKD"
HEAD = {
    "A1": "ĐĂNG KÝ THAY ĐỔI TÊN DOANH NGHIỆP",
    "A2": "ĐĂNG KÝ THAY ĐỔI ĐỊA CHỈ TRỤ SỞ CHÍNH",
    "A3": "ĐĂNG KÝ THAY ĐỔI THÀNH VIÊN CÔNG TY TNHH",
    "A4": "ĐĂNG KÝ THAY ĐỔI VỐN ĐIỀU LỆ",
    "A5": "THÔNG BÁO THAY ĐỔI NGÀNH, NGHỀ KINH DOANH",
    "A6": "THÔNG BÁO THAY ĐỔI THÔNG TIN ĐĂNG KÝ THUẾ",
    "A7": "THÔNG BÁO THAY ĐỔI THÔNG TIN VỀ CHỦ SỞ HỮU HƯỞNG LỢI",
}
CP_ONLY = "Thông tin về cổ phần"
TNHH2_ONLY = "Đăng ký thay đổi phần vốn góp, tỷ lệ phần vốn góp"
GIAM_ONLY = "Doanh nghiệp cam kết bảo đảm thanh toán đủ các khoản nợ"


def thong_bao(client, selected, loai_hinh="tnhh_1tv", **extra):
    payload, _, _ = build_payload(NAME, 3)
    data = payload["data"]
    data.update(dkkd_selected=selected, loai_hinh=loai_hinh, **extra)
    # Danh sách thành viên chỉ có (và bắt buộc) khi TNHH 2 TV đổi thành viên hoặc vốn
    data["thanh_vien"] = [dict(sample_person(i), von_gop="500000000", ty_le="50") for i in (1, 2)] \
        if loai_hinh == "tnhh_2tv" and {"A3", "A4"} & set(selected) else []
    r = client.post("/api/documents/generate", json=payload)
    assert r.status_code == 200, r.text[:300]
    text = next(v for k, v in read_zip(r.content).items() if k.startswith("01."))
    return unicodedata.normalize("NFC", text)  # mẫu Word lưu một số chữ có dấu ở dạng tổ hợp


@pytest.mark.parametrize("selected", [["A1"], ["A2", "A5"], ["A1", "A4", "A6", "A7"], list(HEAD)])
def test_only_selected_sections_printed(client, selected):
    text = thong_bao(client, selected, loai_hinh="tnhh_2tv")
    for code, head in HEAD.items():
        assert (head in text) == (code in selected), code


def test_a3_only_for_tnhh_2tv(client):
    assert HEAD["A3"] not in thong_bao(client, ["A1", "A3"], loai_hinh="tnhh_1tv")
    assert HEAD["A3"] in thong_bao(client, ["A1", "A3"], loai_hinh="tnhh_2tv")


@pytest.mark.parametrize("loai_hinh, hinh_thuc, cp, tnhh2, giam", [
    ("tnhh_1tv", "tang", False, False, False),
    ("tnhh_2tv", "tang", False, True, False),
    ("cp", "giam", True, False, True),
])
def test_capital_section_by_company_type(client, loai_hinh, hinh_thuc, cp, tnhh2, giam):
    text = thong_bao(client, ["A4"], loai_hinh=loai_hinh, hinh_thuc_thay_doi_von=hinh_thuc,
                     von_cu_so="1000000000", von_dieu_le_so="3000000000")
    assert (CP_ONLY in text, TNHH2_ONLY in text, GIAM_ONLY in text) == (cp, tnhh2, giam)
    assert "1,000,000,000 VNĐ (Một tỷ đồng)" in text
    assert "3,000,000,000 VNĐ (Ba tỷ đồng)" in text
    assert ("Giảm vốn điều lệ" if giam else "Tăng vốn điều lệ") in text


def test_added_and_removed_industries_go_to_their_own_tables(client):
    text = thong_bao(client, ["A5"], nganh_bo=[{"ma": "4610", "ten": "Đại lý, môi giới, đấu giá hàng hóa"}])
    added, removed = text.split("được bỏ khỏi danh sách đã đăng ký", 1)
    assert "Lập trình máy vi tính" in added and "Lập trình máy vi tính" not in removed
    assert "Đại lý, môi giới, đấu giá hàng hóa" in removed and "4610" in removed
    # Không có ngành bỏ -> không in tiêu đề "Bỏ ngành"
    assert "Bỏ ngành, nghề kinh doanh sau" not in thong_bao(client, ["A5"], nganh_bo=[])


def test_tax_info_and_new_names(client):
    text = thong_bao(client, ["A1", "A6"], ten_moi_vn="Công ty TNHH Mới", ktt_ho_ten="Lê Văn Kế",
                     ktt_so_cccd="001090001234", dia_chi_thue_so_nha="Số 5 Phố Huế")
    assert "sau khi thay đổi: CÔNG TY TNHH MỚI" in text
    assert "Kế toán trưởng/Phụ trách kế toán: LÊ VĂN KẾ" in text and "001090001234" in text
    assert "tổ/xóm/ấp/thôn: Số 5 Phố Huế" in text
