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
    # Thành viên / cổ đông dự họp: bắt buộc với TNHH 2 TV và Cổ phần (có Biên bản họp)
    data["thanh_vien"] = [dict(sample_person(i), von_gop="500000000", ty_le="50") for i in (1, 2)] \
        if loai_hinh != "tnhh_1tv" else []
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


# ---------- Mục 8.2b: Quyết định và Biên bản họp ----------

def ho_so(client, selected, loai_hinh, **extra):
    payload, _, _ = build_payload(NAME, 3)
    data = payload["data"]
    data.update(dkkd_selected=selected, loai_hinh=loai_hinh, **extra)
    data["thanh_vien"] = [dict(sample_person(i), von_gop="500000000", ty_le="50") for i in (1, 2)] \
        if loai_hinh != "tnhh_1tv" or "A7" in selected else []
    if loai_hinh == "tnhh_2tv" and "A3" in selected and "tv_cu" not in extra:
        data["tv_cu"] = [{"ho_ten": "THÀNH VIÊN CŨ MỘT", "so_cccd": "001080000011", "gioi_tinh": "Nam",
                          "dia_chi_day_du": "Số 1 Phố Huế, Phường Hai Bà Trưng, Thành phố Hà Nội"},
                         {"ho_ten": "THÀNH VIÊN CŨ HAI", "so_cccd": "001080000022", "gioi_tinh": "Nữ",
                          "dia_chi_day_du": "Số 2 Ngõ Trạm, Phường Hoàn Kiếm, Thành phố Hà Nội"}]
    if loai_hinh == "tnhh_2tv" and "A3" in selected and "chuyen_nhuong" not in extra:
        data["chuyen_nhuong"] = [{"ben_a": "1", "ben_b": "0", "gia_tri_so": "500000000", "ty_le": "50"}]
    r = client.post("/api/documents/generate", json=payload)
    assert r.status_code == 200, r.text[:300]
    return {k: unicodedata.normalize("NFC", v) for k, v in read_zip(r.content).items()}


@pytest.mark.parametrize("loai_hinh, co_quan, so, has_bbh", [
    ("tnhh_1tv", "QUYẾT ĐỊNH CỦA CHỦ SỞ HỮU", "QĐ-CSH", False),
    ("tnhh_2tv", "QUYẾT ĐỊNH CỦA HỘI ĐỒNG THÀNH VIÊN", "QĐ-HĐTV", True),
    ("cp", "QUYẾT ĐỊNH CỦA ĐẠI HỘI ĐỒNG CỔ ĐÔNG", "QĐ-ĐHĐCĐ", True),
])
def test_decision_and_minutes_by_company_type(client, loai_hinh, co_quan, so, has_bbh):
    files = ho_so(client, ["A1"], loai_hinh)
    qd = next(v for k, v in files.items() if k.startswith("03."))
    assert co_quan in qd and f"Số: 01/2026/{so}" in qd
    assert any(k.startswith("04. Biên bản họp") for k in files) is has_bbh
    assert ("Căn cứ Biên bản họp" in qd) is has_bbh


def test_one_article_per_selected_content_numbered_in_order(client):
    files = ho_so(client, ["A2", "A5", "A6", "A7"], "tnhh_1tv",
                  nganh_bo=[{"ma": "4610", "ten": "Đại lý, môi giới, đấu giá hàng hóa"}])
    qd = next(v for k, v in files.items() if k.startswith("03."))
    dieu = [line.split(".")[0] + "." + line.split(".", 1)[1][:80] for line in qd.splitlines() if line.startswith("Điều ")]
    # A2, A5, sửa Điều lệ, giao thực hiện, hiệu lực; A6/A7 không có Điều riêng
    assert [d.split(".")[0] for d in dieu] == ["Điều 1", "Điều 2", "Điều 3", "Điều 4", "Điều 5"]
    assert "địa chỉ trụ sở chính" in dieu[0] and "ngành, nghề" in dieu[1] and "Điều lệ" in dieu[2]
    assert "Bỏ các ngành, nghề kinh doanh sau" in qd and "Đại lý, môi giới, đấu giá hàng hóa (Mã ngành: 4610)" in qd
    assert "- Như Điều 5;" in qd


