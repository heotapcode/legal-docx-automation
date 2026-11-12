"""Dựng lại "Giấy đề nghị đăng ký doanh nghiệp" của 3 thủ tục thành lập mới từ Mẫu số 2, 3, 4 mới.

Nguồn: scripts_and_tools/nguon_mau/thong_tu_2026_du_thao/Mẫu số 2|3|4 ... .docx (tách bằng tach_bieu_mau_thong_tu.py).
Giữ đúng tên biến các thủ tục đang dùng (form nhập không đổi) và giữ các ô app đã đánh dấu / điền sẵn
(Thành lập mới, Hạch toán độc lập, Khấu trừ, BHXH hàng tháng, BOT: Không, năm tài chính, số lao động, Chức danh).

Quyết định của anh (12/11/2026):
  1. Giữ các phần cho trường hợp đặc biệt (chia/tách/hợp nhất/chuyển đổi, hộ kinh doanh, cơ sở bảo trợ xã hội,
     chủ sở hữu là tổ chức, Giấy chứng nhận đăng ký đầu tư, Phụ lục Cam kết nhà đầu tư nước ngoài): để trống như form.
  2. Giữ khối "Trường hợp không có số định danh cá nhân..." (để trống).
  3. TNHH 1 TV: "Mô hình tổ chức công ty" tự đánh dấu "Chủ tịch công ty, Giám đốc hoặc Tổng Giám đốc".
  4. Bỏ đoạn "Lưu ý" về phương thức đóng bảo hiểm xã hội.
  Như Mẫu 12: bỏ chú thích cuối trang, chức danh người ký để nguyên dòng dài của form.

Chạy từ thư mục gốc repo (ghi đè file đích):
    python scripts_and_tools/build_mau234_giay_de_nghi.py
"""
import importlib.util
from pathlib import Path

import docx
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent
NGUON = ROOT / "nguon_mau" / "thong_tu_2026_du_thao"
TPL = ROOT.parent / "webapp_v2" / "templates"

_spec = importlib.util.spec_from_file_location("m12", ROOT / "build_mau12_thong_bao_thay_doi.py")
m12 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m12)
key, text, fill, set_text, cell_set, rows = m12.key, m12.text, m12.fill, m12.set_text, m12.cell_set, m12.rows
remove, new_par_like, drop_notes, put_text, plain_run = (m12.remove, m12.new_par_like, m12.drop_notes, m12.put_text,
                                                         m12.plain_run)
MC, WPS = m12.MC, "{http://schemas.microsoft.com/office/word/2010/wordprocessingShape}"


