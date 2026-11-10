"""Dựng bộ mẫu "Thành lập hộ kinh doanh" (webapp_v2/templates/Thành lập hộ kinh doanh).

Nguồn:
  - Giấy đề nghị: form mẫu nhà nước, lưu ở scripts_and_tools/nguon_mau/ho_kinh_doanh/ (không chứa dữ liệu cá nhân).
  - Giấy ủy quyền (tùy chọn --uq): file Word của một hồ sơ cũ. File này có dữ liệu người thật nên KHÔNG đưa vào repo;
    script thay thông tin Bên A và Bên B bằng biến, rồi kiểm tra không còn số định danh nào viết cứng.
    Không truyền --uq thì giữ nguyên mẫu Giấy ủy quyền đang có.

Trình bày theo hồ sơ đã điền (anh duyệt 10/11/2026): bỏ chú thích và ô đánh dấu, bảng ngành 3 cột, ngày để trống, khổ A4.

Chạy từ thư mục gốc repo (ghi đè file đích):
    python scripts_and_tools/build_ho_kinh_doanh.py [--uq "đường dẫn/Giấy ủy quyền.docx"]
Sau khi chạy: cd webapp_v2 && python -m tools.template_lint "templates/Thành lập hộ kinh doanh" && pytest tests/test_ho_kinh_doanh.py
"""
import argparse
import copy
import re
import unicodedata
import zipfile
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Mm
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parent
FORM = ROOT / "nguon_mau" / "ho_kinh_doanh" / "Giấy đề nghị đăng ký hộ kinh doanh (form gốc).docx"
DST = ROOT.parent / "webapp_v2" / "templates" / "Thành lập hộ kinh doanh"
_args = argparse.ArgumentParser(description=__doc__.split("\n")[0])
_args.add_argument("--uq", help="File .docx Giấy ủy quyền nguồn (không lưu trong repo)")
UQ = _args.parse_args().uq

DOTS = re.compile(r"[.…]{2,}")
YEAR = "{{ ngay_lap_ngan[-4:] }}"


def remove(el):
    el.getparent().remove(el)


def drop_superscripts(p):
    for r in list(p.runs):
        va = r._r.find(qn("w:rPr") + "/" + qn("w:vertAlign"))
        if va is not None and va.get(qn("w:val")) == "superscript":
            remove(r._r)


def base_run(p):
    """Bản sao run đầu (giữ phông, cỡ chữ), bỏ đậm/nghiêng/chỉ số trên."""
    src = p.runs[0]._r if p.runs else None
    r = copy.deepcopy(src) if src is not None else p._p.makeelement(qn("w:r"), {})
    for t in r.findall(qn("w:t")) + r.findall(qn("w:tab")) + r.findall(qn("w:br")):
        remove(t)
    rpr = r.find(qn("w:rPr"))
    if rpr is not None:
        for tag in ("w:b", "w:bCs", "w:i", "w:iCs", "w:vertAlign"):
            el = rpr.find(qn(tag))
            if el is not None:
                remove(el)
    return r


def set_parts(p, parts):
    """parts: [(text, 'b'|'i'|'')]. Thay toàn bộ nội dung đoạn, giữ định dạng đoạn và phông của run đầu."""
    tmpl = base_run(p)
    for r in list(p.runs):
        remove(r._r)
    for text, style in parts:
        r = copy.deepcopy(tmpl)
        rpr = r.find(qn("w:rPr"))
        if rpr is None:
            rpr = r.makeelement(qn("w:rPr"), {})
            r.insert(0, rpr)
        for flag in style:
            tag = {"b": ("w:b", "w:bCs"), "i": ("w:i", "w:iCs")}[flag]
            for t in tag:
                rpr.append(rpr.makeelement(qn(t), {}))
        for i, chunk in enumerate(text.split("\t")):
            if i:
                r.append(r.makeelement(qn("w:tab"), {}))
            if chunk:
                t = r.makeelement(qn("w:t"), {})
                t.text = chunk
                t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                r.append(t)
        p._p.append(r)


