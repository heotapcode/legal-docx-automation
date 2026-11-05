"""Sửa dữ liệu viết cứng trong Biên bản họp của 2 bộ mẫu (chạy một lần, từ thư mục gốc repo):
    python scripts_and_tools/fix_bbh_hardcoded_members.py

1. "Thay đổi địa chỉ và thuế TNHH 2 TV" / 03. Biên bản họp Hội đồng thành viên:
   - 3 thành viên thật (họ tên, ngày sinh, CCCD) -> lặp danh sách {{ thanh_vien }} nhập vào
   - ngày họp 22/10/2026 và tên "Công ty TNHH Logistics CMC" -> {{ ngay_lap }}, {{ ten_cong_ty_vn }}
   - "Ông"/"bà" cố định -> danh xưng theo giới tính
   - bảng chữ ký có tên "TRẦN ĐĂNG HÀO" -> một cột cho mỗi thành viên
   Các file còn lại cùng bộ (01, 02, 04): ngày 22/10/2026, "Công ty TNHH Logistics CMC", số hiệu "TB-CMC"
   -> {{ ngay_lap }} / {{ ngay_lap_ngan }} / {{ ten_cong_ty_vn }}
2. "Giải thể công ty TNHH 2 TV" / 02. Biên bản họp và 04. Báo cáo thanh lý tài sản:
   - 2 thành viên cố định, số GCN "01/2025/GCN cấp ngày 30/09/2025" dùng chung -> lặp danh sách
   - số phiếu 3.000 / 2.000 / 5000 và tỷ lệ 60% / 40% -> tính từ vốn góp ({{ tv.so_phieu }}, {{ tong_so_phieu }})
   - "Ông" cố định trước tên thư ký -> {{ thu_ky_danh_xung }}
"""
import copy
from pathlib import Path

import docx
from docx.text.paragraph import Paragraph

TEMPLATES = Path(__file__).resolve().parent.parent / "webapp_v2" / "templates"


def set_text(p: Paragraph, text: str, keep_runs: int = 1):
    """Đặt chữ cho đoạn văn, giữ định dạng của run đầu tiên, xóa các run còn lại."""
    runs = p.runs
    assert runs, "đoạn văn không có run"
    runs[0].text = text
    for r in runs[keep_runs:]:
        r._r.getparent().remove(r._r)


def insert_after(p: Paragraph, text: str) -> Paragraph:
    new = copy.deepcopy(p._p)
    p._p.addnext(new)
    para = Paragraph(new, p._parent)
    set_text(para, text)
    return para


def replace_in_runs(p: Paragraph, old: str, new: str) -> int:
    n = 0
    for r in p.runs:
        if old in r.text:
            r.text = r.text.replace(old, new)
            n += 1
    return n


def find(doc, startswith: str) -> Paragraph:
    hits = [p for p in doc.paragraphs if p.text.strip().startswith(startswith)]
    assert len(hits) == 1, (startswith, len(hits))
    return hits[0]


def already_fixed(doc) -> bool:
    return any("thanh_vien" in p.text and "{%" in p.text for p in doc.paragraphs)