class Form:
    """Điền lần lượt theo thứ tự trong văn bản: mỗi lần tìm đoạn kế tiếp bắt đầu bằng `prefix` sau con trỏ."""

    def __init__(self, src):
        self.doc = docx.Document(str(src))
        self.body = self.doc.element.body
        self.pos = 0

    def paras(self):
        return list(self.body.iter(qn("w:p")))

    def next(self, prefix):
        ps = self.paras()
        for i in range(self.pos, len(ps)):
            if key(text(ps[i])).startswith(key(prefix)):
                self.pos = i + 1
                return ps[i]
        raise AssertionError(f"Không thấy đoạn {prefix!r} sau vị trí {self.pos}")

    def fill(self, label, value, prefix=None):
        fill(self.next(prefix or label), label, value)

    def tick_leftmost(self, label):
        """Đánh X vào ô vuông nằm bên trái nhất của dòng chứa nhãn (ô đứng trước chữ, vd "☐ Hàng tháng").
        Một số mẫu neo các ô này vào đoạn ngay trước bảng."""
        p = self.next(label)
        anc = p
        while anc is not None and anc.tag != qn("w:tbl"):
            anc = anc.getparent()
        scopes = [anc, anc.getprevious()] if anc is not None else [p]
        boxes = [ac for sc in scopes if sc is not None for ac in sc.iter(MC + "AlternateContent")
                 if ac.find(f".//{WPS}wsp") is not None]
        assert boxes, f"Không thấy ô vuông quanh {label!r}"

        def x(ac):
            off = ac.find(".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}positionH/"
                          "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}posOffset")
            return int(off.text) if off is not None else 0
        ac = min(boxes, key=x)
        shapes = list(ac.iter(f"{WPS}wsp"))
        if len(shapes) > 1:  # nhóm hình: chọn ô vuông bên trái nhất trong nhóm
            A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
            tick_ac(ac, min(shapes, key=lambda w: int(w.find(f".//{A}off").get("x"))))
        else:
            tick_ac(ac)
        # Bảng "nổi" (tblpPr) bị LibreOffice đẩy sang trang sau, tách khỏi ô vuông: chuyển thành bảng thường
        if anc is not None:
            tblpr = anc.find(qn("w:tblPr"))
            for fl in tblpr.findall(qn("w:tblpPr")):
                tblpr.remove(fl)

    def tick(self, label):
        """Đánh X vào ô vuông (hình vẽ) đầu tiên sau nhãn, trong cùng dòng bảng hoặc cùng đoạn."""
        p = self.next(label)
        scope = p
        anc = p.getparent()
        while anc is not None and anc.tag != qn("w:tr"):
            anc = anc.getparent()
        if anc is not None:
            scope = anc
        seen = False
        for el in scope.iter():
            if el is p:
                seen = True
            if seen and el.tag == MC + "AlternateContent" and el.find(f".//{WPS}wsp") is not None:
                tick_ac(el)
                return
        raise AssertionError(f"Không thấy ô vuông sau {label!r}")

    def table(self, first_cell):
        for t in self.body.iter(qn("w:tbl")):
            if key(text(t)).startswith(key(first_cell)):
                return t
        raise AssertionError(first_cell)

    def drop_paras(self, *prefixes):
        for pre in prefixes:
            remove(self.next(pre))
            self.pos -= 1  # đoạn vừa xóa không còn trong danh sách

    def save(self, rel, signer="ddpl_ho_ten"):
        sign = self.table("NGƯỜI ĐẠI DIỆN THEO PHÁP LUẬT")
        cell = rows(sign)[0][-1]
        title = m12.para_by(cell, "NGƯỜI ĐẠI DIỆN")
        tr = cell.getparent()
        trpr = tr.find(qn("w:trPr"))
        if trpr is None:
            trpr = tr.makeelement(qn("w:trPr"), {})
            tr.insert(0, trpr)
        trpr.append(trpr.makeelement(qn("w:cantSplit"), {}))
        anchor = list(cell.iterchildren(qn("w:p")))[-1]
        for _ in range(3):
            q = new_par_like(title)
            anchor.addnext(q)
            anchor = q
        anchor.addnext(new_par_like(title, "{{ %s }}" % signer, bold=True))
        drop_notes(self.body)
        m12.tach.renumber_footnotes(self.doc)
        cp = self.doc.core_properties
        cp.author = cp.last_modified_by = ""
        cp.title = ""
        self.doc.save(str(TPL / rel))
        assert "{{ {{" not in text(self.body)
        print("Đã ghi", rel)


def tick_ac(ac, wsp=None):
    """Đánh X vào ô vuông: biến hình vuông thành khung chữ có X.
    Ô vuông nằm một mình trong ô bảng được chuyển thành hình nằm trong dòng (inline): hình neo trong bảng bị
    LibreOffice đặt sai chỗ khi bảng sang trang mới."""
    tc = ac.getparent()
    while tc is not None and tc.tag != qn("w:tc"):
        tc = tc.getparent()
    if tc is not None and not text(tc).strip():
        to_inline(ac)
    wsp = wsp if wsp is not None else ac.find(f".//{WPS}wsp")
    body = wsp.find(WPS + "bodyPr")
    for k in ("lIns", "tIns", "rIns", "bIns"):
        body.set(k, "0")
    body.set("anchor", "ctr")
    wsp.find(WPS + "cNvSpPr").set("txBox", "1")
    old = wsp.find(WPS + "txbx")
    if old is not None:
        wsp.remove(old)
    txbx = wsp.makeelement(WPS + "txbx", {})
    content = txbx.makeelement(qn("w:txbxContent"), {})
    q = content.makeelement(qn("w:p"), {})
    ppr = q.makeelement(qn("w:pPr"), {})
    ppr.append(ppr.makeelement(qn("w:jc"), {qn("w:val"): "center"}))
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
        ac.remove(fb)


WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"


def to_inline(ac):
    anchor = ac.find(f".//{WP}anchor")
    if anchor is None:
        return
    inline = anchor.makeelement(WP + "inline", {"distT": "0", "distB": "0", "distL": "0", "distR": "0"})
    for tag in ("extent", "effectExtent", "docPr", "cNvGraphicFramePr"):
        el = anchor.find(WP + tag)
        if el is not None:
            inline.append(el)
    inline.append(anchor.find("{http://schemas.openxmlformats.org/drawingml/2006/main}graphic"))
    anchor.getparent().replace(anchor, inline)


# ---------------------------------------------------------------- phần dùng chung
def header(f):
    set_text(f.next("……, ngày"), "{{ noi_lap }}, ngày ...... tháng ...... năm {{ ngay_lap_ngan[-4:] }}")
    set_text(f.next("Kính gửi"), "Kính gửi: {{ phong_dkkd }}")


