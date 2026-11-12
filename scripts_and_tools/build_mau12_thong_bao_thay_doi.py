"""Dựng lại các mẫu "Giấy đề nghị đăng ký thay đổi / Thông báo thay đổi nội dung ĐKDN" từ Mẫu số 12 mới.

Nguồn: scripts_and_tools/nguon_mau/thong_tu_2026_du_thao/Mẫu số 12 ... .docx (tách bằng tach_bieu_mau_thong_tu.py).
Mỗi thủ tục giữ các phần của mẫu nó cần và điền đúng các biến thủ tục đó đang dùng (form nhập liệu không đổi).

Quyết định của anh (12/11/2026):
  1. Dòng "Doanh nghiệp có Giấy chứng nhận quyền sử dụng đất tại đảo..." giữ nguyên như form (không đánh dấu sẵn).
  2. Ô "Đề nghị Quý Cơ quan cấp Giấy xác nhận..." luôn đánh dấu X.
  3. Chức danh người ký để nguyên dòng dài như form.
  4. Bỏ: thay đổi trên cơ sở tách/sáp nhập, sửa đổi chi tiết ngành và "Lưu ý", mục C hiệu đính
     (cùng các phần app không dùng: vốn đầu tư DNTN, người đại diện theo ủy quyền, cổ đông sáng lập).
  5. Chủ sở hữu hưởng lợi: in cả hai đoạn của form.
Các nội dung đã điền sẵn ở mẫu cũ (hình thức tăng/giảm vốn, nguồn vốn, tài sản góp vốn...) giữ nguyên giá trị.

Chạy từ thư mục gốc repo (ghi đè file đích):
    python scripts_and_tools/build_mau12_thong_bao_thay_doi.py
Sau khi chạy: cd webapp_v2 && python -m tools.template_lint && UPDATE_GOLDEN=1 pytest tests/test_golden_snapshots.py
"""
import copy
import importlib.util
import re
import unicodedata
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "nguon_mau" / "thong_tu_2026_du_thao" / \
    "Mẫu số 12 - Giấy đề nghị đăng ký thay đổi - Thông báo thay đổi nội dung đăng ký doanh nghiệp.docx"
TPL = ROOT.parent / "webapp_v2" / "templates"

_spec = importlib.util.spec_from_file_location("tach", ROOT / "tach_bieu_mau_thong_tu.py")
tach = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tach)

DOTS = re.compile(r"[.…]{2,}")
BLANK = re.compile(r"[\s.…/]*")  # chỗ điền tay: chấm, "……/……/……"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
DATE = "{{ noi_lap }}, ngày ...... tháng ...... năm {{ ngay_lap_ngan[-4:] }}"

# Các phần của Mẫu 12: (tên, chuỗi nhận diện đầu phần). Phần kéo dài tới trước phần kế tiếp.
PARTS = [
    ("HEAD", "MẪUSỐ12"),
    ("A", "A.ĐĂNGKÝTHAYĐỔINỘIDUNG"),
    ("TACH", "DOANHNGHIỆPĐĂNGKÝTHAYĐỔITRÊNCƠSỞ"),
    ("QPAN", "-DOANHNGHIỆPCÓGIẤYCHỨNGNHẬNQUYỀNSỬDỤNGĐẤT"),
    ("TEN", "ĐĂNGKÝTHAYĐỔITÊNDOANHNGHIỆP"),
    ("DIACHI", "ĐĂNGKÝTHAYĐỔIĐỊACHỈTRỤSỞCHÍNH"),
    ("THANHVIEN", "ĐĂNGKÝTHAYĐỔITHÀNHVIÊNCÔNGTYTNHH"),
    ("VON", "ĐĂNGKÝTHAYĐỔIVỐNĐIỀULỆ"),
    ("NGANH", "THÔNGBÁOTHAYĐỔINGÀNH,NGHỀKINHDOANH"),
    ("DNTN", "ĐĂNGKÝTHAYĐỔIVỐNĐẦUTƯ"),
    ("UYQ", "THÔNGBÁOTHAYĐỔINGƯỜIĐẠIDIỆNTHEOỦYQUYỀN"),
    ("CODONG", "THÔNGBÁOTHAYĐỔICỔĐÔNGSÁNGLẬP"),
    ("THUE", "THÔNGBÁOTHAYĐỔITHÔNGTINĐĂNGKÝTHUẾ"),
    ("CSHHL", "THÔNGBÁOTHAYĐỔITHÔNGTINVỀCHỦSỞHỮUHƯỞNGLỢI"),
    ("B", "B.BỔSUNG,CẬPNHẬT"),
    ("C", "C.ĐỀNGHỊHIỆUĐÍNH"),
    ("CLOSE", "ĐỀNGHỊQUÝCƠQUANCẤPGIẤYXÁCNHẬN"),
]
ALWAYS_DROP = {"TACH", "DNTN", "UYQ", "CODONG", "C"}