def fix_thay_doi_dia_chi():
    path = TEMPLATES / "Thay đổi địa chỉ và thuế TNHH 2 TV" / "03. Biên bản họp Hội đồng thành viên.docx"
    doc = docx.Document(str(path))
    if already_fixed(doc):
        print("Bỏ qua (đã sửa):", path.name)
        return

    p = find(doc, "Hôm nay, vào hồi")
    text = p.text
    assert "ngày 22 tháng 10 năm 2026" in text and "Công ty TNHH Logistics CMC" in text
    set_text(p, text.replace("ngày 22 tháng 10 năm 2026", "{{ ngay_lap }}")
                    .replace("Công ty TNHH Logistics CMC", "{{ ten_cong_ty_vn }}"))

    # 3 dòng thành viên viết cứng -> vòng lặp (giữ in đậm phần họ tên)
    m1 = find(doc, "1. Ông NGUYỄN NHƯ HÙNG")
    m2 = find(doc, "2. Ông LƯU ĐỨC KIÊN")
    m3 = find(doc, "3. Ông TRẦN ĐĂNG HÀO")
    # Dòng 1 -> thẻ mở vòng lặp, dòng 2 -> nội dung mỗi thành viên, dòng 3 -> thẻ đóng
    set_text(m1, "{%p for tv in thanh_vien %}")
    r = m2.runs
    assert len(r) >= 2
    r[0].text = "{{ tv.stt }}. {{ tv.danh_xung }} {{ tv.ho_ten }}"
    r[1].text = " — Sinh ngày: {{ tv.ngay_sinh }} — CCCD số: {{ tv.so_cccd }}"
    for extra in r[2:]:
        extra._r.getparent().remove(extra._r)
    set_text(m3, "{%p endfor %}")

    p = find(doc, "Tổng số thành viên dự họp:")
    set_text(p, "Tổng số thành viên dự họp: {{ '%02d' % (thanh_vien|length) }}/{{ '%02d' % (thanh_vien|length) }} "
                "thành viên, đại diện cho 100% tổng số vốn điều lệ của Công ty.")
    p = find(doc, "Chủ tọa cuộc họp:")
    assert replace_in_runs(p, "Ông {{ ddpl_ho_ten }}", "{{ ddpl_danh_xung }} {{ ddpl_ho_ten }}") == 1
    p = find(doc, "Thư ký cuộc họp:")
    assert replace_in_runs(p, "Ông {{ thu_ky_ho_ten }}", "{{ thu_ky_danh_xung }} {{ thu_ky_ho_ten }}") == 1
    p = find(doc, "2. Cập nhật thông tin đăng ký thuế")
    assert replace_in_runs(p, "là bà {{ ktt_ho_ten }}", "là {{ ktt_ho_ten }}") == 1

    # Bảng tiêu đề: ngày lập
    cell = doc.tables[0].rows[1].cells[1]
    assert "ngày 22 tháng 10 năm 2026" in cell.text
    for cp in cell.paragraphs:
        replace_in_runs(cp, "ngày 22 tháng 10 năm 2026", "{{ ngay_lap }}")
    assert "{{ ngay_lap }}" in cell.text, "ngày bị tách run, cần sửa tay"

    # Bảng chữ ký thành viên: 1 cột / thành viên
    sig = doc.tables[2]
    cells = sig.rows[0].cells
    assert len(cells) == 3 and "TRẦN ĐĂNG HÀO" in cells[2].text
    template_par = cells[1].paragraphs[-1]          # đoạn chứa tên, giữ định dạng (in đậm)
    assert "{{ thu_ky_ho_ten }}" in template_par.text
    replace_in_runs(template_par, "{{ thu_ky_ho_ten }}", "{{ tv.ho_ten }}")
    for cp in cells[0].paragraphs[1:]:
        cp._p.getparent().remove(cp._p)
    set_text(cells[0].paragraphs[0], "{%tc for tv in thanh_vien %}")
    for cp in cells[2].paragraphs[1:]:
        cp._p.getparent().remove(cp._p)
    set_text(cells[2].paragraphs[0], "{%tc endfor %}")

    doc.save(str(path))
    print("Đã sửa:", path.name)