def lv(label, value, tail=""):
    parts = [(label, ""), (value, "b")]
    return parts + ([(tail, "")] if tail else [])


def a4(d):
    cp = d.core_properties  # tạo docProps/core.xml (thiếu thì docxtpl ghi trùng khi sinh)
    cp.author = cp.last_modified_by = ""
    for s in d.sections:
        s.page_width, s.page_height = Mm(210), Mm(297)


# ---------------- 01. Giấy đề nghị ----------------
d = docx.Document(str(FORM))
P, T = list(d.paragraphs), list(d.tables)
assert P[2].text.startswith("GIẤY ĐỀ NGHỊ ĐĂNG KÝ HỘ KINH DOANH")
assert P[36].text.startswith("7. Thông tin về các thành viên")

set_parts(P[1], [("{{ noi_lap }}, ngày ...... tháng ...... năm " + YEAR, "i")])
set_parts(P[3], [("Kính gửi: {{ hkd_dia_chi_xa_phuong | co_quan_hkd }}", "b")])
set_parts(P[5], lv("Tôi là: ", "{{ chu_ho_ho_ten | upper }}"))
set_parts(P[6], lv("Sinh ngày: ", "{{ chu_ho_ngay_sinh }}") + lv("\tGiới tính: ", "{{ chu_ho_gioi_tinh }}"))
remove(P[7]._p)
set_parts(P[8], lv("Số định danh cá nhân: ", "{{ chu_ho_so_cccd }}"))
set_parts(P[9], lv("Điện thoại: ", "{{ chu_ho_sdt }}") + lv("\tThư điện tử: ", "{{ chu_ho_email }}"))
# Phần kê khai thêm khi CSDL dân cư gián đoạn: để trống, bỏ dấu chấm
for p in T[0].rows[0].cells[0].paragraphs:
    for r in p.runs:
        r.text = DOTS.sub("", r.text).rstrip("\t ")
set_parts(P[13], lv("Tên hộ kinh doanh viết bằng tiếng Việt: ", "{{ ten_hkd | upper }}"))
set_parts(P[14], lv("Tên hộ kinh doanh viết bằng tiếng nước ngoài: ", "{{ ten_hkd_nn | upper }}"))
set_parts(P[15], lv("Tên hộ kinh doanh viết tắt: ", "{{ ten_hkd_viet_tat | upper }}"))
set_parts(P[17], lv("Số nhà/phòng, ngách/hẻm, ngõ/kiệt, đường/phố/đại lộ, tổ/xóm/ấp/thôn: ", "{{ hkd_dia_chi_so_nha }}"))
set_parts(P[18], lv("Xã/Phường/Đặc khu: ", "{{ hkd_dia_chi_xa_phuong }}"))
set_parts(P[19], lv("Tỉnh/Thành phố trực thuộc trung ương: ", "{{ hkd_dia_chi_tinh_thanh }}"))
set_parts(P[20], lv("Điện thoại: ", "{{ hkd_sdt }}", "\tFax: "))
set_parts(P[21], lv("Thư điện tử: ", "{{ hkd_email }}", "\tWebsite: "))
set_parts(P[22], lv("Kinh doanh tại trụ sở: ", "{{ 'Không' if kd_tai_tru_so == 'khong' else 'Có' }}"))
drop_superscripts(P[23])

# Bảng ngành: 3 cột STT | Tên ngành | Mã ngành; ngành chính ghi "(Chính)" sau mã
t1 = T[1]
for tr in t1._tbl.findall(qn("w:tr")):
    tcs = tr.findall(qn("w:tc"))
    gone = tcs[3]
    w_gone = gone.find(qn("w:tcPr") + "/" + qn("w:tcW"))
    remove(gone)
    w_keep = tcs[1].find(qn("w:tcPr") + "/" + qn("w:tcW"))
    if w_gone is not None and w_keep is not None and w_gone.get(qn("w:type")) == w_keep.get(qn("w:type")):
        w_keep.set(qn("w:w"), str(int(w_keep.get(qn("w:w"))) + int(w_gone.get(qn("w:w")))))
