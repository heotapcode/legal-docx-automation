import docx
from docx.oxml.ns import qn
from lxml import etree
from pathlib import Path

def harmonize_font_sizes(doc: docx.Document):
    # 1. Standardize docDefaults & Normal style to 12pt (sz="24")
    try:
        styles_elem = doc.styles._element
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        # docDefaults
        for sz_node in styles_elem.xpath('//w:docDefaults//w:sz', namespaces=ns):
            sz_node.set(qn('w:val'), '24')
        for szCs_node in styles_elem.xpath('//w:docDefaults//w:szCs', namespaces=ns):
            szCs_node.set(qn('w:val'), '24')
            
        # Normal style
        for sz_node in styles_elem.xpath('//w:style[@w:styleId="Normal"]//w:sz', namespaces=ns):
            sz_node.set(qn('w:val'), '24')
        for szCs_node in styles_elem.xpath('//w:style[@w:styleId="Normal"]//w:szCs', namespaces=ns):
            szCs_node.set(qn('w:val'), '24')
    except Exception as e:
        print("Style defaults error:", e)

    # 2. Iterate all paragraphs in body and tables
    all_paras = list(doc.paragraphs)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    all_paras.append(p)

    for p in all_paras:
        runs = p.runs
        if not runs:
            continue

        # Collect explicit font sizes from surrounding runs
        explicit_sizes = []
        for r in runs:
            sz = r._r.xpath('./w:rPr/w:sz/@w:val')
            if sz:
                explicit_sizes.append(sz[0])

        # If there are explicit sizes in this paragraph, the target size is the most common one
        # Otherwise default to '24' (12pt)
        if explicit_sizes:
            target_sz = max(set(explicit_sizes), key=explicit_sizes.count)
        else:
            target_sz = '24'

        # Apply target_sz to every run in this paragraph
        for r in runs:
            r_elem = r._r
            rpr = r_elem.xpath('./w:rPr')
            if not rpr:
                rpr_elem = etree.Element(qn('w:rPr'))
                r_elem.insert(0, rpr_elem)
            else:
                rpr_elem = rpr[0]

            sz_elem = rpr_elem.xpath('./w:sz')
            if sz_elem:
                sz_elem[0].set(qn('w:val'), target_sz)
            else:
                new_sz = etree.Element(qn('w:sz'))
                new_sz.set(qn('w:val'), target_sz)
                rpr_elem.append(new_sz)

            szCs_elem = rpr_elem.xpath('./w:szCs')
            if szCs_elem:
                szCs_elem[0].set(qn('w:val'), target_sz)
            else:
                new_szCs = etree.Element(qn('w:szCs'))
                new_szCs.set(qn('w:val'), target_sz)
                rpr_elem.append(new_szCs)

# Test on 03. Giấy đề nghị.docx
tpl = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Chuyển đổi loại hình 1TV sang 2 TV\03. Giấy đề nghị.docx")
doc = docx.Document(str(tpl))
harmonize_font_sizes(doc)

# Check paragraphs that had 'sz: None' previously
print("After harmonization in 03. Giấy đề nghị.docx:")
for idx in [16, 18, 25, 35, 52]:
    if idx < len(doc.paragraphs):
        p = doc.paragraphs[idx]
        print(f"P#{idx}: {p.text[:40]}")
        for r in p.runs[:2]:
            sz = r._r.xpath('./w:rPr/w:sz/@w:val')
            print(f"   Run '{r.text[:20]}' -> sz={sz[0] if sz else 'None'}")
