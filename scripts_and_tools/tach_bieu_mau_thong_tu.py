"""Tách file Phụ lục biểu mẫu đăng ký doanh nghiệp (một file Word gồm nhiều mẫu) thành mỗi mẫu một file .docx.

Cách tách: mỗi mẫu bắt đầu ở tiêu đề của nó, lùi về ngay sau ngắt trang / ngắt section gần nhất phía trước, và kết thúc
ngay trước mẫu kế tiếp. Mỗi file giữ nguyên định dạng, khổ giấy (kể cả trang ngang), chú thích cuối trang của bản gốc.

    python scripts_and_tools/tach_bieu_mau_thong_tu.py <file phụ lục.docx> [thư mục đích]

Mặc định ghi vào scripts_and_tools/nguon_mau/thong_tu_2026_du_thao/. Chạy lại được (ghi đè).
"""
import copy
import re
import sys
import unicodedata
from pathlib import Path

import docx
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent
OUT_DEFAULT = ROOT / "nguon_mau" / "thong_tu_2026_du_thao"

# (tên file, chuỗi nhận diện tiêu đề sau khi bỏ khoảng trắng, viết hoa)
FORMS = [
    ("Mẫu số 1 - Giấy đề nghị đăng ký doanh nghiệp - Doanh nghiệp tư nhân",
     "GIẤYĐỀNGHỊĐĂNGKÝDOANHNGHIỆPDOANHNGHIỆPTƯNHÂN"),
    ("Mẫu số 2 - Giấy đề nghị đăng ký doanh nghiệp - Công ty TNHH một thành viên",
     "GIẤYĐỀNGHỊĐĂNGKÝDOANHNGHIỆPCÔNGTYTRÁCHNHIỆMHỮUHẠNMỘTTHÀNHVIÊN"),
    ("Mẫu số 3 - Giấy đề nghị đăng ký doanh nghiệp - Công ty TNHH hai thành viên trở lên",
     "GIẤYĐỀNGHỊĐĂNGKÝDOANHNGHIỆPCÔNGTYTRÁCHNHIỆMHỮUHẠNHAITHÀNHVIÊNTRỞLÊN"),
    ("Mẫu số 4 - Giấy đề nghị đăng ký doanh nghiệp - Công ty cổ phần",
     "GIẤYĐỀNGHỊĐĂNGKÝDOANHNGHIỆPCÔNGTYCỔPHẦN"),
    ("Mẫu số 5 - Giấy đề nghị đăng ký doanh nghiệp - Công ty hợp danh",
     "GIẤYĐỀNGHỊĐĂNGKÝDOANHNGHIỆPCÔNGTYHỢPDANH"),
    ("Mẫu số 10 - Danh sách chủ sở hữu hưởng lợi của doanh nghiệp", "MẪUSỐ10"),
    ("Mẫu số 12 - Giấy đề nghị đăng ký thay đổi - Thông báo thay đổi nội dung đăng ký doanh nghiệp", "MẪUSỐ12"),
    ("Mẫu số 27 - Thông báo tạm ngừng - tiếp tục kinh doanh trước thời hạn", "THÔNGBÁOVỀVIỆCTẠMNGỪNGKINHDOANH"),
    ("Mẫu số 30 - Thông báo về việc giải thể doanh nghiệp", "THÔNGBÁOVỀVIỆCGIẢITHỂDOANHNGHIỆP"),
]