grid = t1._tbl.find(qn("w:tblGrid"))
cols = grid.findall(qn("w:gridCol"))
cols[1].set(qn("w:w"), str(int(cols[1].get(qn("w:w"))) + int(cols[3].get(qn("w:w")))))
remove(cols[3])
for c in t1.rows[0].cells:
    for p in c.paragraphs:
        drop_superscripts(p)
data_tr = t1.rows[1]._tr
for_tr, end_tr = copy.deepcopy(data_tr), copy.deepcopy(data_tr)
data_tr.addprevious(for_tr)
data_tr.addnext(end_tr)
rows = t1.rows
for row, texts in ((rows[1], ["{%tr for n in ma_nganh %}", "", ""]),
                   (rows[2], ["{{ loop.index }}", "{{ n.ten }}", "{{ n.ma }}{{ ' (Chính)' if n.is_main else '' }}"]),
                   (rows[3], ["{%tr endfor %}", "", ""])):
    for c, txt in zip(row.cells, texts):
        p = c.paragraphs[0]
        if not p.runs:
            p.add_run("")
        set_parts(p, [(txt, "")])

# Độ rộng cột (phần năm mươi của %): STT 9%, Tên ngành 71%, Mã ngành 20%; tên ngành căn trái
for tr in t1._tbl.findall(qn("w:tr")):
    for tc, w in zip(tr.findall(qn("w:tc")), ("450", "3550", "1000")):
        tc.find(qn("w:tcPr") + "/" + qn("w:tcW")).set(qn("w:w"), w)
for g, w in zip(t1._tbl.find(qn("w:tblGrid")).findall(qn("w:gridCol")), ("840", "6620", "1890")):
    g.set(qn("w:w"), w)
t1.rows[2].cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT

set_parts(P[25], lv("Bằng số: ", "{{ von_kinh_doanh_so | money | replace(',', '.') }} VNĐ", ";"))
chu = copy.deepcopy(P[25]._p)
P[25]._p.addnext(chu)
set_parts(Paragraph(chu, P[25]._parent), lv("Bằng chữ: ", "{{ von_kinh_doanh_so | so_thanh_chu }}"))
set_parts(P[28], lv("Số nhà/phòng, ngách/hẻm, ngõ/kiệt, đường/phố/đại lộ, tổ/xóm/ấp/thôn: ", "{{ thue_dia_chi_so_nha }}"))
set_parts(P[29], lv("Xã/Phường/Đặc khu: ", "{{ thue_dia_chi_xa_phuong }}"))
set_parts(P[30], lv("Tỉnh/Thành phố trực thuộc trung ương: ", "{{ thue_dia_chi_tinh_thanh }}"))
set_parts(P[31], [("Điện thoại: \tThư điện tử: ", "")])
set_parts(P[32], [("5.2. Ngày bắt đầu hoạt động ", ""),
                  ("(trường hợp hộ kinh doanh dự kiến bắt đầu hoạt động kể từ ngày được cấp Giấy chứng nhận đăng ký hộ "
                   "kinh doanh thì không cần kê khai nội dung này)", "i"), (": ", ""), ("{{ ngay_bat_dau_hd }}", "b")])
set_parts(P[33], [("5.3. Tổng số lao động ", ""), ("(dự kiến)", "i"), (": ", ""), ("{{ so_lao_dong }}", "b")])
set_parts(P[34], lv("5.4. Phương pháp tính thuế GTGT: ",
                    "{{ 'Phương pháp khoán' if pp_thue_gtgt == 'khoan' else 'Phương pháp kê khai' }}"))
