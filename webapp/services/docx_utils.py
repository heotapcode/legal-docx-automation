import copy
from docx.table import _Row
from docx.text.paragraph import Paragraph
from services.word_service import replace_text_in_paragraph

def clone_paragraph(paragraph):
    p = paragraph._p
    new_p = copy.deepcopy(p)
    p.addnext(new_p)
    return Paragraph(new_p, paragraph._parent)

def clone_row(table, row_idx):
    row = table.rows[row_idx]
    new_tr = copy.deepcopy(row._tr)
    row._tr.addnext(new_tr)
    return _Row(new_tr, table)

def delete_paragraph(paragraph):
    p = paragraph._p
    p.getparent().remove(p)
    p._p = p._element = None

def process_dynamic_blocks(doc, members, csh, fmt_money_fn, so_thanh_chu_fn, parse_addr_fn):
    """
    Finds blocks between <<BEGIN_TV_BLOCK>> and <<END_TV_BLOCK>>.
    Duplicates them for each member (members[1:]).
    Then replaces [TV2_...] placeholders with the actual member data.
    """
    while True:
        start_idx, end_idx = -1, -1
        for i, p in enumerate(doc.paragraphs):
            if '<<BEGIN_TV_BLOCK>>' in p.text:
                start_idx = i
            elif '<<END_TV_BLOCK>>' in p.text and start_idx != -1:
                end_idx = i
                break
        
        if start_idx == -1 or end_idx == -1:
            break
            
        block = doc.paragraphs[start_idx + 1 : end_idx]
        
        # Clone for each additional member (index 2 to N)
        # We must insert them AFTER the current block.
        insert_after_p = doc.paragraphs[end_idx]
        
        for m_idx in range(2, len(members)):
            m = members[m_idx]
            sn, xp, tt = parse_addr_fn(m.get('DIA_CHI', ''))
            nhan_cn = m.get('nhan_cn', '')
            
            reps = {
                '[TV2_HO_TEN]': m.get('HO_TEN', ''),
                '[TV2_SO_CCCD]': m.get('CCCD', ''),
                '[TV2_NGAY_SINH]': m.get('NGAY_SINH', ''),
                '[TV2_GIOI_TINH]': m.get('GIOI_TINH', ''),
                '[TV2_DIA_CHI_SO_NHA]': sn,
                '[TV2_DIA_CHI_XA_PHUONG]': xp,
                '[TV2_DIA_CHI_TINH_THANH]': tt,
                '[TV2_VON_CU_SO]': fmt_money_fn(nhan_cn),
                '[TV2_VON_CU_MOI]': so_thanh_chu_fn(nhan_cn),
                '[TV2_TY_LE]': m.get('ty_le', '')
            }
            
            for bp in block:
                new_p = clone_paragraph(insert_after_p)
                new_p._p.getparent().replace(new_p._p, copy.deepcopy(bp._p))
                new_p = Paragraph(insert_after_p._p.getnext(), doc._body)
                
                for k, v in reps.items():
                    if k in new_p.text:
                        replace_text_in_paragraph(new_p, k, str(v))
                        
                insert_after_p = new_p
                        
        # Now process the original block for members[1] (TV2)
        m1 = members[1] if len(members) > 1 else {}
        sn, xp, tt = parse_addr_fn(m1.get('DIA_CHI', ''))
        nhan_cn = m1.get('nhan_cn', '')
        reps0 = {
            '[TV2_HO_TEN]': m1.get('HO_TEN', ''),
            '[TV2_SO_CCCD]': m1.get('CCCD', ''),
            '[TV2_NGAY_SINH]': m1.get('NGAY_SINH', ''),
            '[TV2_GIOI_TINH]': m1.get('GIOI_TINH', ''),
            '[TV2_DIA_CHI_SO_NHA]': sn,
            '[TV2_DIA_CHI_XA_PHUONG]': xp,
            '[TV2_DIA_CHI_TINH_THANH]': tt,
            '[TV2_VON_CU_SO]': fmt_money_fn(nhan_cn),
            '[TV2_VON_CU_MOI]': so_thanh_chu_fn(nhan_cn),
            '[TV2_TY_LE]': m1.get('ty_le', '')
        }
        for bp in block:
            for k, v in reps0.items():
                if k in bp.text:
                    replace_text_in_paragraph(bp, k, str(v))
                    
        # Remove tags
        delete_paragraph(doc.paragraphs[start_idx])
        delete_paragraph(doc.paragraphs[end_idx])

