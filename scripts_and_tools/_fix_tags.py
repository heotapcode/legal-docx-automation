import os
from docx import Document
from docx.text.paragraph import Paragraph
import re

d = 'Mẫu Chuyển đổi loại hình 1TV sang 2 TV'

def clear_tags(doc):
    for p in doc.paragraphs:
        if '<<BEGIN_TV_BLOCK>>' in p.text or '<<END_TV_BLOCK>>' in p.text:
            p._element.getparent().remove(p._element)

doc1 = Document(os.path.join(d, '01. Quyết định.docx'))
clear_tags(doc1)

# In Quyết định, Block 1 is from "1.1 Thành viên thêm phần vốn góp" or "Họ chữ đệm và tên: [TV2_HO_TEN]"
# Wait, let's just find the exact paragraphs.
# Block 1 starts at "Họ chữ đệm và tên: [TV2_HO_TEN]" (first occurrence)
# ends at "Ông [TV2_HO_TEN] nhận chuyển nhượng phần vốn góp từ bà [DDPL_HO_TEN]"
def insert_tags_by_search(doc, start_text, end_text):
    start_idx = -1
    end_idx = -1
    for i, p in enumerate(doc.paragraphs):
        if start_idx == -1 and start_text in p.text:
            start_idx = i
        if start_idx != -1 and end_idx == -1 and end_text in p.text:
            end_idx = i
            break
            
    if start_idx != -1 and end_idx != -1:
        doc.paragraphs[start_idx].insert_paragraph_before('<<BEGIN_TV_BLOCK>>')
        if end_idx + 1 < len(doc.paragraphs):
            doc.paragraphs[end_idx + 1].insert_paragraph_before('<<END_TV_BLOCK>>')
        else:
            doc.add_paragraph('<<END_TV_BLOCK>>')
        return True
    return False

insert_tags_by_search(doc1, "Họ chữ đệm và tên: [TV2_HO_TEN]", "[TV2_VON_CU_MOI]")

# There is a second block in Quyết định: "Điều 3:" ... "Họ chữ đệm và tên: [TV2_HO_TEN]" ... "Địa chỉ liên lạc: [TV2_DIA_CHI_TINH_THANH]"
# Wait, let's find the second occurrence.
start_idx2 = -1
end_idx2 = -1
found_first = False
for i, p in enumerate(doc1.paragraphs):
    if "Họ chữ đệm và tên: [TV2_HO_TEN]" in p.text:
        if not found_first:
            found_first = True
        else:
            start_idx2 = i
            break
for i in range(start_idx2, len(doc1.paragraphs)):
    if "[TV2_DIA_CHI_TINH_THANH]" in doc1.paragraphs[i].text:
        end_idx2 = i
        break
if start_idx2 != -1 and end_idx2 != -1:
    doc1.paragraphs[start_idx2].insert_paragraph_before('<<BEGIN_TV_BLOCK>>')
    if end_idx2 + 1 < len(doc1.paragraphs):
        doc1.paragraphs[end_idx2 + 1].insert_paragraph_before('<<END_TV_BLOCK>>')
    else:
        doc1.add_paragraph('<<END_TV_BLOCK>>')

doc1.save(os.path.join(d, '01. Quyết định.docx'))

doc2 = Document(os.path.join(d, '02. Điều lệ.docx'))
clear_tags(doc2)
insert_tags_by_search(doc2, "Họ chữ đệm và tên: [TV2_HO_TEN]", "[TV2_TY_LE]")
doc2.save(os.path.join(d, '02. Điều lệ.docx'))

print("Tags re-inserted successfully.")