remove(T[2]._tbl)
set_parts(P[35], [("6. Chủ thể thành lập hộ kinh doanh: Cá nhân", "b")])
remove(T[3]._tbl)
remove(P[36]._p)
remove(T[4]._tbl)
# Ô ký: bỏ "(Ký và ghi họ tên)" và chú thích
sig = T[5].rows[0].cells[-1]
for p in sig.paragraphs[1:]:
    if "Ký" in p.text:
        remove(p._p)
for p in sig.paragraphs:
    drop_superscripts(p)
a4(d)
d.save(str(DST / "01. Giấy đề nghị đăng ký hộ kinh doanh.docx"))

# ---------------- 02. Giấy ủy quyền ----------------
def put(p, text):
    p.runs[0].text = text
    for r in p.runs[1:]:
        remove(r._r)


def dedupe_zip(path):
    """File chuyển từ .doc bằng LibreOffice: python-docx ghi thêm docProps/core.xml -> giữ bản mới nhất."""
    with zipfile.ZipFile(path) as z:
        last = {info.filename: (info, z.read(info)) for info in z.infolist()}
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for info, data in last.values():
            z.writestr(info, data)


def build_uq(src):
    u = docx.Document(src)
    Q = u.paragraphs
    nfc = lambda t: unicodedata.normalize("NFC", t)  # noqa: E731
    assert nfc(Q[3].text).strip() == "GIẤY ỦY QUYỀN", Q[3].text
    assert nfc(Q[8].text).startswith("Ông/Bà:") and nfc(Q[11].text).startswith("Địa chỉ liên hệ:")
    put(Q[5], "Giấy ủy quyền này được lập và ký vào ngày ...... tháng ...... năm " + YEAR + ", giữa các bên dưới đây:")
    put(Q[8], "Ông/Bà: \t{{ chu_ho_ho_ten | upper }}")
    put(Q[9], "Số định danh cá nhân: {{ chu_ho_so_cccd }}\tGiới tính: {{ chu_ho_gioi_tinh }}")
    put(Q[10], "Ngày sinh: {{ chu_ho_ngay_sinh }}")
    put(Q[11], "Địa chỉ liên hệ: {{ chu_ho_dia_chi_so_nha }}, {{ chu_ho_dia_chi_xa_phuong }}, {{ chu_ho_dia_chi_tinh_thanh }}")
    q20 = nfc(Q[20].text)
    assert "tên dự kiến là" in q20, q20
    put(Q[20], q20.split("tên dự kiến là")[0] + "tên dự kiến là {{ ten_hkd | upper }}")
    # Ô ký Bên A: đoạn có chữ cuối cùng là họ tên người ký
    signer = [p for p in u.tables[0].rows[0].cells[-1].paragraphs if p.text.strip()][-1]
    assert nfc(signer.text).strip() != "BÊN A"
    put(signer, "{{ chu_ho_ho_ten | upper }}")
    # Bên B: thay thông tin nhân viên viết cứng bằng biến {{ uq_* }} (cấu hình dùng chung)
    import sys
    sys.path.insert(0, str(ROOT))
    from uy_quyen_dung_bien import fix_paragraph, iter_paragraphs
    for p in iter_paragraphs(u):
        fix_paragraph(p)
    a4(u)
    out = DST / "02. Giấy ủy quyền.docx"
    u.save(str(out))
    dedupe_zip(out)
    # Không còn số định danh nào của người thật
    text = "\n".join(p.text for p in docx.Document(str(out)).paragraphs)
    assert not re.findall(r"\b\d{12}\b", text), "Còn số định danh viết cứng trong Giấy ủy quyền"


if UQ:
    build_uq(UQ)
print("Đã dựng", DST.name, "(Giấy đề nghị" + (" + Giấy ủy quyền)" if UQ else "; Giấy ủy quyền giữ nguyên)"))
