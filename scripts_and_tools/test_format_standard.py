import docx
from docx.oxml.ns import qn
from lxml import etree
from pathlib import Path

def standardize_document_format(doc: docx.Document):
    # 1. Normal style
    try:
        normal = doc.styles['Normal']
        normal.font.name = 'Times New Roman'
        rpr = normal._element.xpath('./w:rPr')
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
                rpr[0].append(rf)
    except Exception as e:
        print('Normal style error:', e)

    # 2. Iterate all paragraphs
    all_paras = list(doc.paragraphs)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    all_paras.append(p)

    cleaned_highlights = 0
    fixed_runs = 0

    for p in all_paras:
        for r in p.runs:
            r.font.name = 'Times New Roman'
            r_elem = r._r
            rpr = r_elem.xpath('./w:rPr')
            if rpr:
                # Remove highlight
                for hl in rpr[0].xpath('./w:highlight'):
                    rpr[0].remove(hl)
                    cleaned_highlights += 1
                
                # Enforce Times New Roman in rFonts
                rFonts = rpr[0].xpath('./w:rFonts')
                if rFonts:
                    rFonts[0].set(qn('w:ascii'), 'Times New Roman')
                    rFonts[0].set(qn('w:hAnsi'), 'Times New Roman')
                    rFonts[0].set(qn('w:cs'), 'Times New Roman')
                else:
                    rf = etree.Element(qn('w:rFonts'))
                    rf.set(qn('w:ascii'), 'Times New Roman')
                    rf.set(qn('w:hAnsi'), 'Times New Roman')
                    rf.set(qn('w:cs'), 'Times New Roman')
                    rpr[0].insert(0, rf)
                fixed_runs += 1
            else:
                rpr_new = etree.Element(qn('w:rPr'))
                rf = etree.Element(qn('w:rFonts'))
                rf.set(qn('w:ascii'), 'Times New Roman')
                rf.set(qn('w:hAnsi'), 'Times New Roman')
                rf.set(qn('w:cs'), 'Times New Roman')
                rpr_new.append(rf)
                r_elem.insert(0, rpr_new)
                fixed_runs += 1

    return cleaned_highlights, fixed_runs

tpl_path = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Chuyển đổi loại hình 1TV sang 2 TV\01. Quyết định.docx")
doc = docx.Document(str(tpl_path))
hl_count, run_count = standardize_document_format(doc)
print(f"Standardized: {hl_count} highlights removed, {run_count} runs set to Times New Roman")