def person(f, p, ho_ten_label, chuc_danh=None, lien_lac="Địa chỉ liên lạc"):
    """Khối thông tin cá nhân: họ tên, ngày sinh, giới tính, số định danh, (chức danh), địa chỉ liên lạc, quốc gia."""
    f.fill(ho_ten_label, "{{ %s_ho_ten | upper }}" % p)
    f.fill("Ngày, tháng, năm sinh:", "{{ %s_ngay_sinh }}" % p)
    f.fill("Giới tính:", "{{ %s_gioi_tinh }}" % p)
    f.fill("Số định danh cá nhân:", "{{ %s_so_cccd }}" % p)
    if chuc_danh:
        f.fill("Chức danh:", chuc_danh)
    f.next(lien_lac)
    f.fill("tổ/xóm/ấp/thôn:", "{{ %s_dia_chi_so_nha }}" % p, prefix="Số nhà/phòng")
    f.fill("Xã/Phường/Đặc khu:", "{{ %s_dia_chi_xa_phuong }}" % p)
    f.fill("Tỉnh/Thành phố trực thuộc trung ương:", "{{ %s_dia_chi_tinh_thanh }}" % p)
    f.fill("Quốc gia:", "Việt Nam")


def company(f):
    f.tick("Thành lập mới")
    f.fill("Tên công ty viết bằng tiếng Việt (ghi bằng chữ in hoa):", "{{ ten_cong_ty_vn }}")
    f.fill("Tên công ty viết bằng tiếng nước ngoài (nếu có):", "{{ ten_cong_ty_en }}")
    f.fill("Tên công ty viết tắt (nếu có):", "{{ ten_cong_ty_viet_tat }}")
    f.next("3. Địa chỉ trụ sở chính")
    f.fill("tổ/xóm/ấp/thôn:", "{{ dia_chi_so_nha }}", prefix="Số nhà/phòng")
    f.fill("Xã/Phường/Đặc khu:", "{{ dia_chi_xa_phuong }}")
    f.fill("Tỉnh/Thành phố trực thuộc trung ương:", "{{ dia_chi_tinh_thanh }}")
    f.fill("Điện thoại:", "{{ sdt_cong_ty }}")
    f.fill("Thư điện tử (nếu có):", "{{ email_cong_ty }}")
    nganh_widths(f)


def nganh_widths(f):
    """Bảng ngành của form để cột "Tên ngành" hẹp, tên ngành dài bị xuống dòng nhiều: chia lại độ rộng cột
    (STT 8%, Tên ngành 50%, Mã ngành 14%, Ngành chính 28%), tổng độ rộng giữ nguyên."""
    t = f.table("STTTên ngànhMã ngành")
    grid = t.find(qn("w:tblGrid"))
    cols = grid.findall(qn("w:gridCol"))
    assert len(cols) == 4, len(cols)
    total = sum(int(c.get(qn("w:w"))) for c in cols)
    widths = [round(total * r) for r in (0.08, 0.50, 0.14)]
    widths.append(total - sum(widths))
    for c, w in zip(cols, widths):
        c.set(qn("w:w"), str(w))
    for tr in t.iterchildren(qn("w:tr")):
        for tc, w in zip(tr.iterchildren(qn("w:tc")), widths):
            tcw = tc.find(f"{qn('w:tcPr')}/{qn('w:tcW')}")
            if tcw is not None:
                tcw.set(qn("w:w"), str(w))
                tcw.set(qn("w:type"), "dxa")


def von(f):
    f.fill("Vốn điều lệ (bằng số; VNĐ):", "{{ von_dieu_le_so }} đồng")
    f.fill("Vốn điều lệ (bằng chữ; VNĐ):", "{{ von_dieu_le_chu }} đồng")
    for r in rows(f.table("Loại nguồn vốn"))[1:]:
        label = key(text(r[0]))
        full = label in (key("Vốn tư nhân"), key("Tổng cộng"))
        cell_set(r[1], "{{ von_dieu_le_so }}" if full else "0")
        cell_set(r[2], "100" if full else "0")


def tai_san(f):
    for r in rows(f.table("STTTài sản góp vốn"))[1:]:
        dvn = len(r) > 3 and key(text(r[1])) == key("Đồng Việt Nam")
        tong = key(text(r[0])) == key("Tổng số")
        cells = r[-2:]
        cell_set(cells[0], "{{ von_dieu_le_so }}" if dvn or tong else "0")
        cell_set(cells[1], "100" if dvn or tong else "0")