def fix_giai_the_2tv():
    folder = TEMPLATES / "Giải thể công ty TNHH 2 TV"
    path = folder / "02. Biên bản họp.docx"
    doc = docx.Document(str(path))
    if already_fixed(doc):
        print("Bỏ qua (đã sửa):", path.name, "và 04. Báo cáo thanh lý tài sản.docx")
        return

    p = find(doc, "Tham gia cuộc họp có tất cả")
    set_text(p, "Tham gia cuộc họp có tất cả {{ '%02d' % (thanh_vien|length) }}/{{ '%02d' % (thanh_vien|length) }} "
                "thành viên, sở hữu và đại diện cho 100 % vốn điều lệ công ty, cụ thể gồm:")

    ho_ten_1 = find(doc, "Họ và tên: {{ ddpl_ho_ten }}")
    von_1 = find(doc, "Số vốn góp: {{ ddpl_von_gop }}")
    gcn_paras = [q for q in doc.paragraphs if q.text.strip().startswith("Giấy chứng nhận đăng ký vốn góp số")]
    assert len(gcn_paras) == 2
    ho_ten_2 = find(doc, "Họ và tên: {{ tv2_ho_ten }}")
    von_2 = find(doc, "Số vốn góp: {{ tv2_von_gop }}")

    # Thành viên 1 -> thân vòng lặp; thành viên 2 -> thẻ mở/đóng vòng lặp
    set_text(ho_ten_2, "{%p endfor %}")
    for q in (von_2, gcn_paras[1]):
        q._p.getparent().remove(q._p)
    open_tag = copy.deepcopy(ho_ten_1._p)
    ho_ten_1._p.addprevious(open_tag)
    set_text(Paragraph(open_tag, ho_ten_1._parent), "{%p for tv in thanh_vien %}")
    set_text(ho_ten_1, "Họ và tên: {{ tv.ho_ten }}")
    set_text(von_1, "Số vốn góp: {{ tv.von_gop }} đồng ({{ tv.von_chu }}), chiếm {{ tv.ty_le }}% tổng số vốn điều lệ.")
    set_text(gcn_paras[0], "Giấy chứng nhận đăng ký vốn góp số: {{ tv.so_gcn or '……' }} cấp ngày {{ tv.ngay_gcn or '……' }}")

    p = find(doc, "Thư ký cuộc họp:")
    set_text(p, "Thư ký cuộc họp: {{ thu_ky_danh_xung }} {{ thu_ky_ho_ten }}")
    p = find(doc, "Chủ tọa cuộc họp:")
    set_text(p, "Chủ tọa cuộc họp: {{ ddpl_danh_xung }} {{ ddpl_ho_ten }} - Chức vụ: Chủ tịch HĐTV")

    # Đoạn quy ước phiếu: tách thành câu mở đầu + 1 dòng/thành viên + câu tổng
    p = find(doc, "Công ty quy ước 1.000.000 đồng")
    set_text(p, "Công ty quy ước 1.000.000 đồng tương ứng với 1 phiếu biểu quyết. Vậy:")
    q1 = insert_after(p, "{%p for tv in thanh_vien %}")
    q2 = insert_after(q1, "- {{ tv.danh_xung }} {{ tv.ho_ten }} có {{ tv.so_phieu }} phiếu biểu quyết, "
                          "tương ứng với {{ tv.ty_le }}% vốn điều lệ;")
    q3 = insert_after(q2, "{%p endfor %}")
    insert_after(q3, "Công ty có tổng {{ tong_so_phieu }} phiếu biểu quyết, tương ứng với 100% vốn điều lệ.")

    n = sum(replace_in_runs(q, "5000 phiếu", "{{ tong_so_phieu }} phiếu") for q in doc.paragraphs)
    assert n == 4, n

    # Bảng chữ ký: thư ký là thu_ky_ho_ten (không cố định là thành viên thứ 2)
    sig = doc.tables[1].rows[0].cells[1]
    assert "{{ tv2_ho_ten }}" in sig.text
    for cp in sig.paragraphs:
        replace_in_runs(cp, "{{ tv2_ho_ten }}", "{{ thu_ky_ho_ten }}")
    assert "{{ thu_ky_ho_ten }}" in sig.text
    doc.save(str(path))
    print("Đã sửa:", path.name)

    # 04. Báo cáo thanh lý: danh sách hoàn trả vốn theo thành viên, tổng có đơn vị
    path = folder / "04. Báo cáo thanh lý tài sản.docx"
    doc = docx.Document(str(path))
    for q in doc.paragraphs:
        replace_in_runs(q, "{{ tong_von_gop }}", "{{ tong_von_gop }} đồng")
    line_1 = find(doc, "+ {{ ddpl_ho_ten }}: {{ ddpl_von_gop }}")
    line_2 = find(doc, "+ {{ tv2_ho_ten }}: {{ tv2_von_gop }}")
    open_tag = copy.deepcopy(line_1._p)
    line_1._p.addprevious(open_tag)
    set_text(Paragraph(open_tag, line_1._parent), "{%p for tv in thanh_vien %}")
    set_text(line_1, "     + {{ tv.ho_ten }}: {{ tv.von_gop }} đồng")
    set_text(line_2, "{%p endfor %}")
    doc.save(str(path))
    print("Đã sửa:", path.name)


def _all_paragraphs(doc):
    yield from doc.paragraphs
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                yield from cell.paragraphs


def fix_thay_doi_dia_chi_others():
    folder = TEMPLATES / "Thay đổi địa chỉ và thuế TNHH 2 TV"
    replacements = {
        "01. Thông báo thay đổi ĐKKD và thông tin thuế.docx": [
            ("ngày 22 tháng 10 năm 2026", "{{ ngay_lap }}"),
            ("01/2026/TB-CMC", "01/2026/TB"),
        ],
        "02. Quyết định của Hội đồng thành viên.docx": [
            ("Công ty TNHH Logistics CMC", "{{ ten_cong_ty_vn }}"),
            ("ngày 22/10/2026", "ngày {{ ngay_lap_ngan }}"),
            ("ngày 22 tháng 10 năm 2026", "{{ ngay_lap }}"),
        ],
        "04. Giấy ủy quyền.docx": [
            ("ngày 22 tháng 10 năm 2026", "{{ ngay_lap }}"),
        ],
    }
    for fname, pairs in replacements.items():
        path = folder / fname
        doc = docx.Document(str(path))
        changed = 0
        for p in _all_paragraphs(doc):
            for old, new in pairs:
                if old in p.text:
                    n = replace_in_runs(p, old, new)
                    assert n, f"{fname}: '{old}' bị tách qua nhiều run, cần sửa tay"
                    changed += n
        doc.save(str(path))
        leftover = [o for p in _all_paragraphs(docx.Document(str(path))) for o, _ in pairs if o in p.text]
        assert not leftover, (fname, leftover)
        print(f"{'Đã sửa' if changed else 'Bỏ qua (đã sửa)'}: {fname} ({changed} chỗ)")


if __name__ == "__main__":
    fix_thay_doi_dia_chi()
    fix_thay_doi_dia_chi_others()
    fix_giai_the_2tv()
