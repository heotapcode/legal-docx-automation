"""Dựng lại "Danh sách chủ sở hữu hưởng lợi của doanh nghiệp" của 8 thủ tục từ Mẫu số 10 mới.

Nguồn: scripts_and_tools/nguon_mau/thong_tu_2026_du_thao/Mẫu số 10 ... .docx (tách bằng tach_bieu_mau_thong_tu.py).
Bảng 18 cột của form giữ nguyên, để một dòng dữ liệu trống làm khuôn; danh sách được điền khi sinh hồ sơ
(services/docx_fillers.py: populate_cshhl, khóa "post": fill_cshhl_table / fill_cshhl_table_cp).

Quyết định của anh (12/11/2026):
  1. Chỉ ghi thành viên/cổ đông có tỷ lệ từ 25% trở lên.
  2. Cột 18 "Người quản lý doanh nghiệp" để trống.
  Bộ TNHH 1 TV (không có danh sách thành viên): dòng chủ sở hữu điền sẵn từ thông tin người đại diện, 100%.
  Chuyển nhượng TNHH 2 TV: người ký trước dùng biến không có dữ liệu (in trống), nay là người đại diện theo pháp luật.
  Tỷ lệ ghi vào cột "Trực tiếp" và "Tổng" (TNHH: nhóm vốn điều lệ; cổ phần: nhóm cổ phần có quyền biểu quyết).
  Chữ ký để nguyên dòng dài của form; bỏ chú thích cuối trang.

Chạy từ thư mục gốc repo (ghi đè file đích):
    python scripts_and_tools/build_mau10_cshhl.py
"""
import importlib.util
from pathlib import Path

import docx
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "nguon_mau" / "thong_tu_2026_du_thao" / "Mẫu số 10 - Danh sách chủ sở hữu hưởng lợi của doanh nghiệp.docx"
TPL = ROOT.parent / "webapp_v2" / "templates"

_spec = importlib.util.spec_from_file_location("m12", ROOT / "build_mau12_thong_bao_thay_doi.py")
m12 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m12)

# (file đích, biến tên người ký, điền sẵn dòng chủ sở hữu từ thông tin người đại diện)
# Bộ TNHH 1 TV không có danh sách thành viên: chủ sở hữu (100%) là người đại diện, điền sẵn trong mẫu như bản cũ.
TARGETS = [
    ("Chuyển nhượng Công ty TNHH 2 TV/04. Danh sách chủ sở hữu hưởng lợi.docx", "ddpl_ho_ten"),
    ("Chuyển nhượng công ty TNHH 1 TV/04. Danh sách chủ sở hữu hưởng lợi.docx", "ddpl_ho_ten", True),
    ("Chuyển đổi loại hình 1TV sang 2 TV/05. Danh sách chủ sở hữu hưởng lợi.docx", "ddpl_ho_ten"),
    ("Thay đổi nội dung ĐKKD/06. Danh sách chủ sở hữu hưởng lợi.docx", "ddpl_ho_ten"),
    ("Thành lập mới công ty Cổ Phần/05. Danh sách chủ sở hữu hưởng lợi.docx", "ddpl_ho_ten"),
    ("Thành lập mới công ty TNHH 1 TV/04. Danh sách chủ sở hữu hưởng lợi.docx", "ddpl_ho_ten", True),
    ("Thành lập mới công ty TNHH 2 TV/05. Danh sách chủ sở hữu hưởng lợi.docx", "ddpl_ho_ten"),
    ("Tăng vốn công ty TNHH 2 TV/05. Danh sách chủ sở hữu hưởng lợi.docx", "ddpl_ho_ten"),
]


OWNER_ROW = ["1", "{{ ddpl_ho_ten | upper }}", "{{ ddpl_ngay_sinh }}", "{{ ddpl_gioi_tinh }}",
             "Số định danh cá nhân: {{ ddpl_so_cccd }}", "Việt Nam", "Kinh", "{{ ddpl_dia_chi_day_du }}",
             "100%", "", "100%"]


# Độ rộng tương đối 18 cột: form để cột họ tên, giấy tờ, địa chỉ rất hẹp (họ tên xuống dòng từng chữ).
# Nới các cột này, thu hẹp các cột tỷ lệ; tổng độ rộng bảng giữ nguyên.
WIDTHS = [500, 1500, 1000, 600, 1650, 750, 650, 2300, 650, 650, 700, 650, 650, 700, 850, 950, 850, 850]