def thue(f, lao_dong, nam_tai_chinh):
    f.tick("Hạch toán độc lập")
    if nam_tai_chinh:
        set_text(f.next("Áp dụng từ ngày"), "Áp dụng từ ngày " + nam_tai_chinh, bold=False)
    f.fill("Tổng số lao động (dự kiến):", lao_dong)
    f.tick("Không")  # Hoạt động theo dự án BOT...: Không
    f.tick("Khấu trừ")
    # Ô vuông BHXH neo vào đoạn phía trên bảng: giữ tiêu đề, đoạn đó và bảng cùng một trang
    pos = f.pos
    for pre in ("Thông tin về việc đóng bảo hiểm xã hội", "Phương thức đóng bảo hiểm xã hội"):
        q = next(x for x in f.paras()[pos:] if pre in text(x))
        ppr = q.find(qn("w:pPr"))
        if ppr is None:
            ppr = q.makeelement(qn("w:pPr"), {})
            q.insert(0, ppr)
        ppr.insert(0, ppr.makeelement(qn("w:keepNext"), {}))
    f.tick_leftmost("Hàng tháng")
    f.drop_paras("Lưu ý", "- Doanh nghiệp đăng ký ngành, nghề kinh doanh chính là nông nghiệp",
                 "- Doanh nghiệp đăng ký ngành, nghề kinh doanh chính khác")


# ---------------------------------------------------------------- từng mẫu
def tnhh_1tv():
    f = Form(NGUON / "Mẫu số 2 - Giấy đề nghị đăng ký doanh nghiệp - Công ty TNHH một thành viên.docx")
    header(f)
    person(f, "ddpl", "Tôi là (ghi họ tên bằng chữ in hoa):", lien_lac="Địa chỉ liên lạc (chỉ kê khai")
    company(f)
    f.next("5. Chủ sở hữu")
    person(f, "ddpl", "Họ, chữ đệm và tên chủ sở hữu (ghi bằng chữ in hoa):")
    f.tick("Chủ tịch công ty, Giám đốc hoặc Tổng Giám đốc")
    von(f)
    tai_san(f)
    f.next("9. Người đại diện theo pháp luật")
    person(f, "ddpl", "Họ, chữ đệm và tên (ghi bằng chữ in hoa):", chuc_danh="Giám đốc")
    thue(f, "02", None)
    f.save("Thành lập mới công ty TNHH 1 TV/01. Giấy đề nghị.docx")


def tnhh_2tv():
    f = Form(NGUON / "Mẫu số 3 - Giấy đề nghị đăng ký doanh nghiệp - Công ty TNHH hai thành viên trở lên.docx")
    header(f)
    person(f, "ddpl", "Tôi là (ghi họ tên bằng chữ in hoa):", lien_lac="Địa chỉ liên lạc (chỉ kê khai")
    company(f)
    von(f)
    f.next("8. Người đại diện theo pháp luật")
    person(f, "ddpl", "Họ, chữ đệm và tên (ghi bằng chữ in hoa):", chuc_danh="Giám đốc")
    thue(f, "04", "01/01 đến ngày 31/12")
    f.save("Thành lập mới công ty TNHH 2 TV/01. Giấy đề nghị.docx")


def co_phan():
    f = Form(NGUON / "Mẫu số 4 - Giấy đề nghị đăng ký doanh nghiệp - Công ty cổ phần.docx")
    header(f)
    person(f, "ddpl", "Tôi là (ghi họ tên bằng chữ in hoa):", lien_lac="Địa chỉ liên lạc (chỉ kê khai")
    company(f)
    von(f)
    f.fill("Mệnh giá cổ phần (VNĐ):", "10.000")
    for r in rows(f.table("STTLoại cổ phầnSố lượng"))[1:]:
        main = key(text(r[1])) == key("Cổ phần phổ thông") or key(text(r[0])) == key("Tổng số")
        vals = ["{{ so_luong_cp_moi }}", "{{ von_dieu_le_so }}", "100"] if main else ["0", "0", "0"]
        for c, v in zip(r[-3:], vals):
            cell_set(c, v)
    for r in rows(f.table("STTLoại cổ phần được quyền chào bán"))[1:]:
        main = key(text(r[1])) == key("Cổ phần phổ thông") or key(text(r[0])) == key("Tổng số")
        cell_set(r[-1], "{{ so_luong_cp_moi }}" if main else "0")
    f.next("10. Người đại diện theo pháp luật")
    person(f, "ddpl", "Họ, chữ đệm và tên (ghi bằng chữ in hoa):", chuc_danh="Giám đốc")
    thue(f, "04", "01/01 đến ngày 31/12")
    f.save("Thành lập mới công ty Cổ Phần/01. Giấy đề nghị.docx")


if __name__ == "__main__":
    tnhh_1tv()
    tnhh_2tv()
    co_phan()