@pytest.mark.parametrize("loai_hinh, selected", [("tnhh_1tv", ["A6"]), ("cp", ["A6", "A7"]), ("tnhh_2tv", ["A7"])])
def test_no_decision_or_minutes_when_only_tax_or_beneficial_owner(client, loai_hinh, selected):
    """A6, A7 không đưa vào Quyết định/Biên bản họp (anh xác nhận 10/11/2026): chỉ chọn A6/A7 thì không sinh hai văn bản này."""
    files = ho_so(client, selected, loai_hinh)
    assert not any(k.startswith(("03.", "04.")) for k in files)


def test_minutes_lists_attendees_and_contents(client):
    files = ho_so(client, ["A4", "A7"], "cp", hinh_thuc_thay_doi_von="giam", von_cu_so="3000000000",
                  von_dieu_le_so="2000000000")
    bbh = next(v for k, v in files.items() if k.startswith("04."))
    assert "BIÊN BẢN HỌP ĐẠI HỘI ĐỒNG CỔ ĐÔNG" in bbh and "Tổng số cổ đông dự họp: 02/02 cổ đông" in bbh
    assert "1. Giảm vốn điều lệ từ 3,000,000,000 đồng xuống 2,000,000,000 đồng." in bbh
    assert "chủ sở hữu hưởng lợi" not in bbh and "đăng ký thuế" not in bbh
    assert "CÁC CỔ ĐÔNG DỰ HỌP KÝ TÊN" in bbh


# ---------- Mục 8.2c: văn bản kèm theo ----------

@pytest.mark.parametrize("loai_hinh, selected, expected", [
    ("tnhh_1tv", ["A1"], ["01.", "02.", "03."]),
    ("tnhh_2tv", ["A4"], ["01.", "02.", "03.", "04.", "05."]),
    ("tnhh_2tv", ["A3"], ["01.", "02.", "03.", "04.", "05.", "08.", "09."]),  # đổi thành viên: HĐ + BB thanh lý
    ("tnhh_2tv", ["A1"], ["01.", "02.", "03.", "04."]),          # không đổi thành viên/vốn: không có DS thành viên
    ("cp", ["A4", "A7"], ["01.", "02.", "03.", "04.", "06."]),    # Cổ phần không có DS thành viên
    ("tnhh_1tv", ["A8"], ["02.", "03.", "07."]),                  # chỉ đổi ĐDPL: không có Thông báo thay đổi ĐKDN
    ("tnhh_1tv", ["A6"], ["01.", "02."]),                         # chỉ đổi thông tin thuế: không có Quyết định
    ("cp", ["A6", "A7"], ["01.", "02.", "06."]),                  # thuế + CSHHL: không có Quyết định, Biên bản họp
])
def test_attachments_follow_selection(client, loai_hinh, selected, expected):
    files = ho_so(client, selected, loai_hinh)
    assert sorted(k[:3] for k in files if k.endswith(".docx")) == expected


def test_change_of_legal_representative(client):
    files = ho_so(client, ["A8"], "cp", ddpl_cu_ho_ten="TRẦN VĂN CŨ", ddpl_cu_so_cccd="001080000001")
    qd = next(v for k, v in files.items() if k.startswith("03."))
    assert "miễn nhiệm" in qd and "TRẦN VĂN CŨ" in qd and "001080000001" in qd
    tb = next(v for k, v in files.items() if k.startswith("07."))
    assert "Số định danh cá nhân của Chủ tịch hội đồng quản trị" in tb and "CHỦ TỊCH HỘI ĐỒNG QUẢN TRỊ" in tb


def test_beneficial_owner_list_uses_entered_people(client):
    files = ho_so(client, ["A7"], "tnhh_1tv")
    ds = next(v for k, v in files.items() if k.startswith("06."))
    assert "NGUYỄN VĂN THỬ1" in ds and "NGUYỄN VĂN THỬ2" in ds



# ---------- Người ký, chủ tọa, thư ký, người dự họp (anh xác nhận 08/11/2026) ----------

CHU_TICH = dict(chu_tich_ho_ten="Lê Văn Chủ Tịch", chu_tich_so_cccd="001070000007", chu_tich_gioi_tinh="Nam")


