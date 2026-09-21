import docx
from docx.oxml.ns import qn
from lxml import etree
from pathlib import Path

def standardize_document_with_harmonized_size(doc: docx.Document):
    # 1. Standardize styles (docDefaults & Normal style) to Times New Roman, 12pt (sz="24")
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
            
        # Normal style
        for sz_node in styles_elem.xpath('//w:style[@w:styleId="Normal"]//w:sz'):
            sz_node.set(qn('w:val'), '24')
        for szCs_node in styles_elem.xpath('//w:style[@w:styleId="Normal"]//w:szCs'):
            szCs_node.set(qn('w:val'), '24')
        for rf in styles_elem.xpath('//w:style[@w:styleId="Normal"]//w:rFonts'):
            rf.set(qn('w:ascii'), 'Times New Roman')
            rf.set(qn('w:hAnsi'), 'Times New Roman')
            rf.set(qn('w:cs'), 'Times New Roman')
    except Exception as e:
        print("Styles standardization warning:", e)

    # 2. Collect all paragraphs across body, tables, headers, footers
    all_paras = list(doc.paragraphs)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    all_paras.append(p)
    for s in doc.sections:
        if s.header:
            all_paras.extend(s.header.paragraphs)
            for t in s.header.tables:
                for row in t.rows:
                    for cell in row.cells:
                        all_paras.extend(cell.paragraphs)
        if s.footer:
            all_paras.extend(s.footer.paragraphs)
            for t in s.footer.tables:
                for row in t.rows:
                    for cell in row.cells:
                        all_paras.extend(cell.paragraphs)

    # 3. Process each paragraph
    for p in all_paras:
        runs = p.runs
        if not runs:
            continue

        # Step 3a: Remove yellow highlights first
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

        # Step 3b: Determine the surrounding/dominant font size of this paragraph
        # Weight by number of characters in each run
        size_weights = {}
        for r in runs:
            text_len = max(len(r.text.strip()), 1)
            sz_val = r._r.xpath('./w:rPr/w:sz/@w:val')
            if sz_val:
                sz = sz_val[0]
                size_weights[sz] = size_weights.get(sz, 0) + text_len

        # If explicit sizes exist in this paragraph:
        # Pick the size with the most characters.
        # However, if size '28' (14pt) is present alongside '24' (12pt),
        # the user specifically noted form text is 12pt and inserted info was 14pt,
        # so prefer '24' over '28' in mixed paragraphs!
        if size_weights:
            if '24' in size_weights and '28' in size_weights:
                target_sz = '24'
            else:
                target_sz = max(size_weights, key=size_weights.get)
        else:
            target_sz = '24'  # Standard 12pt

        # Step 3c: Enforce Times New Roman and target_sz on all runs in paragraph
        for r in runs:
            r.font.name = 'Times New Roman'
            r_elem = r._r
            rpr = r_elem.xpath('./w:rPr')
            if not rpr:
                rpr_elem = etree.Element(qn('w:rPr'))
                r_elem.insert(0, rpr_elem)
            else:
                rpr_elem = rpr[0]

            # rFonts
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

            # sz
            sz = rpr_elem.xpath('./w:sz')
            if sz:
                sz[0].set(qn('w:val'), target_sz)
            else:
                new_sz = etree.Element(qn('w:sz'))
                new_sz.set(qn('w:val'), target_sz)
                rpr_elem.append(new_sz)

            # szCs
            szCs = rpr_elem.xpath('./w:szCs')
            if szCs:
                szCs[0].set(qn('w:val'), target_sz)
            else:
                new_szCs = etree.Element(qn('w:szCs'))
                new_szCs.set(qn('w:val'), target_sz)
                rpr_elem.append(new_szCs)

# Test on 01. Quyết định.docx and 03. Giấy đề nghị.docx
for fname in ["01. Quyết định.docx", "03. Giấy đề nghị.docx"]:
    p_path = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Chuyển đổi loại hình 1TV sang 2 TV") / fname
    doc = docx.Document(str(p_path))
    standardize_document_with_harmonized_size(doc)
    
    # Check paragraphs with {{
    print(f"\n=== {fname} ===")
    for idx, p in enumerate(doc.paragraphs):
        if "{{" in p.text:
            sizes = [r._r.xpath('./w:rPr/w:sz/@w:val')[0] for r in p.runs if r._r.xpath('./w:rPr/w:sz/@w:val')]
            print(f"P#{idx} runs sizes: {set(sizes)} -> text: {p.text[:60]}")
