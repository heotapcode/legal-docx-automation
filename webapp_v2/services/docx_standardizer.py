import docx
from docx.oxml.ns import qn
from lxml import etree

def standardize_document(doc: docx.Document):
    """
    Áp dụng tiêu chuẩn thể thức văn bản hành chính Việt Nam (Nghị định 30/2020/NĐ-CP):
    1. Phông chữ chuẩn: Times New Roman 100% cho mọi style, paragraph, run, table cell.
    2. Triệt tiêu hoàn toàn font lỗi .VnTime, .VnTimeH, Calibri, Aptos thừa.
    3. Xóa bỏ hoàn toàn highlight màu vàng (dấu vết placeholder của template).
    4. Chuẩn hóa kích cỡ font chữ (Font size):
       - Đồng bộ kích cỡ chữ của thông tin đưa vào bằng đúng cỡ chữ của nội dung xung quanh.
       - Chuẩn hóa docDefaults và Normal style về 12pt (sz="24") thay vì 14pt (sz="28").
       - Trong các đoạn văn bản có kích thước 12pt (hoặc bảng biểu 10-11pt), các run dữ liệu được điền vào sẽ tự động mang kích cỡ bằng đúng các run xung quanh trong cùng đoạn/ô.
    """
    # 1. Chuẩn hóa styles (docDefaults & Normal style) về Times New Roman, 12pt (sz="24")
    try:
        styles_elem = doc.styles._element

        # docDefaults
        for sz_node in styles_elem.xpath('//w:docDefaults//w:sz'):
            sz_node.set(qn('w:val'), '24')
        for szCs_node in styles_elem.xpath('//w:docDefaults//w:szCs'):
            szCs_node.set(qn('w:val'), '24')
        for rf in styles_elem.xpath('//w:docDefaults//w:rFonts'):
            rf.set(qn('w:ascii'), 'Times New Roman')
            rf.set(qn('w:hAnsi'), 'Times New Roman')
            rf.set(qn('w:cs'), 'Times New Roman')
            rf.set(qn('w:eastAsia'), 'Times New Roman')

        # Normal style & các style khác
        for style in doc.styles:
            if hasattr(style, 'font') and style.font:
                try:
                    style.font.name = 'Times New Roman'
                except Exception:
                    pass
            if hasattr(style, '_element') and style._element is not None:
                rpr = style._element.xpath('./w:rPr')
                if rpr:
                    rFonts = rpr[0].xpath('./w:rFonts')
                    if rFonts:
                        rFonts[0].set(qn('w:ascii'), 'Times New Roman')
                        rFonts[0].set(qn('w:hAnsi'), 'Times New Roman')
                        rFonts[0].set(qn('w:cs'), 'Times New Roman')
                        rFonts[0].set(qn('w:eastAsia'), 'Times New Roman')
                    else:
                        rf = etree.Element(qn('w:rFonts'))
                        rf.set(qn('w:ascii'), 'Times New Roman')
                        rf.set(qn('w:hAnsi'), 'Times New Roman')
                        rf.set(qn('w:cs'), 'Times New Roman')
                        rf.set(qn('w:eastAsia'), 'Times New Roman')
                        rpr[0].insert(0, rf)

        # Đặt Normal style sz về 24 (12pt)
        for sz_node in styles_elem.xpath('//w:style[@w:styleId="Normal"]//w:sz'):
            sz_node.set(qn('w:val'), '24')
        for szCs_node in styles_elem.xpath('//w:style[@w:styleId="Normal"]//w:szCs'):
            szCs_node.set(qn('w:val'), '24')
    except Exception as e:
        print(f"Warning standardizing styles: {e}")

    # 2. Thu thập toàn bộ paragraphs từ body, tables, headers, footers
    all_paras = list(doc.paragraphs)

    # Tables
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    all_paras.append(p)

    # Headers & Footers
    for s in doc.sections:
        if s.header:
            for p in s.header.paragraphs:
                all_paras.append(p)
            for t in s.header.tables:
                for row in t.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            all_paras.append(p)
        if s.footer:
            for p in s.footer.paragraphs:
                all_paras.append(p)
            for t in s.footer.tables:
                for row in t.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            all_paras.append(p)

    # 3. Chuẩn hóa từng paragraph: phông chữ và kích cỡ đồng bộ
    for p in all_paras:
        runs = p.runs
        if not runs:
            continue

        # 3a. Xóa highlight vàng và lọc màu không hợp lệ
        for r in runs:
            r_elem = r._r
            rpr = r_elem.xpath('./w:rPr')
            if rpr:
                for hl in rpr[0].xpath('./w:highlight'):
                    rpr[0].remove(hl)
                for color in rpr[0].xpath('./w:color'):
                    val = color.get(qn('w:val'), '').lower()
                    if val in ('ffff00', 'yellow', 'none'):
                        rpr[0].remove(color)

        # 3b. Xác định kích cỡ font chữ của nội dung xung quanh (dominant size)
        size_weights = {}
        for r in runs:
            text_len = max(len(r.text.strip()), 1)
            sz_val = r._r.xpath('./w:rPr/w:sz/@w:val')
            if sz_val:
                sz = sz_val[0]
                size_weights[sz] = size_weights.get(sz, 0) + text_len

        # Nếu đoạn có chứa cả 12pt (sz="24") và 14pt (sz="28"):
        # Ưu tiên sz="24" để thông tin điền vào khớp với cỡ chữ 12pt của form
        if size_weights:
            if '24' in size_weights and '28' in size_weights:
                target_sz = '24'
            else:
                target_sz = max(size_weights, key=size_weights.get)
        else:
            target_sz = '24'  # Mặc định 12pt

        # 3c. Áp dụng Times New Roman và target_sz cho tất cả runs trong đoạn
        for r in runs:
            r.font.name = 'Times New Roman'
            r_elem = r._r
            rpr = r_elem.xpath('./w:rPr')
            if not rpr:
                rpr_elem = etree.Element(qn('w:rPr'))
                r_elem.insert(0, rpr_elem)
            else:
                rpr_elem = rpr[0]

            # rFonts: Times New Roman
            rFonts = rpr_elem.xpath('./w:rFonts')
            if rFonts:
                rFonts[0].set(qn('w:ascii'), 'Times New Roman')
                rFonts[0].set(qn('w:hAnsi'), 'Times New Roman')
                rFonts[0].set(qn('w:cs'), 'Times New Roman')
                rFonts[0].set(qn('w:eastAsia'), 'Times New Roman')
            else:
                rf = etree.Element(qn('w:rFonts'))
                rf.set(qn('w:ascii'), 'Times New Roman')
                rf.set(qn('w:hAnsi'), 'Times New Roman')
                rf.set(qn('w:cs'), 'Times New Roman')
                rf.set(qn('w:eastAsia'), 'Times New Roman')
                rpr_elem.insert(0, rf)

            # sz: đồng bộ với nội dung xung quanh
            sz = rpr_elem.xpath('./w:sz')
            if sz:
                sz[0].set(qn('w:val'), target_sz)
            else:
                new_sz = etree.Element(qn('w:sz'))
                new_sz.set(qn('w:val'), target_sz)
                rpr_elem.append(new_sz)

            # szCs: đồng bộ
            szCs = rpr_elem.xpath('./w:szCs')
            if szCs:
                szCs[0].set(qn('w:val'), target_sz)
            else:
                new_szCs = etree.Element(qn('w:szCs'))
                new_szCs.set(qn('w:val'), target_sz)
                rpr_elem.append(new_szCs)

    return doc
