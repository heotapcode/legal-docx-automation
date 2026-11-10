"""Mục 8.2b: dựng Quyết định và Biên bản họp cho thủ tục gộp thay đổi ĐKDN (bộ "Thay đổi nội dung ĐKKD").

Nền: hai mẫu của bộ "Thay đổi địa chỉ và thuế TNHH 2 TV" (giữ khổ giấy, kiểu chữ, bảng tiêu đề, bảng ký).
Câu chữ là BẢN NHÁP, cần người làm pháp lý duyệt (docs/muc8-bang-nghiep-vu.md).

- 03. Quyết định.docx: của Chủ sở hữu (TNHH 1 TV) / Hội đồng thành viên (TNHH 2 TV) / Đại hội đồng cổ đông (Cổ phần).
  Mỗi nội dung đã chọn là một Điều, đánh số tự động; tiếp theo là Điều sửa Điều lệ (nếu có A1-A5, A8), Điều giao người
  đại diện làm thủ tục, Điều hiệu lực.
- A6 (thông tin đăng ký thuế) và A7 (chủ sở hữu hưởng lợi) không đưa vào Quyết định và Biên bản họp (anh xác nhận
  10/11/2026); chỉ chọn A6/A7 thì bộ hồ sơ không có Quyết định, Biên bản họp (điều kiện ở _schema.json).
- 04. Biên bản họp.docx: Hội đồng thành viên / Đại hội đồng cổ đông, chỉ sinh cho TNHH 2 TV và Cổ phần (✅1).

Chạy từ thư mục gốc repo:  python scripts_and_tools/build_muc8_quyet_dinh.py   (ghi đè hai file đích)
"""
import copy
from pathlib import Path

import docx
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent.parent / "webapp_v2" / "templates"
SRC = ROOT / "Thay đổi địa chỉ và thuế TNHH 2 TV"
DST = ROOT / "Thay đổi nội dung ĐKKD"

# Biến dùng chung (đặt ở đầu tài liệu)
SETUP = [
    "{%p set lh = loai_hinh or 'tnhh_1tv' %}",
    "{%p set chu_the = 'CHỦ SỞ HỮU' if lh == 'tnhh_1tv' else ('HỘI ĐỒNG THÀNH VIÊN' if lh == 'tnhh_2tv' "
    "else 'ĐẠI HỘI ĐỒNG CỔ ĐÔNG') %}",
    "{%p set co_quan = 'Hội đồng thành viên' if lh == 'tnhh_2tv' else 'Đại hội đồng cổ đông' %}",
    "{%p set giam = hinh_thuc_thay_doi_von == 'giam' %}",
    "{%p set ns = namespace(d=0) %}",
]
DIEU = "{% set ns.d = ns.d + 1 %}Điều {{ ns.d }}."
DIEU_LE = "{%p if dkkd_selected | select('in', ['A1', 'A2', 'A3', 'A4', 'A5', 'A8']) | list %}"
NGANH = [
    ("{%p if ma_nganh %}", None),
    ("• Bổ sung các ngành, nghề kinh doanh sau:", None),
    ("{%p for n in ma_nganh %}", None),
    ("   - {{ n.ten }} (Mã ngành: {{ n.ma }}){{ ' – ngành, nghề kinh doanh chính' if n.is_main else '' }};", None),
    ("{%p endfor %}", None),
    ("{%p endif %}", None),
    ("{%p if nganh_bo %}", None),
    ("• Bỏ các ngành, nghề kinh doanh sau khỏi danh sách đã đăng ký:", None),
    ("{%p for n in nganh_bo %}", None),
    ("   - {{ n.ten }} (Mã ngành: {{ n.ma }});", None),
    ("{%p endfor %}", None),
    ("{%p endif %}", None),
]


