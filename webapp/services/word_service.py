import os
import shutil
import tempfile
import zipfile
from io import BytesIO
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from config import TEMPLATES_DIR

DKKD_SECTION_MARKERS = [
    ("A1", "ĐĂNG KÝ THAY ĐỔI TÊN DOANH NGHIỆP"),
    ("A2", "ĐĂNG KÝ THAY ĐỔI ĐỊA CHỈ TRỤ SỞ CHÍNH"),
    ("A3", "ĐĂNG KÝ THAY ĐỔI THÀNH VIÊN CÔNG TY TNHH"),
    ("A4", "ĐĂNG KÝ THAY ĐỔI VỐN ĐIỀU LỆ"),
    ("A5", "THÔNG BÁO THAY ĐỔI NGÀNH, NGHỀ KINH DOANH"),
    ("A6", "THÔNG BÁO THAY ĐỔI THÔNG TIN ĐĂNG KÝ THUẾ"),
    ("A7", "CHỦ SỞ HỮU HƯỞNG LỢI CỦA DOANH NGHIỆP"),
]

DKKD_END_MARKERS = [
    "Kèm theo Thông báo này",
    "CHỮ KÝ CỦA CÁC THÀNH VIÊN",
    "Người đại diện theo pháp luật"
]

def remove_unselected_sections(doc, selected_sections):
    if not selected_sections:
        selected_sections = []
        
    body = doc._body._body
    found = []
    
    for i, elem in enumerate(body):
        text = "".join(elem.itertext()).upper()
        for code, marker in DKKD_SECTION_MARKERS:
            if marker in text:
                found.append((code, i))
                break
                
    if not found:
        return
        
    found.sort(key=lambda x: x[1])
    
    end_pos = len(body)
    for i, elem in enumerate(body):
        text = "".join(elem.itertext()).upper()
        for em in DKKD_END_MARKERS:
            if em.upper() in text:
                if i > found[0][1]:
                    end_pos = min(end_pos, i)
                    break
                    
    to_delete = []
    for idx, (code, start_idx) in enumerate(found):
        if code not in selected_sections:
            end_idx = found[idx + 1][1] if idx + 1 < len(found) else end_pos
            to_delete.append((start_idx, end_idx))
            
    for start_idx, end_idx in reversed(to_delete):
        for i in range(end_idx - 1, start_idx - 1, -1):
            if i < len(body):
                elem = body[i]
                elem.getparent().remove(elem)

def get_all_paragraphs(doc):
    paras = list(doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                paras.extend(get_all_paragraphs(cell))
    return paras

def replace_text_in_paragraph(paragraph, old_text, new_text):
    if old_text not in paragraph.text:
        return
    for run in paragraph.runs:
        if old_text in run.text:
            run.text = run.text.replace(old_text, str(new_text))
            run.font.highlight_color = WD_COLOR_INDEX.YELLOW

def clean_comma(paragraph):
    for old, new in [(" ,", ","), (", ,", ","), (": ,", ": "), (":,", ": ")]:
        if old in paragraph.text:
            for run in paragraph.runs:
                run.text = run.text.replace(old, new)

def generate_documents(template_name, data, ma_nganh_list, dkkd_selected=None) -> bytes:
    template_path = os.path.join(TEMPLATES_DIR, f"Mẫu {template_name}")
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template folder not found: {template_path}")

    for k, v in data.items():
        if v is None:
            data[k] = ""

    with tempfile.TemporaryDirectory() as temp_dir:
        for f in os.listdir(template_path):
            if f.startswith("~$") or not f.endswith((".docx", ".doc")):
                continue
            src = os.path.join(template_path, f)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(temp_dir, f))
        
        for f in os.listdir(temp_dir):
            if not f.endswith(".docx"):
                print(f"Warning: Cannot process .doc file {f} with python-docx. Please convert to .docx.")
                continue
                
            doc_path = os.path.join(temp_dir, f)
            doc = Document(doc_path)
            
            for key, val in data.items():
                placeholder = f"[{key}]"
                
                for section in doc.sections:
                    header = section.header
                    for paragraph in get_all_paragraphs(header):
                        replace_text_in_paragraph(paragraph, placeholder, val)
                    
                    footer = section.footer
                    for paragraph in get_all_paragraphs(footer):
                        replace_text_in_paragraph(paragraph, placeholder, val)
                
                for paragraph in get_all_paragraphs(doc):
                    replace_text_in_paragraph(paragraph, placeholder, val)

            for section in doc.sections:
                header = section.header
                for paragraph in get_all_paragraphs(header):
                    clean_comma(paragraph)
                footer = section.footer
                for paragraph in get_all_paragraphs(footer):
                    clean_comma(paragraph)
            for paragraph in get_all_paragraphs(doc):
                clean_comma(paragraph)

            if ma_nganh_list:
                for table in doc.tables:
                    try:
                        row1_text = [cell.text.strip() for cell in table.rows[0].cells]
                        if 'Mã ngành' in row1_text and 'Tên ngành' in row1_text:
                            col_stt = row1_text.index('STT') if 'STT' in row1_text else None
                            col_ten = row1_text.index('Tên ngành') if 'Tên ngành' in row1_text else None
                            col_ma = row1_text.index('Mã ngành') if 'Mã ngành' in row1_text else None
                            col_chinh = row1_text.index('Ngành nghề kinh doanh chính') if 'Ngành nghề kinh doanh chính' in row1_text else None
                            
                            while len(table.rows) > 1:
                                table._tbl.remove(table.rows[1]._tr)
                            
                            for i, nganh in enumerate(ma_nganh_list):
                                row_cells = table.add_row().cells
                                if col_stt is not None:
                                    row_cells[col_stt].text = str(i + 1)
                                if col_ten is not None:
                                    row_cells[col_ten].text = nganh.get('ten', '')
                                if col_ma is not None:
                                    row_cells[col_ma].text = nganh.get('ma', '')
                                if col_chinh is not None and (nganh.get('is_main') or i == 0):
                                    row_cells[col_chinh].text = 'X'
                                    
                                for cell in row_cells:
                                    for paragraph in cell.paragraphs:
                                        for run in paragraph.runs:
                                            run.font.highlight_color = WD_COLOR_INDEX.YELLOW
                    except Exception as e:
                        print(f"Lỗi bảng mã ngành: {e}")
                        pass
                        
            if dkkd_selected is not None:
                remove_unselected_sections(doc, dkkd_selected)
                        
            doc.save(doc_path)
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for f in os.listdir(temp_dir):
                zip_file.write(os.path.join(temp_dir, f), arcname=f)
                
        return zip_buffer.getvalue()
