import os
from docx import Document
from docx.text.paragraph import Paragraph

def find_block(doc, marker1, marker2):
    start = -1
    end = -1
    for i, p in enumerate(doc.paragraphs):
        if marker1 in p.text:
            start = i
        if marker2 in p.text:
            end = i
            break
    return start, end

# We will just write a python script to manually insert [BEGIN_TV] and [END_TV] around TV2_HO_TEN blocks.
# In "01. Quyết định.docx", TV2_HO_TEN is at P54 (Họ chữ đệm và tên) and P66 (Ông cam kết).
# Wait, Quyết định has 2 blocks? Let's check exactly where TV2_HO_TEN is used.
