"""Mục 8.2a: dựng mẫu "Giấy đề nghị / Thông báo thay đổi nội dung ĐKDN" chỉ in các phần đã chọn.

Biến đổi file webapp_v2/templates/Thay đổi nội dung ĐKKD/01. Thông báo bổ sung cập nhật.docx (mẫu nhà nước, giữ
nguyên câu chữ) thành mẫu docxtpl:

- Mỗi phần A1..A7 được bọc {%p if 'Ax' in dkkd_selected %} ... {%p endif %}. Các tiêu đề phần là danh sách đánh số
  tự động của Word, nên bỏ phần nào thì các phần còn lại tự đánh số lại liên tục.
- A3 (thay đổi thành viên) chỉ in cho TNHH 2 TV; trong A4: "Thông tin về cổ phần" chỉ cho Cổ phần, "phần vốn góp"
  chỉ cho TNHH 2 TV, cam kết thanh toán nợ chỉ khi giảm vốn.
- Điền dữ liệu: tên mới, địa chỉ mới, vốn cũ/mới (số và chữ), bảng nguồn vốn, ngành bổ sung (bảng tự điền theo
  danh sách ngành đã chọn), ngành bỏ ({%tr for %}), kế toán trưởng và địa chỉ nhận thông báo thuế.
- Bỏ phần "Sửa đổi chi tiết ngành, nghề" (thủ tục gộp chỉ hỗ trợ bổ sung và bỏ ngành) và các dòng trống thừa.

Chạy một lần từ thư mục gốc repo:  python scripts_and_tools/build_muc8_thong_bao.py
Đã chạy rồi thì từ chối chạy lại (phát hiện thẻ {%p if trong file).
"""
import copy
import sys
import unicodedata
from pathlib import Path

import docx
from docx.oxml.ns import qn

PATH = Path(__file__).resolve().parent.parent / "webapp_v2" / "templates" / "Thay đổi nội dung ĐKKD" / \
    "01. Thông báo bổ sung cập nhật.docx"


def new_par_before(anchor, text):
    """Đoạn văn mới chỉ chứa `text`, chèn ngay trước phần tử `anchor` (đoạn văn hoặc bảng)."""
    p = anchor.makeelement(qn("w:p"), {})
    r = p.makeelement(qn("w:r"), {})
    t = r.makeelement(qn("w:t"), {})
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    r.append(t)
    p.append(r)
    anchor.addprevious(p)
    return p


def append_text(paragraph, text):
    """Thêm `text` vào cuối đoạn, theo định dạng của run cuối có chữ (không in nghiêng phần ghi chú)."""
    runs = [r for r in paragraph.runs if r.text.strip()] or paragraph.runs
    if runs:
        new = copy.deepcopy(runs[0]._r)
        for t in new.findall(qn("w:t")):
            new.remove(t)
        rpr = new.find(qn("w:rPr"))
        if rpr is not None:
            for tag in ("w:i", "w:iCs"):
                el = rpr.find(qn(tag))
                if el is not None:
                    rpr.remove(el)
        paragraph._p.append(new)
        from docx.text.run import Run
        Run(new, paragraph).text = text
    else:
        paragraph.add_run(text)


def set_par_text(paragraph, text):
    """Thay toàn bộ chữ của đoạn, giữ định dạng run đầu."""
    runs = paragraph.runs
    if not runs:
        paragraph.add_run(text)
        return
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)


def set_cell(cell, text):
    set_par_text(cell.paragraphs[0], text)


def remove(el):
    el.getparent().remove(el)