def clone(par, runs):
    """Bản sao đoạn `par` với các run mới [(chữ, đậm)]; định dạng theo run đầu của đoạn mẫu."""
    p = copy.deepcopy(par._p)
    base = None
    for r in p.findall(qn("w:r")):
        if base is None:
            base = copy.deepcopy(r)
        p.remove(r)
    for text, bold in runs:
        r = copy.deepcopy(base)
        for t in r.findall(qn("w:t")) + r.findall(qn("w:br")):
            r.remove(t)
        rpr = r.find(qn("w:rPr"))
        if rpr is None:
            rpr = r.makeelement(qn("w:rPr"), {})
            r.insert(0, rpr)
        for tag in ("w:b", "w:bCs"):
            el = rpr.find(qn(tag))
            if el is not None:
                rpr.remove(el)
            if bold:
                rpr.append(rpr.makeelement(qn(tag), {}))
        t = r.makeelement(qn("w:t"), {})
        t.text = text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        r.append(t)
        p.append(r)
    return p


def rebuild_body(doc, template_par, items, start, end):
    """Thay các đoạn doc.paragraphs[start:end] bằng `items`: chuỗi (đoạn thường) hoặc list[(chữ, đậm)]."""
    pars = doc.paragraphs
    anchor = pars[start]._p
    for item in items:
        runs = [(item, False)] if isinstance(item, str) else item
        anchor.addprevious(clone(template_par, runs))
    for p in pars[start:end]:
        p._p.getparent().remove(p._p)


def set_run_text(par, text):
    par.runs[0].text = text
    for r in par.runs[1:]:
        r._r.getparent().remove(r._r)


