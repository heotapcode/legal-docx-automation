import os
from docx import Document
d = 'Mẫu Chuyển đổi loại hình 1TV sang 2 TV'
doc = Document(os.path.join(d, '04. Danh sách thành viên.docx'))

for row in doc.tables[0].rows:
    for cell in row.cells:
        if '[DDPL DIA_CHI_SO_NHA]' in cell.text:
            cell.text = cell.text.replace('[DDPL DIA_CHI_SO_NHA]', '[DDPL_DIA_CHI_SO_NHA]')
        if '[DDPL DIA_CHI_XA_PHUONG]' in cell.text:
            cell.text = cell.text.replace('[DDPL DIA_CHI_XA_PHUONG]', '[DDPL_DIA_CHI_XA_PHUONG]')
        if '[DDPL DIA_CHI_TINH_THANH]' in cell.text:
            cell.text = cell.text.replace('[DDPL DIA_CHI_TINH_THANH]', '[DDPL_DIA_CHI_TINH_THANH]')
        if 'Nữ' == cell.text.strip():
            cell.text = cell.text.replace('Nữ', '[DDPL_GIOI_TINH]')
        if 'Nam' == cell.text.strip():
            cell.text = cell.text.replace('Nam', '[TV2_GIOI_TINH]')
            
doc.save(os.path.join(d, '04. Danh sách thành viên.docx'))