def main():
    d = docx.Document(str(PATH))
    if any("{%p if" in p.text for p in d.paragraphs):
        sys.exit("Mẫu đã được dựng (có thẻ {%p if), không chạy lại.")
    P, T = list(d.paragraphs), list(d.tables)
    # Chuẩn hóa Unicode (NFC): file Word có thể lưu chữ có dấu ở dạng tổ hợp
    head = lambda i: unicodedata.normalize("NFC", P[i].text.strip())  # noqa: E731
    # Kiểm tra đúng mẫu gốc (vị trí các tiêu đề phần)
    assert head(45).startswith("ĐĂNG KÝ THAY ĐỔI TÊN DOANH NGHIỆP")
    assert head(51).startswith("ĐĂNG KÝ THAY ĐỔI ĐỊA CHỈ TRỤ SỞ CHÍNH")
    assert head(62).startswith("ĐĂNG KÝ THAY ĐỔI THÀNH VIÊN")
    assert head(85).startswith("ĐĂNG KÝ THAY ĐỔI VỐN ĐIỀU LỆ")
    assert head(101).startswith("THÔNG BÁO THAY ĐỔI NGÀNH")
    assert head(107).startswith("THÔNG BÁO THAY ĐỔI THÔNG TIN ĐĂNG KÝ THUẾ")
    assert head(109).startswith("THÔNG BÁO THAY ĐỔI THÔNG TIN VỀ CHỦ SỞ HỮU HƯỞNG LỢI")
    assert head(104).startswith("Sửa đổi chi tiết ngành")

    # ----- Điền dữ liệu -----
    append_text(P[46], "{{ ten_moi_vn | upper }}")
    append_text(P[47], " {{ ten_moi_nn | upper }}")
    append_text(P[48], " {{ ten_moi_viet_tat | upper }}")
    append_text(P[53], " {{ dia_chi_moi_so_nha }}")
    append_text(P[54], "{{ dia_chi_moi_xa_phuong }}")
    append_text(P[55], "{{ dia_chi_moi_tinh_thanh }}")
    P[56].runs[0].text = "Điện thoại: {{ sdt_cong_ty }}"
    P[57].runs[6].text = ": {{ email_cong_ty }}"
    append_text(P[87], "{{ von_cu_so }} VNĐ ({{ von_cu_chu }})")
    append_text(P[88], "{{ von_dieu_le_so }} VNĐ ({{ von_dieu_le_chu }})")
    append_text(P[91], "{{ ngay_thay_doi_von }}")
    append_text(P[92], "{{ 'Giảm vốn điều lệ' if hinh_thuc_thay_doi_von == 'giam' else 'Tăng vốn điều lệ' }}")
    append_text(P[96], "{{ menh_gia_co_phan }}")
    # Bảng nguồn vốn (T2): vốn tư nhân 100%; bảng tài sản góp vốn (T3): Đồng Việt Nam 100%
    for t, rows in ((T[2], ("Vốn tư nhân", "Tổng cộng")), (T[3], ("Đồng Việt Nam", "Tổng số"))):
        for row in t.rows:
            label = row.cells[0].text.strip() + " " + row.cells[1].text.strip()
            if any(k in label for k in rows):
                set_cell(row.cells[-2], "{{ von_dieu_le_so }}")
                set_cell(row.cells[-1], "100")
    # Ngành bỏ (T6): một dòng cho mỗi ngành trong nganh_bo
    t6 = T[6]
    data_tr = t6.rows[1]._tr
    for_tr, end_tr = copy.deepcopy(data_tr), copy.deepcopy(data_tr)
    data_tr.addprevious(for_tr)
    data_tr.addnext(end_tr)
    rows = t6.rows
    set_cell(rows[1].cells[0], "{%tr for n in nganh_bo %}")
    for c in rows[1].cells[1:]:
        set_cell(c, "")
    for c, v in zip(rows[2].cells, ("{{ loop.index }}", "{{ n.ten }}", "{{ n.ma }}", "")):
        set_cell(c, v)
    set_cell(rows[3].cells[0], "{%tr endfor %}")
    for c in rows[3].cells[1:]:
        set_cell(c, "")
    # Thông tin đăng ký thuế (T8): kế toán trưởng (dòng 2) và địa chỉ nhận thông báo thuế (dòng 3)
    ktt = T[8].rows[2].cells[1].paragraphs
    set_par_text(ktt[1], "Họ, chữ đệm và tên Kế toán trưởng/Phụ trách kế toán: {{ ktt_ho_ten | upper }}")
    set_par_text(ktt[2], "Ngày, tháng, năm sinh: {{ ktt_ngay_sinh }}")
    set_par_text(ktt[3], "Giới tính: {{ ktt_gioi_tinh if ktt_ho_ten else '' }}")
    set_par_text(ktt[4], "Số định danh cá nhân: {{ ktt_so_cccd }}")
    set_par_text(ktt[5], "Điện thoại: {{ ktt_sdt }}")
    thue = T[8].rows[3].cells[1].paragraphs
    set_par_text(thue[1], "Số nhà/phòng, ngách/hẻm, ngõ/kiệt, đường/phố/đại lộ, tổ/xóm/ấp/thôn: "
                          "{{ dia_chi_thue_so_nha or dia_chi_moi_so_nha or dia_chi_so_nha }}")
    set_par_text(thue[2], "Xã/Phường/Đặc khu: {{ dia_chi_thue_xa_phuong or dia_chi_moi_xa_phuong or dia_chi_xa_phuong }}")
    set_par_text(thue[3], "Tỉnh/Thành phố trực thuộc trung ương: "
                          "{{ dia_chi_thue_tinh_thanh or dia_chi_moi_tinh_thanh or dia_chi_tinh_thanh }}")
    set_par_text(thue[4], "Điện thoại (nếu có): {{ sdt_cong_ty }}")
    set_par_text(thue[5], "Thư điện tử (nếu có): {{ email_cong_ty }}")

    # ----- Bỏ phần "Sửa đổi chi tiết ngành" và dòng trống thừa -----
    remove(P[104]._p)
    remove(T[7]._tbl)
    for i in list(range(11, 45)) + list(range(65, 85)) + list(range(113, 141)):
        assert not P[i].text.strip(), i
        remove(P[i]._p)

    # ----- Điều kiện hiển thị -----
    sec = lambda code: f"{{%p if '{code}' in dkkd_selected %}}"  # noqa: E731
    new_par_before(P[45]._p, sec("A1"))
    new_par_before(P[51]._p, "{%p endif %}")
    new_par_before(P[51]._p, sec("A2"))
    new_par_before(P[62]._p, "{%p endif %}")
    new_par_before(P[62]._p, "{%p if 'A3' in dkkd_selected and loai_hinh == 'tnhh_2tv' %}")
    new_par_before(P[85]._p, "{%p endif %}")
    new_par_before(P[85]._p, sec("A4"))
    new_par_before(P[95]._p, "{%p if loai_hinh == 'cp' %}")
    new_par_before(P[97]._p, "{%p endif %}")
    new_par_before(P[97]._p, "{%p if loai_hinh == 'tnhh_2tv' %}")
    new_par_before(P[100]._p, "{%p endif %}")
    new_par_before(P[100]._p, "{%p if hinh_thuc_thay_doi_von == 'giam' %}")
    new_par_before(P[101]._p, "{%p endif %}")
    new_par_before(P[101]._p, "{%p endif %}")  # hết A4
    new_par_before(P[101]._p, sec("A5"))
    new_par_before(P[102]._p, "{%p if ma_nganh %}")
    new_par_before(P[103]._p, "{%p endif %}")
    new_par_before(P[103]._p, "{%p if nganh_bo %}")
    new_par_before(P[105]._p, "{%p endif %}")
    new_par_before(P[107]._p, "{%p endif %}")  # hết A5
    new_par_before(P[107]._p, sec("A6"))
    new_par_before(P[109]._p, "{%p endif %}")
    new_par_before(P[109]._p, sec("A7"))
    new_par_before(P[111]._p, "{%p endif %}")

    d.save(str(PATH))
    print(f"Đã dựng {PATH.name}")


if __name__ == "__main__":
    main()
