import os
from docx import Document
d = 'Mẫu Chuyển đổi loại hình 1TV sang 2 TV'
doc = Document(os.path.join(d, '05. Danh sách chủ sở hữu hưởng lợi.docx'))

for row in doc.tables[0].rows:
    for cell in row.cells:
        if 'Nữ' == cell.text.strip():
            cell.text = cell.text.replace('Nữ', '[DDPL_GIOI_TINH]')
            
doc.save(os.path.join(d, '05. Danh sách chủ sở hữu hưởng lợi.docx'))