def text(el) -> str:
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def key(s: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", s)).upper()


def has_sect(el) -> bool:
    return el.tag == qn("w:p") and el.find(f"./{qn('w:pPr')}/{qn('w:sectPr')}") is not None


def has_page_break(el) -> bool:
    return (any(b.get(qn("w:type")) == "page" for b in el.iter(qn("w:br")))
            or el.find(f".//{qn('w:pageBreakBefore')}") is not None)


def find_starts(els) -> list:
    starts = []
    for name, marker in FORMS:
        hits = [i for i, el in enumerate(els) if el.tag in (qn("w:p"), qn("w:tbl")) and key(text(el)).startswith(marker)]
        # Bỏ mục lục ở đầu file (bảng liệt kê các mẫu)
        hits = [i for i in hits if els[i].tag == qn("w:p")]
        assert hits, f"Không thấy tiêu đề: {name}"
        i = hits[0]
        while i > 0 and not (has_sect(els[i - 1]) or has_page_break(els[i - 1])):
            i -= 1
        starts.append(i)
    assert starts == sorted(starts), "Thứ tự mẫu trong file khác dự kiến"
    return starts


def extract(src: Path, start: int, end: int, out: Path) -> None:
    d = docx.Document(str(src))
    body = d.element.body
    els = [el for el in body.iterchildren() if el.tag != qn("w:sectPr")]
    final = body.find(qn("w:sectPr"))
    # Thuộc tính trang của phần cuối: section chứa phần tử `end`
    owner = next((el for el in els[end:] if has_sect(el)), None)
    if owner is not None:
        final.getparent().replace(final, copy.deepcopy(owner.find(f"./{qn('w:pPr')}/{qn('w:sectPr')}")))
    for i, el in enumerate(els):
        if not start <= i <= end:
            body.remove(el)
    last = els[end]
    if has_sect(last):
        last.find(qn("w:pPr")).remove(last.find(f"./{qn('w:pPr')}/{qn('w:sectPr')}"))
    for b in list(last.iter(qn("w:br"))):  # ngắt trang cuối sẽ sinh trang trắng
        if b.get(qn("w:type")) == "page":
            b.getparent().remove(b)
    fix_label(d, out.stem)
    renumber_footnotes(d)
    d.save(str(out))


def fix_label(d, name: str) -> None:
    """Dòng "Mẫu số N" ở bản gốc là số tự đánh (danh sách đánh số liên tục qua các mẫu); tách ra sẽ thành "Mẫu số 1".
    Thay bằng chữ cố định, giữ căn lề và phông của mức đánh số."""
    number = re.match(r"Mẫu số (\d+)", name).group(1)
    numbering = d.part.numbering_part.element
    for p in d.element.body.iter(qn("w:p")):
        num_pr = p.find(f"./{qn('w:pPr')}/{qn('w:numPr')}")
        if num_pr is None:
            continue
        num_id = num_pr.find(qn("w:numId")).get(qn("w:val"))
        num = next(n for n in numbering.iterchildren(qn("w:num")) if n.get(qn("w:numId")) == num_id)
        abs_id = num.find(qn("w:abstractNumId")).get(qn("w:val"))
        absn = next(a for a in numbering.iterchildren(qn("w:abstractNum")) if a.get(qn("w:abstractNumId")) == abs_id)
        lvl = absn.find(qn("w:lvl"))
        if not lvl.find(qn("w:lvlText")).get(qn("w:val")).startswith("Mẫu số"):
            return
        ppr = p.find(qn("w:pPr"))
        ppr.remove(num_pr)
        for tag in ("w:jc", "w:ind"):
            src = lvl.find(f"./{qn('w:pPr')}/{qn(tag)}")
            if src is not None and ppr.find(qn(tag)) is None:
                ppr.append(copy.deepcopy(src))
        run = p.makeelement(qn("w:r"), {})
        if lvl.find(qn("w:rPr")) is not None:
            run.append(copy.deepcopy(lvl.find(qn("w:rPr"))))
        t = run.makeelement(qn("w:t"), {})
        t.text = f"Mẫu số {number}"
        run.append(t)
        p.insert(list(p).index(ppr) + 1, run)
        return


def renumber_footnotes(d) -> None:
    """Chỉ giữ chú thích cuối trang mẫu này dùng, đánh lại mã 1..n (bản gốc dùng chung một kho cho mọi mẫu)."""
    part = next((r.target_part for r in d.part.rels.values() if r.reltype.endswith("/footnotes")), None)
    if part is None:
        return
    from lxml import etree
    root = etree.fromstring(part.blob)
    refs = list(d.element.body.iter(qn("w:footnoteReference")))
    new_id = {}
    for r in refs:
        new_id.setdefault(r.get(qn("w:id")), str(len(new_id) + 1))
        r.set(qn("w:id"), new_id[r.get(qn("w:id"))])
    for fn in list(root.iterchildren(qn("w:footnote"))):
        if fn.get(qn("w:type")) in ("separator", "continuationSeparator", "continuationNotice"):
            continue
        old = fn.get(qn("w:id"))
        if old in new_id:
            fn.set(qn("w:id"), new_id[old])
        else:
            root.remove(fn)
    part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def main() -> None:
    src = Path(sys.argv[1])
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    els = [el for el in docx.Document(str(src)).element.body.iterchildren() if el.tag != qn("w:sectPr")]
    starts = find_starts(els)
    ends = [s - 1 for s in starts[1:]] + [len(els) - 1]
    for (name, _), s, e in zip(FORMS, starts, ends):
        out = out_dir / f"{name}.docx"
        extract(src, s, e, out)
        print(f"{out.name}: phần tử {s}-{e}")


if __name__ == "__main__":
    main()