def set_widths(tbl):
    grid = tbl.find(qn("w:tblGrid"))
    cols = grid.findall(qn("w:gridCol"))
    assert len(cols) == len(WIDTHS), len(cols)
    total = sum(int(c.get(qn("w:w"))) for c in cols)
    w = [round(total * x / sum(WIDTHS)) for x in WIDTHS]
    w[-1] += total - sum(w)
    for c, v in zip(cols, w):
        c.set(qn("w:w"), str(v))
    for tr in tbl.iterchildren(qn("w:tr")):
        pos = 0
        for tc in tr.iterchildren(qn("w:tc")):
            tcpr = tc.find(qn("w:tcPr"))
            span_el = tcpr.find(qn("w:gridSpan")) if tcpr is not None else None
            span = int(span_el.get(qn("w:val"))) if span_el is not None else 1
            tcw = tcpr.find(qn("w:tcW")) if tcpr is not None else None
            if tcw is not None:
                tcw.set(qn("w:w"), str(sum(w[pos:pos + span])))
                tcw.set(qn("w:type"), "dxa")
            pos += span


def small_font(tbl, half_points="20"):
    """Chữ trong bảng cỡ 10 để 18 cột không xuống dòng từng chữ (form để 12-13)."""
    for p in tbl.iter(qn("w:p")):
        ppr = p.find(qn("w:pPr"))
        if ppr is None:
            ppr = p.makeelement(qn("w:pPr"), {})
            p.insert(0, ppr)
        mark = ppr.find(qn("w:rPr"))
        if mark is None:
            mark = ppr.makeelement(qn("w:rPr"), {})
            ppr.append(mark)
        rprs = [mark] + [r.find(qn("w:rPr")) for r in p.iterchildren(qn("w:r"))]
        for r in p.iterchildren(qn("w:r")):
            if r.find(qn("w:rPr")) is None:
                rp = r.makeelement(qn("w:rPr"), {})
                r.insert(0, rp)
                rprs.append(rp)
        for rpr in filter(lambda x: x is not None, rprs):
            for tag in ("w:sz", "w:szCs"):
                for el in rpr.findall(qn(tag)):
                    rpr.remove(el)
                rpr.append(rpr.makeelement(qn(tag), {qn("w:val"): half_points}))


def build(rel, signer, owner=False):
    d = docx.Document(str(SRC))
    body = d.element.body
    set_widths(d.tables[0]._tbl)
    for tc in d.tables[0].rows[-1]._tr.iterchildren(qn("w:tc")):  # dòng dữ liệu: căn giữa theo chiều dọc
        tcpr = tc.find(qn("w:tcPr"))
        for v in tcpr.findall(qn("w:vAlign")):
            tcpr.remove(v)
        tcpr.append(tcpr.makeelement(qn("w:vAlign"), {qn("w:val"): "center"}))
    if owner:
        data = d.tables[0].rows[-1]
        for c, v in zip(data.cells, OWNER_ROW):
            if v:
                m12.cell_set(c._tc, v)
    small_font(d.tables[0]._tbl)
    sign = d.tables[1]
    cell = sign.rows[0].cells[0]._tc
    m12.set_text(m12.para_by(cell, "……, ngày"), "{{ noi_lap }}, ngày ...... tháng ...... năm {{ ngay_lap_ngan[-4:] }}")
    title = m12.para_by(cell, "NGƯỜI ĐẠI DIỆN")
    anchor = list(cell.iterchildren(qn("w:p")))[-1]
    for _ in range(3):
        q = m12.new_par_like(title)
        anchor.addnext(q)
        anchor = q
    anchor.addnext(m12.new_par_like(title, "{{ %s }}" % signer, bold=True))
    m12.drop_notes(body)
    m12.tach.renumber_footnotes(d)
    cp = d.core_properties
    cp.author = cp.last_modified_by = ""
    cp.title = ""
    d.save(str(TPL / rel))
    print("Đã ghi", rel)


if __name__ == "__main__":
    for t in TARGETS:
        build(*t)
