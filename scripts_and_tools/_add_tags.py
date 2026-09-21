import os
from docx import Document
from docx.text.paragraph import Paragraph

d = 'Mẫu Chuyển đổi loại hình 1TV sang 2 TV'

# 1. Quyết định
doc = Document(os.path.join(d, '01. Quyết định.docx'))

def insert_tag_before(doc, p_index, tag):
    p = doc.paragraphs[p_index]
    new_p = p.insert_paragraph_before(tag)
    return new_p

def insert_tag_after(doc, p_index, tag):
    if p_index + 1 < len(doc.paragraphs):
        return insert_tag_before(doc, p_index + 1, tag)
    else:
        return doc.add_paragraph(tag)

# P17-P22 (Họ chữ đệm -> Ông cam kết)
# Wait, P24 is also TV2.
# Let's just wrap P17-P24 in one block!
insert_tag_before(doc, 17, '<<BEGIN_TV_BLOCK>>')
insert_tag_after(doc, 24, '<<END_TV_BLOCK>>')

# P53-P57 (Họ chữ đệm -> Địa chỉ)
insert_tag_before(doc, 53, '<<BEGIN_TV_BLOCK>>')
insert_tag_after(doc, 57, '<<END_TV_BLOCK>>')

doc.save(os.path.join(d, '01. Quyết định.docx'))

# 2. Điều lệ
doc2 = Document(os.path.join(d, '02. Điều lệ.docx'))
# P34-P39
insert_tag_before(doc2, 34, '<<BEGIN_TV_BLOCK>>')
insert_tag_after(doc2, 39, '<<END_TV_BLOCK>>')
doc2.save(os.path.join(d, '02. Điều lệ.docx'))

print("Tags inserted.")