# ---------------------------------------------------------------- tiện ích XML
def key(s):
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", s)).upper()


def text(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def remove(el):
    el.getparent().remove(el)


def text_runs(p):
    """Các run trực tiếp chỉ chứa chữ (không phải hình vẽ / ô đánh dấu / chú thích)."""
    out = []
    for r in p.iterchildren(qn("w:r")):
        if r.find(qn("w:t")) is not None and r.find(qn("w:drawing")) is None and \
                r.find(MC + "AlternateContent") is None and r.find(qn("w:footnoteReference")) is None:
            out.append(r)
    return out


def plain_run(p, bold=False):
    """Run mới mang phông của run chữ đầu tiên trong đoạn, bỏ đậm/nghiêng/chỉ số trên."""
    runs = text_runs(p)
    r = copy.deepcopy(runs[0]) if runs else p.makeelement(qn("w:r"), {})
    for c in list(r):
        if c.tag != qn("w:rPr"):
            remove(c)
    rpr = r.find(qn("w:rPr"))
    if rpr is not None:
        for tag in ("w:b", "w:bCs", "w:i", "w:iCs", "w:vertAlign", "w:u"):
            for el in rpr.findall(qn(tag)):
                remove(el)
    if bold:
        if rpr is None:
            rpr = r.makeelement(qn("w:rPr"), {})
            r.insert(0, rpr)
        rpr.append(rpr.makeelement(qn("w:b"), {}))
    return r


def put_text(r, s):
    t = r.makeelement(qn("w:t"), {})
    t.text = s
    t.set(XML_SPACE, "preserve")
    r.append(t)
    return r


def set_text(p, s, bold=None):
    """Thay toàn bộ chữ của đoạn (giữ hình vẽ, định dạng đoạn và phông run đầu)."""
    runs = text_runs(p)
    if bold is None:
        bold = bool(runs) and runs[0].find(f"{qn('w:rPr')}/{qn('w:b')}") is not None
    r = put_text(plain_run(p, bold), s)
    for old in runs:
        remove(old)
    ppr = p.find(qn("w:pPr"))
    if ppr is not None:
        ppr.addnext(r)
    else:
        p.insert(0, r)


def fill(p, label, value):
    """Chèn `value` ngay sau nhãn `label` trong đoạn; xóa dấu chấm điền tay ngay sau nhãn."""
    runs = text_runs(p)
    full = "".join(text(r) for r in runs)
    pos = key(full).find(key(label))
    assert pos >= 0, f"Không thấy nhãn {label!r} trong {full!r}"
    # vị trí kết thúc nhãn trong chuỗi gốc (bỏ qua khoảng trắng như key())
    need, end = len(key(label)) + pos, 0
    count = 0
    for i, ch in enumerate(unicodedata.normalize("NFC", full)):
        if not ch.isspace():
            count += 1
        if count == need:
            end = i + 1
            break
    # tách run chứa vị trí `end`
    seen = 0
    for r in runs:
        t = r.find(qn("w:t"))
        s = t.text or ""
        if seen + len(s) >= end:
            cut = end - seen
            head, tail = s[:cut], s[cut:]
            tail = "" if BLANK.fullmatch(tail) else DOTS.sub("", tail)
            t.text, t_tail = head, tail
            t.set(XML_SPACE, "preserve")
            new = put_text(plain_run(p), " " + value)
            r.addnext(new)
            if t_tail.strip():
                rest = copy.deepcopy(r)
                rest.find(qn("w:t")).text = t_tail
                new.addnext(rest)
            # xóa dấu chấm (cả "……/……/……") ở các run phía sau; tab kẻ chấm chỉ xóa khi sau đó không còn chữ
            later = []
            after = False
            for r2 in list(p.iterchildren(qn("w:r"))):
                if after:
                    later.append(r2)
                after = after or r2 is new
            for r2 in later:
                for t2 in r2.findall(qn("w:t")):
                    t2.text = "" if BLANK.fullmatch(t2.text or "") else DOTS.sub("", t2.text or "")
            has_more = any((t2.text or "").strip() for r2 in later for t2 in r2.findall(qn("w:t")))
            after = False
            for r2 in list(p.iterchildren(qn("w:r"))):
                if after:
                    if not has_more:
                        for tab in r2.findall(qn("w:tab")):
                            remove(tab)
                    if r2.find(qn("w:t")) is not None and not (r2.find(qn("w:t")).text or "").strip() and \
                            len(r2) <= 2 and r2.find(qn("w:footnoteReference")) is None:
                        remove(r2)
                after = after or r2 is new
            return
        seen += len(s)
    raise AssertionError(label)


def para_by(el, prefix):
    for p in el.iter(qn("w:p")):
        if key(text(p)).startswith(key(prefix)):
            return p
    raise AssertionError(f"Không thấy đoạn {prefix!r}")


def new_par_like(p, s="", bold=False):
    q = p.makeelement(qn("w:p"), {})
    ppr = p.find(qn("w:pPr"))
    if ppr is not None:
        q.append(copy.deepcopy(ppr))
        num = q.find(f"{qn('w:pPr')}/{qn('w:numPr')}")
        if num is not None:
            remove(num)
    if s:
        q.append(put_text(plain_run(p, bold), s))
    return q


def tag_par(anchor, s, before=True):
    """Đoạn chỉ chứa thẻ docxtpl ({%p ... %}), chèn trước/sau phần tử anchor."""
    q = anchor.makeelement(qn("w:p"), {})
    q.append(put_text(q.makeelement(qn("w:r"), {}), s))
    (anchor.addprevious if before else anchor.addnext)(q)
    return q


def cell_set(cell_el, s):
    """Ghi chữ vào ô bảng (đoạn đầu), mang phông của chữ trong ô bên cạnh nếu ô trống."""
    p = cell_el.find(qn("w:p"))
    if text_runs(p):
        set_text(p, s, bold=False)
        return
    row = cell_el.getparent()
    ref = next((q for q in row.iter(qn("w:p")) if text_runs(q)), p)
    r = put_text(plain_run(ref), s)
    p.append(r)


def rows(tbl):
    return [[c for c in tr.iterchildren(qn("w:tc"))] for tr in tbl.iterchildren(qn("w:tr"))]


def tick(p):
    """Biến ô vuông (hình chữ nhật) đầu tiên trong đoạn thành ô có chữ X."""
    ac = p.find(".//" + MC + "AlternateContent")
    wsp = ac.find(f".//{{http://schemas.microsoft.com/office/word/2010/wordprocessingShape}}wsp")
    ns = "{http://schemas.microsoft.com/office/word/2010/wordprocessingShape}"
    body = wsp.find(ns + "bodyPr")
    for k in ("lIns", "tIns", "rIns", "bIns"):
        body.set(k, "0")
    body.set("anchor", "ctr")
    cnv = wsp.find(ns + "cNvSpPr")
    cnv.set("txBox", "1")
    txbx = wsp.makeelement(ns + "txbx", {})
    content = txbx.makeelement(qn("w:txbxContent"), {})
    q = content.makeelement(qn("w:p"), {})
    ppr = q.makeelement(qn("w:pPr"), {})
    jc = ppr.makeelement(qn("w:jc"), {qn("w:val"): "center"})
    ppr.append(jc)
    q.append(ppr)
    r = q.makeelement(qn("w:r"), {})
    rpr = r.makeelement(qn("w:rPr"), {})
    rpr.append(rpr.makeelement(qn("w:b"), {}))
    r.append(rpr)
    q.append(put_text(r, "X"))
    content.append(q)
    txbx.append(content)
    body.addprevious(txbx)
    fb = ac.find(MC + "Fallback")
    if fb is not None:
        remove(fb)


def drop_page_breaks(el):
    for b in list(el.iter(qn("w:br"))):
        if b.get(qn("w:type")) == "page":
            remove(b)
    for b in list(el.iter(qn("w:pageBreakBefore"))):
        remove(b)


def drop_footnote_ref(p):
    for r in list(p.iterchildren(qn("w:r"))):
        if r.find(qn("w:footnoteReference")) is not None:
            remove(r)


# ---------------------------------------------------------------- khung chung
class Form:
    def __init__(self):
        self.doc = docx.Document(str(SRC))
        body = self.doc.element.body
        self.els = [e for e in body.iterchildren() if e.tag != qn("w:sectPr")]
        starts = []
        for name, marker in PARTS:
            i = next((i for i, e in enumerate(self.els) if e.tag == qn("w:p") and key(text(e)).startswith(marker)),
                     None)
            assert i is not None, f"Không thấy phần {name}"
            starts.append(i)
        # Phần tử trống đứng ngay trước một tiêu đề phần thuộc về phần đó (ngắt trang)
        self.part = {}
        bounds = starts[1:] + [len(self.els)]
        for (name, _), s, e in zip(PARTS, starts, bounds):
            self.part[name] = self.els[s:e]
        self.head = self.els[:starts[0]] + self.part["HEAD"]

    def p(self, part, prefix):
        for e in self.part[part]:
            if e.tag == qn("w:p") and key(text(e)).startswith(key(prefix)):
                return e
        raise AssertionError(f"{part}: không thấy {prefix!r}")

    def t(self, part, prefix):
        for e in self.part[part]:
            if e.tag == qn("w:tbl") and key(text(e)).startswith(key(prefix)):
                return e
        raise AssertionError(f"{part}: không thấy bảng {prefix!r}")

    def drop(self, *els):
        for e in els:
            if e.getparent() is not None:
                remove(e)

    def drop_from(self, part, first_prefix, last_prefix=None):
        """Xóa các phần tử trong phần, từ đoạn/bảng bắt đầu bằng first_prefix đến hết last_prefix (hoặc hết phần)."""
        items = self.part[part]
        i = next(i for i, e in enumerate(items) if key(text(e)).startswith(key(first_prefix)))
        j = len(items) - 1
        if last_prefix:
            j = next(j for j, e in enumerate(items) if j >= i and key(text(e)).startswith(key(last_prefix)))
        self.drop(*items[i:j + 1])

    def common(self, signer):
        d = self.doc
        hdr = next(e for e in self.head if e.tag == qn("w:tbl"))
        cells = rows(hdr)
        set_text(cells[0][0].find(qn("w:p")), "{{ ten_cong_ty_vn }}")
        date_p = para_by(cells[1][1], "……,ngày")
        set_text(date_p, DATE)
        kg = para_by(self.doc.element.body, "Kính gửi")
        set_text(kg, "Kính gửi: {{ phong_dkkd }}")
        fill(para_by(d.element.body, "Tên doanh nghiệp (ghi bằng chữ in hoa)"),
             "Tên doanh nghiệp (ghi bằng chữ in hoa):", "{{ ten_cong_ty_vn }}")
        fill(para_by(d.element.body, "Mã số doanh nghiệp/Mã số thuế"), "Mã số doanh nghiệp/Mã số thuế:",
             "{{ ma_so_thue }}")
        close = self.p("CLOSE", "Đề nghị Quý Cơ quan cấp Giấy xác nhận")
        tick(close)
        sign = next(e for e in self.part["CLOSE"] if e.tag == qn("w:tbl"))
        cell = rows(sign)[0][-1]
        last = list(cell.iterchildren(qn("w:p")))[-1]
        title = para_by(cell, "NGƯỜI ĐẠI DIỆN")
        tr = cell.getparent()
        trpr = tr.find(qn("w:trPr"))
        if trpr is None:
            trpr = tr.makeelement(qn("w:trPr"), {})
            tr.insert(0 if tr[0].tag != qn("w:tblPrEx") else 1, trpr)
        trpr.append(trpr.makeelement(qn("w:cantSplit"), {}))  # tên người ký không bị tách sang trang sau
        anchor = last
        for _ in range(3):
            q = new_par_like(title)
            anchor.addnext(q)
            anchor = q
        anchor.addnext(new_par_like(title, "{{ %s }}" % signer, bold=True))

    def keep_only(self, parts):
        for name, _ in PARTS:
            if name not in parts:
                self.drop(*self.part[name])

    def save(self, rel):
        body = self.doc.element.body
        drop_page_breaks(body)
        # đoạn trống liên tiếp (chỗ ngắt trang cũ) gom lại còn một
        prev_empty = False
        for e in list(body.iterchildren(qn("w:p"))):
            empty = not text(e).strip() and e.find(f".//{qn('w:drawing')}") is None and \
                e.find(f"{qn('w:pPr')}/{qn('w:sectPr')}") is None
            if empty and prev_empty:
                remove(e)
            prev_empty = empty
        tach.renumber_footnotes(self.doc)
        cp = self.doc.core_properties
        cp.author = cp.last_modified_by = ""
        cp.title = ""
        out = TPL / rel
        self.doc.save(str(out))
        left = text(body)
        for bad in ("(Cơ quan đăng ký kinh doanh cấp tỉnh)", "{{ {{"):
            assert bad not in left, (rel, bad)
        print("Đã ghi", rel)


# ---------------------------------------------------------------- phần vốn
def von_fill(f, cu, moi, unit, thoi_diem, hinh_thuc, nguon_von=True):
    fill(f.p("VON", "Vốn điều lệ đã đăng ký"), "Vốn điều lệ đã đăng ký (bằng số, bằng chữ, VNĐ):",
         "{{ %s_so }} %s ({{ %s_chu }})" % (cu, unit, cu))
    fill(f.p("VON", "Vốn điều lệ sau khi thay đổi"), "Vốn điều lệ sau khi thay đổi (bằng số, bằng chữ, VNĐ):",
         "{{ %s_so }} %s ({{ %s_chu }})" % (moi, unit, moi))
    if thoi_diem:
        fill(f.p("VON", "Thời điểm thay đổi vốn"), "Thời điểm thay đổi vốn:", thoi_diem)
    fill(f.p("VON", "Hình thức tăng, giảm vốn"), "Hình thức tăng, giảm vốn:", hinh_thuc)
    total = "{{ %s_so }} %s" % (moi, unit) if unit else "{{ %s_so }}" % moi
    zero = "0" if nguon_von == "zero" else ""
    for r in rows(f.t("VON", "Loại nguồn vốn"))[1:]:
        label = key(text(r[0]))
        if label in (key("Vốn tư nhân"), key("Tổng cộng")):
            cell_set(r[1], total)
            cell_set(r[2], "100")
        elif zero:
            cell_set(r[1], zero)
            cell_set(r[2], zero)
    for r in rows(f.t("VON", "STTTài sản góp vốn"))[1:]:
        label = key(text(r[1])) if len(r) > 2 else key(text(r[0]))
        if label in (key("Đồng Việt Nam"),):
            cell_set(r[2], total)
            cell_set(r[3], "100")
        elif key(text(r[0])) == key("Tổng số"):
            cell_set(r[-2], total)
            cell_set(r[-1], "100")
        elif zero:
            cell_set(r[2], zero)
            cell_set(r[3], zero)


def co_phan_fill(f, menh_gia, so_luong, gia_tri, zero="0"):
    fill(f.p("VON", "Mệnh giá cổ phần"), "Mệnh giá cổ phần:", menh_gia)
    for r in rows(f.t("VON", "STTLoại cổ phần"))[1:]:
        if key(text(r[1])) == key("Cổ phần phổ thông") or key(text(r[0])) == key("Tổng số"):
            vals = [so_luong, gia_tri, "100"]
            for c, v in zip(r[-3:], vals):
                cell_set(c, v)
        elif zero:
            for c in r[-3:]:
                cell_set(c, zero)


def drop_von_extras(f, co_phan=False, phan_von_gop=False, giam=False):
    if not co_phan:
        f.drop_from("VON", "Thông tin về cổ phần", "STTLoại cổ phần")
    if not phan_von_gop:
        f.drop_from("VON", "2. Đăng ký thay đổi phần vốn góp", "(Đối với thành viên có phần vốn góp")
    if not giam:
        f.drop_from("VON", "Doanh nghiệp cam kết bảo đảm thanh toán đủ")


def b_lines(f, lines):
    head = f.p("B", "B. BỔ SUNG, CẬP NHẬT")
    anchor = head
    for s in lines:
        q = new_par_like(f.p("CSHHL", "Trường hợp doanh nghiệp có sự thay đổi"), s)
        anchor.addnext(q)
        anchor = q


# ---------------------------------------------------------------- từng thủ tục
def tang_von_tnhh(rel, hinh_thuc, phan_von_gop):
    f = Form()
    f.keep_only({"HEAD", "A", "QPAN", "VON", "CLOSE"})
    drop_von_extras(f, phan_von_gop=phan_von_gop)
    von_fill(f, "von_cu", "von_moi", "VNĐ", "ngày .... tháng .... năm ….", hinh_thuc, nguon_von="zero")
    f.common("ddpl_ho_ten")
    f.save(rel)


def von_cp(rel, hinh_thuc, giam):
    f = Form()
    f.keep_only({"HEAD", "A", "QPAN", "VON", "CLOSE"})
    drop_von_extras(f, co_phan=True, giam=giam)
    von_fill(f, "von_cu", "von_dieu_le", "đồng", "     /      /{{ ngay_lap_ngan[-4:] }}", hinh_thuc, nguon_von="zero")
    co_phan_fill(f, "10.000 VNĐ", "{{ so_luong_cp_moi }}", "{{ von_dieu_le_so }} đồng")
    f.common("ddpl_ho_ten")
    f.save(rel)


def bo_sung_cp(rel):
    f = Form()
    f.keep_only({"HEAD", "B", "CLOSE"})
    b_lines(f, ["Cập nhật thông tin Công ty như sau:", "Số điện thoại: {{ sdt_cong_ty }}",
                "Email: {{ email_cong_ty }}"])
    f.common("ddpl_ho_ten")
    f.save(rel)


def chuyen_nhuong_2tv():
    f = Form()
    f.keep_only({"HEAD", "A", "QPAN", "THANHVIEN", "CSHHL", "CLOSE"})
    f.common("ddpl_cu_ho_ten")
    f.save("Chuyển nhượng Công ty TNHH 2 TV/01. Thông báo bổ sung cập nhật.docx")


def nganh_tnhh_1tv():
    f = Form()
    f.keep_only({"HEAD", "A", "QPAN", "NGANH", "CLOSE"})
    f.drop_from("NGANH", "2. Bỏ ngành, nghề kinh doanh", "STTTên ngành, nghề kinh doanh được sửa đổi")
    f.drop_from("NGANH", "Lưu ý")
    f.common("ddpl_ho_ten")
    f.save("Thay đổi ngành nghề kinh doanh TNHH 1 TV/01. Thông báo bổ sung ngành nghề kinh doanh.docx")


def ktt_fill(f, gioi_tinh):
    tbl = f.t("THUE", "STTCác chỉ tiêu thông tin đăng ký thuế")
    cell = next(r[1] for r in rows(tbl) if key(text(r[1])).startswith(key("Thông tin về Kế toán trưởng")))
    fill(para_by(cell, "Họ, chữ đệm và tên Kế toán trưởng"), "Họ, chữ đệm và tên Kế toán trưởng/Phụ trách kế toán:",
         "{{ ktt_ho_ten | upper }}")
    fill(para_by(cell, "Ngày, tháng, năm sinh"), "Ngày, tháng, năm sinh:", "{{ ktt_ngay_sinh }}")
    fill(para_by(cell, "Giới tính"), "Giới tính:", gioi_tinh)
    fill(para_by(cell, "Số định danh cá nhân"), "Số định danh cá nhân:", "{{ ktt_so_cccd }}")
    fill(para_by(cell, "Điện thoại"), "Điện thoại:", "{{ ktt_sdt }}")
    return tbl


def dia_chi_fill(f, so_nha, xa, tinh, sdt, email):
    fill(f.p("DIACHI", "Số nhà/phòng"), "tổ/xóm/ấp/thôn:", so_nha)
    fill(f.p("DIACHI", "Xã/Phường/Đặc khu"), "Xã/Phường/Đặc khu:", xa)
    fill(f.p("DIACHI", "Tỉnh/Thành phố trực thuộc trung ương"), "Tỉnh/Thành phố trực thuộc trung ương:", tinh)
    if sdt:
        fill(f.p("DIACHI", "Điện thoại"), "Điện thoại:", sdt)
    if email:
        fill(f.p("DIACHI", "Thư điện tử"), "Thư điện tử (nếu có):", email)


def dia_chi_thue_tnhh_2tv():
    f = Form()
    f.keep_only({"HEAD", "A", "QPAN", "DIACHI", "THUE", "CLOSE"})
    dia_chi_fill(f, "{{ dia_chi_moi_so_nha }}", "{{ dia_chi_moi_xa_phuong }}", "{{ dia_chi_moi_tinh_thanh }}", "", "")
    tick(f.p("DIACHI", "Thư điện tử"))  # ô "Đồng thời thay đổi địa chỉ nhận thông báo thuế" (mẫu cũ: [X] Có)
    ktt_fill(f, "{{ ktt_gioi_tinh if ktt_ho_ten else '' }}")
    f.common("ddpl_ho_ten")
    f.save("Thay đổi địa chỉ và thuế TNHH 2 TV/01. Thông báo thay đổi ĐKKD và thông tin thuế.docx")


def muc8():
    """Bộ gộp "Thay đổi nội dung ĐKKD": in phần nào tùy các ô A1..A7 đã chọn."""
    f = Form()
    f.keep_only({"HEAD", "A", "QPAN", "TEN", "DIACHI", "THANHVIEN", "VON", "NGANH", "THUE", "CSHHL", "CLOSE"})
    fill(f.p("TEN", "Tên doanh nghiệp viết bằng tiếng Việt"),
         "Tên doanh nghiệp viết bằng tiếng Việt sau khi thay đổi (ghi bằng chữ in hoa):", "{{ ten_moi_vn | upper }}")
    fill(f.p("TEN", "Tên doanh nghiệp viết bằng tiếng nước ngoài"),
         "Tên doanh nghiệp viết bằng tiếng nước ngoài sau khi thay đổi (nếu có):", "{{ ten_moi_nn | upper }}")
    fill(f.p("TEN", "Tên doanh nghiệp viết tắt"), "Tên doanh nghiệp viết tắt sau khi thay đổi (nếu có):",
         "{{ ten_moi_viet_tat | upper }}")
    dia_chi_fill(f, "{{ dia_chi_moi_so_nha }}", "{{ dia_chi_moi_xa_phuong }}", "{{ dia_chi_moi_tinh_thanh }}",
                 "{{ sdt_cong_ty }}", "{{ email_cong_ty }}")
    von_fill(f, "von_cu", "von_dieu_le", "VNĐ", "{{ ngay_thay_doi_von }}",
             "{{ 'Giảm vốn điều lệ' if hinh_thuc_thay_doi_von == 'giam' else 'Tăng vốn điều lệ' }}")
    fill(f.p("VON", "Mệnh giá cổ phần"), "Mệnh giá cổ phần:", "{{ menh_gia_co_phan }}")
    # Ngành: bỏ "sửa đổi chi tiết" và "Lưu ý"; bảng ngành bỏ lặp theo nganh_bo
    f.drop_from("NGANH", "3. Sửa đổi chi tiết ngành", "STTTên ngành, nghề kinh doanh được sửa đổi")
    f.drop_from("NGANH", "Lưu ý")
    bo = f.t("NGANH", "STTTên ngành, nghề kinh doanh được bỏ")
    data = list(bo.iterchildren(qn("w:tr")))[1]
    cells = list(data.iterchildren(qn("w:tc")))
    for c, v in zip(cells, ["{{ loop.index }}", "{{ n.ten }}", "{{ n.ma }}", ""]):
        if v:
            cell_set(c, v)
    for s, before in (("{%tr for n in nganh_bo %}", True), ("{%tr endfor %}", False)):
        tr = copy.deepcopy(data)
        for i, c in enumerate(tr.iterchildren(qn("w:tc"))):
            for p in c.iterchildren(qn("w:p")):
                for r in list(p.iterchildren(qn("w:r"))):
                    remove(r)
            if i == 0:
                c.find(qn("w:p")).append(put_text(c.makeelement(qn("w:r"), {}), s))
        (data.addprevious if before else data.addnext)(tr)
    tbl = ktt_fill(f, "{{ ktt_gioi_tinh if ktt_ho_ten else '' }}")
    cell = next(r[1] for r in rows(tbl) if key(text(r[1])).startswith(key("Địa chỉ nhận thông báo thuế")))
    fill(para_by(cell, "Số nhà/phòng"), "tổ/xóm/ấp/thôn:", "{{ dia_chi_thue_so_nha or dia_chi_moi_so_nha or dia_chi_so_nha }}")
    fill(para_by(cell, "Xã/Phường/Đặc khu"), "Xã/Phường/Đặc khu:",
         "{{ dia_chi_thue_xa_phuong or dia_chi_moi_xa_phuong or dia_chi_xa_phuong }}")
    fill(para_by(cell, "Tỉnh/Thành phố"), "Tỉnh/Thành phố trực thuộc trung ương:",
         "{{ dia_chi_thue_tinh_thanh or dia_chi_moi_tinh_thanh or dia_chi_tinh_thanh }}")
    fill(para_by(cell, "Điện thoại (nếu có)"), "Điện thoại (nếu có):", "{{ sdt_cong_ty }}")
    fill(para_by(cell, "Thư điện tử"), "Thư điện tử (nếu có):", "{{ email_cong_ty }}")

    def wrap(items, cond):
        items = [e for e in items if e.getparent() is not None]
        tag_par(items[0], "{%p if " + cond + " %}")
        tag_par(items[-1], "{%p endif %}", before=False)

    def sub(part, first, last=None):
        items = f.part[part]
        i = next(i for i, e in enumerate(items) if e.getparent() is not None and key(text(e)).startswith(key(first)))
        j = i if last is None else next(j for j, e in enumerate(items) if j >= i and key(text(e)).startswith(key(last)))
        return items[i:j + 1]

    # Bọc ngoài trước, bọc trong sau (thẻ đóng của phần trong phải nằm trước thẻ đóng của phần ngoài)
    for part, cond in (("TEN", "'A1' in dkkd_selected"), ("DIACHI", "'A2' in dkkd_selected"),
                       ("THANHVIEN", "'A3' in dkkd_selected and loai_hinh == 'tnhh_2tv'"),
                       ("VON", "'A4' in dkkd_selected"), ("NGANH", "'A5' in dkkd_selected"),
                       ("THUE", "'A6' in dkkd_selected"), ("CSHHL", "'A7' in dkkd_selected")):
        wrap(f.part[part], cond)
    wrap(sub("VON", "Thông tin về cổ phần", "STTLoại cổ phần"), "loai_hinh == 'cp'")
    wrap(sub("VON", "2. Đăng ký thay đổi phần vốn góp", "(Đối với thành viên có phần vốn góp"),
         "loai_hinh == 'tnhh_2tv'")
    wrap(sub("VON", "Doanh nghiệp cam kết bảo đảm thanh toán đủ"), "hinh_thuc_thay_doi_von == 'giam'")
    wrap(sub("NGANH", "1. Bổ sung ngành", "STTTên ngành, nghề kinh doanh được bổ sung"), "ma_nganh")
    wrap(sub("NGANH", "2. Bỏ ngành", "STTTên ngành, nghề kinh doanh được bỏ"), "nganh_bo")
    f.common("ddpl_ho_ten")
    f.save("Thay đổi nội dung ĐKKD/01. Thông báo bổ sung cập nhật.docx")


if __name__ == "__main__":
    tang_von_tnhh("Tăng vốn công ty TNHH 1 TV/01. Thông báo thay đổi ĐKKD.docx",
                  "Chủ sở hữu công ty đầu tư thêm vốn", phan_von_gop=False)
    tang_von_tnhh("Tăng vốn công ty TNHH 2 TV/01. Thông báo thay đổi ĐKKD.docx",
                  "Tăng vốn góp của thành viên công ty và Tiếp nhận thêm vốn góp của thành viên mới",
                  phan_von_gop=True)
    von_cp("Tăng vốn công ty Cổ Phần/01. Thông báo thay đổi ĐKKD.docx",
           "Công ty phát hành thêm cổ phần, các cổ đông đăng ký mua theo tỷ lệ. Các cổ đông mua hết bằng tiền mặt "
           "theo phương thức thanh toán chuyển khoản.", giam=False)
    von_cp("Giảm vốn công ty Cổ Phần/01. Thông báo thay đổi ĐKKD.docx",
           "Công ty hoàn trả một phần vốn góp cho các cổ đông theo tỷ lệ sở hữu cổ phần của họ trong công ty theo "
           "quy định tại Điểm a Khoản 5 Điều 112 Luật Doanh nghiệp 2020 (Công ty đã hoạt động kinh doanh liên tục từ "
           "02 năm trở lên kể từ ngày đăng ký thành lập doanh nghiệp và bảo đảm thanh toán đủ các khoản nợ và nghĩa "
           "vụ tài sản khác sau khi đã hoàn trả cho cổ đông).", giam=True)
    bo_sung_cp("Tăng vốn công ty Cổ Phần/02. Thông báo bổ sung cập nhật.docx")
    bo_sung_cp("Giảm vốn công ty Cổ Phần/02. Thông báo bổ sung cập nhật.docx")
    chuyen_nhuong_2tv()
    nganh_tnhh_1tv()
    dia_chi_thue_tnhh_2tv()
    muc8()