def build_quyet_dinh():
    d = docx.Document(str(SRC / "02. Quyết định của Hội đồng thành viên.docx"))
    P = d.paragraphs
    body_tpl = P[7]  # "Điều 3." đậm + nội dung thường
    set_run_text(P[0], "QUYẾT ĐỊNH CỦA {{ chu_the }}\n{{ ten_cong_ty_vn }}\n(V/v thay đổi nội dung đăng ký doanh nghiệp)")
    items = [
        "- Căn cứ Luật Doanh nghiệp số 59/2020/QH14 được Quốc hội thông qua ngày 17/06/2020;",
        "- Căn cứ Nghị định số 168/2025/NĐ-CP ngày 30/06/2025 của Chính phủ về đăng ký doanh nghiệp;",
        "- Căn cứ Điều lệ {{ ten_cong_ty_vn }};",
        "{%p if lh != 'tnhh_1tv' %}",
        "- Căn cứ Biên bản họp {{ co_quan }} số: 01/2026/BBH-{{ 'HĐTV' if lh == 'tnhh_2tv' else 'ĐHĐCĐ' }}"
        " ngày {{ ngay_lap_ngan }}.",
        "{%p endif %}",
        [("QUYẾT ĐỊNH:", True)],
        # A1
        "{%p if 'A1' in dkkd_selected %}",
        [(DIEU, True), ("  Thay đổi tên doanh nghiệp:", False)],
        "• Tên công ty viết bằng tiếng Việt: {{ ten_moi_vn | upper }}",
        "{%p if ten_moi_nn %}", "• Tên công ty viết bằng tiếng nước ngoài: {{ ten_moi_nn | upper }}", "{%p endif %}",
        "{%p if ten_moi_viet_tat %}", "• Tên công ty viết tắt: {{ ten_moi_viet_tat | upper }}", "{%p endif %}",
        "{%p endif %}",
        # A2
        "{%p if 'A2' in dkkd_selected %}",
        [(DIEU, True), ("  Thay đổi địa chỉ trụ sở chính của Công ty đến địa chỉ mới: {{ dia_chi_moi_so_nha }}, "
                        "{{ dia_chi_moi_xa_phuong }}, {{ dia_chi_moi_tinh_thanh }}.", False)],
        "{%p endif %}",
        # A3
        "{%p if 'A3' in dkkd_selected and lh == 'tnhh_2tv' %}",
        [(DIEU, True), ("  Thông qua việc thay đổi thành viên Công ty. Danh sách thành viên và phần vốn góp của từng "
                        "thành viên sau khi thay đổi theo Danh sách thành viên kèm theo hồ sơ.", False)],
        "{%p endif %}",
        # A4
        "{%p if 'A4' in dkkd_selected %}",
        [(DIEU, True), ("  {{ 'Giảm' if giam else 'Tăng' }} vốn điều lệ của Công ty từ {{ von_cu_so }} đồng "
                        "({{ von_cu_chu }}) {{ 'xuống' if giam else 'lên' }} {{ von_dieu_le_so }} đồng "
                        "({{ von_dieu_le_chu }}).", False)],
        "{%p if lh == 'tnhh_2tv' %}",
        "Phần vốn góp, tỷ lệ phần vốn góp của các thành viên sau khi thay đổi theo Danh sách thành viên kèm theo hồ sơ.",
        "{%p endif %}",
        "{%p if lh == 'cp' %}", "Mệnh giá cổ phần: {{ menh_gia_co_phan }} đồng.", "{%p endif %}",
        "{%p endif %}",
        # A5
        "{%p if 'A5' in dkkd_selected %}",
        [(DIEU, True), ("  Thay đổi ngành, nghề kinh doanh của Công ty:", False)],
        *[t for t, _ in NGANH],
        "{%p endif %}",
        # A8
        "{%p if 'A8' in dkkd_selected %}",
        [(DIEU, True), ("  Thay đổi người đại diện theo pháp luật của Công ty: miễn nhiệm {{ ddpl_cu_danh_xung | lower }} "
                        "{{ ddpl_cu_ho_ten }} (Số định danh cá nhân: {{ ddpl_cu_so_cccd }}); bổ nhiệm "
                        "{{ ddpl_danh_xung | lower }} {{ ddpl_ho_ten }} (Số định danh cá nhân: {{ ddpl_so_cccd }}) giữ chức "
                        "danh Giám đốc, là người đại diện theo pháp luật của Công ty.", False)],
        "{%p endif %}",
        # Điều lệ, giao thực hiện, hiệu lực
        DIEU_LE,
        [(DIEU, True), ("  Sửa đổi, bổ sung các điều khoản tương ứng trong Điều lệ Công ty theo các nội dung thay đổi "
                        "tại Quyết định này.", False)],
        "{%p endif %}",
        [(DIEU, True), ("  Giao {{ ddpl_danh_xung | lower }} {{ ddpl_ho_ten }} – Người đại diện theo pháp luật của Công ty "
                        "chịu trách nhiệm thực hiện các thủ tục đăng ký thay đổi nội dung đăng ký doanh nghiệp tại "
                        "{{ phong_dkkd }} theo quy định của pháp luật.", False)],
        [(DIEU, True), ("  Quyết định này có hiệu lực kể từ ngày ký. {{ 'Chủ sở hữu, Giám đốc' if lh == 'tnhh_1tv' "
                        "else ('Các thành viên Hội đồng thành viên, Giám đốc' if lh == 'tnhh_2tv' else "
                        "'Các cổ đông, Hội đồng quản trị, Giám đốc') }} và các cá nhân, bộ phận có liên quan chịu "
                        "trách nhiệm thi hành Quyết định này.", False)],
    ]
    rebuild_body(d, body_tpl, items, 1, len(P))
    # Biến dùng chung: đầu tài liệu (trước cả bảng tiêu đề, nơi dùng `lh` cho số văn bản)
    first = d.element.body[0]
    for s in SETUP:
        first.addprevious(clone(body_tpl, [(s, False)]))
    # Bảng tiêu đề: số văn bản theo loại hình (dòng địa danh, ngày đã có sẵn)
    set_run_text(d.tables[0].rows[1].cells[0].paragraphs[0],
                 "Số: 01/2026/QĐ-{{ 'CSH' if lh == 'tnhh_1tv' else ('HĐTV' if lh == 'tnhh_2tv' else 'ĐHĐCĐ') }}")
    # Bảng ký
    noi_nhan, ky = d.tables[1].rows[0].cells
    set_run_text(noi_nhan.paragraphs[0], "Nơi nhận:\n- Như Điều {{ ns.d }};\n- Cơ quan ĐKKD {{ tinh_thanh_dkkd }};\n"
                                         "- Lưu: VT, HS.")
    # Người ký: Chủ sở hữu / Chủ tịch Hội đồng thành viên / Chủ tịch Hội đồng quản trị (anh xác nhận 08/11/2026)
    set_run_text(ky.paragraphs[0], "{{ 'CHỦ SỞ HỮU CÔNG TY' if lh == 'tnhh_1tv' else 'T/M ' ~ chu_the }}\n"
                                   "{{ '' if lh == 'tnhh_1tv' else ('CHỦ TỊCH HỘI ĐỒNG THÀNH VIÊN' if lh == 'tnhh_2tv' "
                                   "else 'CHỦ TỊCH HỘI ĐỒNG QUẢN TRỊ') }}\n(Ký, ghi rõ họ tên và đóng dấu)\n\n\n\n\n"
                                   "{{ chu_tich_ho_ten | upper }}")
    d.save(str(DST / "03. Quyết định.docx"))