@pytest.mark.parametrize("loai_hinh, chuc_danh", [
    ("tnhh_1tv", "CHỦ SỞ HỮU CÔNG TY"),
    ("tnhh_2tv", "CHỦ TỊCH HỘI ĐỒNG THÀNH VIÊN"),
    ("cp", "CHỦ TỊCH HỘI ĐỒNG QUẢN TRỊ"),
])
def test_decision_signed_by_owner_or_chairman(client, loai_hinh, chuc_danh):
    files = ho_so(client, ["A1"], loai_hinh, **CHU_TICH)
    qd = next(v for k, v in files.items() if k.startswith("03."))
    sign = qd[qd.index(chuc_danh):]
    assert "LÊ VĂN CHỦ TỊCH" in sign


def test_chair_and_secretary_in_minutes(client):
    # Chủ tịch cũng là thành viên thứ nhất -> thư ký là thành viên tiếp theo
    files = ho_so(client, ["A1"], "cp", chu_tich_ho_ten="NGUYỄN VĂN THỬ1", chu_tich_so_cccd="001090000001",
                  chu_tich_gioi_tinh="Nam")
    bbh = next(v for k, v in files.items() if k.startswith("04."))
    assert "Chủ tọa cuộc họp: Ông NGUYỄN VĂN THỬ1 — Chủ tịch Hội đồng quản trị." in bbh
    assert "Thư ký cuộc họp: Bà NGUYỄN VĂN THỬ2 — Cổ đông." in bbh


def test_member_change_minutes_attended_by_members_before_change(client):
    files = ho_so(client, ["A3"], "tnhh_2tv", **CHU_TICH)
    bbh = next(v for k, v in files.items() if k.startswith("04."))
    attendees = bbh.split("I. THÀNH PHẦN DỰ HỌP:", 1)[1].split("Tổng số", 1)[0]
    assert "THÀNH VIÊN CŨ MỘT" in attendees and "THÀNH VIÊN CŨ HAI" in attendees
    assert "NGUYỄN VĂN THỬ1" not in attendees, "Không phải danh sách sau thay đổi"
    # Danh sách thành viên kèm hồ sơ vẫn là danh sách SAU thay đổi
    dstv = next(v for k, v in files.items() if k.startswith("05."))
    assert "NGUYỄN VĂN THỬ1" in dstv


def test_representative_notice_signed_by_chairman(client):
    files = ho_so(client, ["A8"], "tnhh_2tv", **CHU_TICH)
    tb = next(v for k, v in files.items() if k.startswith("07."))
    assert "Số định danh cá nhân của Chủ tịch hội đồng thành viên: 001070000007" in tb
    assert tb.rstrip().endswith("LÊ VĂN CHỦ TỊCH")



def test_member_change_contracts_one_per_transaction(client):
    files = ho_so(client, ["A3"], "tnhh_2tv", chuyen_nhuong=[
        {"ben_a": "1", "ben_b": "0", "gia_tri_so": "500000000", "ty_le": "25"},
        {"ben_a": "0", "ben_b": "1", "gia_tri_so": "300000000", "ty_le": "15"}])
    hd = sorted(k for k in files if k.startswith("08."))
    assert hd == ["08. Hợp đồng chuyển nhượng_a (THÀNH VIÊN CŨ HAI - NGUYỄN VĂN THỬ1).docx",
                  "08. Hợp đồng chuyển nhượng_b (THÀNH VIÊN CŨ MỘT - NGUYỄN VĂN THỬ2).docx"]
    assert len([k for k in files if k.startswith("09.")]) == 2
    text = files[hd[0]]
    assert "001080000022" in text and "Số 2 Ngõ Trạm" in text and "500,000,000 VNĐ (Năm trăm triệu đồng)" in text


def test_member_change_requires_valid_transaction(client):
    payload, _, _ = build_payload(NAME, 3)
    data = payload["data"]
    data.update(loai_hinh="tnhh_2tv", dkkd_selected=["A3"],
                thanh_vien=[dict(sample_person(i), von_gop="1", ty_le="50") for i in (1, 2)],
                tv_cu=[{"ho_ten": "A", "so_cccd": "001080000011", "dia_chi_day_du": "x"},
                       {"ho_ten": "B", "so_cccd": "001080000022", "dia_chi_day_du": "y"}],
                chuyen_nhuong=[{"ben_a": "5", "ben_b": "0", "gia_tri_so": "1"}])
    r = client.post("/api/documents/generate", json=payload)
    assert r.status_code == 422
    assert any(e["code"] == "options_from" and e["key"] == "ben_a" for e in r.json()["errors"])