def build_bien_ban():
    d = docx.Document(str(SRC / "03. Biên bản họp Hội đồng thành viên.docx"))
    P = d.paragraphs
    body_tpl = P[16]  # "• Tán thành:" đậm + thường
    set_run_text(P[0], "BIÊN BẢN HỌP {{ chu_the }}\n{{ ten_cong_ty_vn }}\n(V/v thay đổi nội dung đăng ký doanh nghiệp)")
    set_run_text(P[1], "Hôm nay, vào hồi 08 giờ 30 phút, {{ ngay_lap }}, tại trụ sở chính {{ ten_cong_ty_vn }}, "
                       "{{ co_quan }} đã tổ chức cuộc họp với các nội dung chi tiết như sau:")
    # Người dự họp: khi đổi thành viên (A3) là danh sách TRƯỚC khi thay đổi (tv_cu), ngược lại là thanh_vien
    set_run_text(P[3], "{%p for tv in ds %}")
    P[4].runs[0].text = "{{ loop.index }}. {{ tv.gioi_tinh | danh_xung }} {{ tv.ho_ten | upper }}"
    set_run_text(P[6], "Tổng số {{ ai }} dự họp: {{ '%02d' % (ds|length) }}/{{ '%02d' % (ds|length) }} "
                       "{{ ai }}, đại diện cho 100% tổng số {{ von }} của Công ty.")
    set_run_text(P[7], "Chủ tọa cuộc họp: {{ chu_tich_gioi_tinh | danh_xung }} {{ chu_tich_ho_ten | upper }} — "
                       "{{ 'Chủ tịch Hội đồng thành viên' "
                       "if lh == 'tnhh_2tv' else 'Chủ tịch Hội đồng quản trị' }}.")
    # Thư ký: người dự họp đầu tiên khác chủ tọa (không viết "{}" trong thẻ {%p: docxtpl đọc nhầm)
    set_run_text(P[8], "Thư ký cuộc họp: {{ tk.gioi_tinh | danh_xung }} {{ tk.ho_ten | upper }} — {{ ai | capitalize }}.")
    item = "{% set ns.d = ns.d + 1 %}{{ ns.d }}. "
    items = [
        "{%p if 'A1' in dkkd_selected %}",
        item + "Thay đổi tên doanh nghiệp thành: {{ ten_moi_vn | upper }}{{ ' (tên tiếng nước ngoài: ' ~ "
               "(ten_moi_nn | upper) ~ ')' if ten_moi_nn else '' }}.",
        "{%p endif %}",
        "{%p if 'A2' in dkkd_selected %}",
        item + "Thay đổi địa chỉ trụ sở chính đến địa chỉ mới: {{ dia_chi_moi_so_nha }}, {{ dia_chi_moi_xa_phuong }}, "
               "{{ dia_chi_moi_tinh_thanh }}.",
        "{%p endif %}",
        "{%p if 'A3' in dkkd_selected and lh == 'tnhh_2tv' %}",
        item + "Thay đổi thành viên Công ty; danh sách thành viên sau khi thay đổi theo Danh sách thành viên kèm theo.",
        "{%p endif %}",
        "{%p if 'A4' in dkkd_selected %}",
        item + "{{ 'Giảm' if giam else 'Tăng' }} vốn điều lệ từ {{ von_cu_so }} đồng {{ 'xuống' if giam else 'lên' }} "
               "{{ von_dieu_le_so }} đồng.",
        "{%p endif %}",
        "{%p if 'A5' in dkkd_selected %}",
        item + "Thay đổi ngành, nghề kinh doanh:",
        *[t for t, _ in NGANH],
        "{%p endif %}",
        "{%p if 'A8' in dkkd_selected %}",
        item + "Thay đổi người đại diện theo pháp luật: miễn nhiệm {{ ddpl_cu_danh_xung | lower }} {{ ddpl_cu_ho_ten }}, "
               "bổ nhiệm {{ ddpl_danh_xung | lower }} {{ ddpl_ho_ten }} giữ chức danh Giám đốc.",
        "{%p endif %}",
        DIEU_LE,
        item + "Sửa đổi, bổ sung các điều khoản tương ứng trong Điều lệ Công ty theo các nội dung thay đổi nêu trên.",
        "{%p endif %}",
        item + "Giao Người đại diện theo pháp luật ký Quyết định và tiến hành thủ tục đăng ký thay đổi tại {{ phong_dkkd }}.",
    ]
    rebuild_body(d, P[10], items, 10, 14)
    P = d.paragraphs
    for p in P:
        if p.text.startswith("Toàn thể các thành viên dự họp"):
            set_run_text(p, "Toàn thể các {{ ai }} dự họp đã tiến hành thảo luận và biểu quyết thông qua toàn bộ các "
                            "nội dung nêu trên:")
        if p.text.startswith("• Tán thành"):
            p.runs[1].text = "100% tổng số {{ von }}."
        if p.text.startswith("Cuộc họp kết thúc"):
            set_run_text(p, p.text.replace("tất cả các thành viên", "tất cả các {{ ai }}"))
        if p.text.startswith("CÁC THÀNH VIÊN DỰ HỌP KÝ TÊN"):
            set_run_text(p, p.text.replace("CÁC THÀNH VIÊN", "CÁC {{ ai | upper }}"))
    set_run_text(d.tables[0].rows[1].cells[0].paragraphs[0],
                 "Số: 01/2026/BBH-{{ 'HĐTV' if lh == 'tnhh_2tv' else 'ĐHĐCĐ' }}")
    thu_ky, chu_toa = d.tables[1].rows[0].cells
    set_run_text(thu_ky.paragraphs[0], thu_ky.paragraphs[0].text.replace("{{ thu_ky_ho_ten }}", "{{ tk.ho_ten | upper }}"))
    set_run_text(chu_toa.paragraphs[0], chu_toa.paragraphs[0].text.replace("{{ ddpl_ho_ten }}",
                                                                           "{{ chu_tich_ho_ten | upper }}"))
    set_run_text(d.tables[2].rows[0].cells[0].paragraphs[0], "{%tc for tv in ds %}")
    set_run_text(d.tables[2].rows[0].cells[1].paragraphs[0], "\n\n\n\n\n{{ tv.ho_ten | upper }}")
    title = d.element.body[0]
    for s in SETUP + ["{%p set ai = 'thành viên' if lh == 'tnhh_2tv' else 'cổ đông' %}",
                      "{%p set von = 'vốn điều lệ' if lh == 'tnhh_2tv' else 'cổ phần có quyền biểu quyết' %}",
                      "{%p set ds = tv_cu if ('A3' in dkkd_selected and lh == 'tnhh_2tv' and tv_cu) else thanh_vien %}",
                      "{%p set tk = ((ds | rejectattr('so_cccd', 'equalto', chu_tich_so_cccd) | list) or [dict()]) | first %}"]:
        title.addprevious(clone(body_tpl, [(s, False)]))
    d.save(str(DST / "04. Biên bản họp.docx"))


if __name__ == "__main__":
    build_quyet_dinh()
    build_bien_ban()
    print("Đã dựng 03. Quyết định.docx và 04. Biên bản họp.docx")
