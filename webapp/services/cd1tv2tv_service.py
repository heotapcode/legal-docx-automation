import os
import shutil
import tempfile
import zipfile
import re
from docx import Document
from io import BytesIO
from config import TEMPLATES_DIR
from services.word_service import get_all_paragraphs, clean_comma, replace_text_in_paragraph
from services.cn2tv_service import fmt_money, so_thanh_chu, parse_address

from services.docx_utils import clone_paragraph, clone_row, delete_paragraph

def get_paragraph_index(doc, text):
    for i, p in enumerate(doc.paragraphs):
        if text in p.text:
            return i
    return -1

def generate_cd1tv2tv_documents(cd_data: dict, form_data: dict) -> bytes:
    csh = cd_data.get('csh', {})
    ddpl_cu = cd_data.get('ddplCu', {})
    ddpl_moi = cd_data.get('ddplMoi', {})
    members = cd_data.get('members', [])
    
    template_path = os.path.join(TEMPLATES_DIR, "Mẫu Chuyển đổi loại hình 1TV sang 2 TV")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        work_dir = os.path.join(temp_dir, "work")
        os.makedirs(work_dir)

        # 1. Copy static files
        static_files = [
            "01. Quyết định.docx",
            "02. Điều lệ.docx",
            "03. Giấy đề nghị.docx",
            "04. Danh sách thành viên.docx",
            "04. Giấy ủy quyền.docx",
            "05. Danh sách chủ sở hữu hưởng lợi.docx",
        ]
        
        for fname in static_files:
            src = os.path.join(template_path, fname)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(work_dir, fname))

        # 2. Hợp đồng chuyển nhượng
        hd_template = os.path.join(template_path, "07. Hợp đồng chuyển nhượng + Biên bản thanh lý.docx")
        for i, m in enumerate(members):
            nhan_cn = str(m.get('nhan_cn', '')).replace('.', '').replace(',', '').strip()
            if nhan_cn.isdigit() and int(nhan_cn) > 0:
                suffix = chr(ord('a') + i)
                fname = f"07{suffix}. HĐCN và Thanh lý ({csh.get('HO_TEN', '')} - {m.get('HO_TEN', '')}).docx"
                fname = re.sub(r'[<>:"/\\|?*]', '_', fname)
                if os.path.exists(hd_template):
                    shutil.copy2(hd_template, os.path.join(work_dir, fname))
                    
        # 3. Xác nhận góp vốn
        xnv_template = os.path.join(template_path, "Giấy chứng nhận góp vốn.docx")
        for i, m in enumerate(members):
            fname = f"08_{i+1}. Giấy chứng nhận góp vốn - {m.get('HO_TEN', '')}.docx"
            fname = re.sub(r'[<>:"/\\|?*]', '_', fname)
            if os.path.exists(xnv_template):
                shutil.copy2(xnv_template, os.path.join(work_dir, fname))
        
        # 4. Process files
        common = {
            "[TEN_CONG_TY_VN]": form_data.get('TEN_CONG_TY_VN', ''),
            "[TEN_CONG_TY_NN]": form_data.get('TEN_CONG_TY_EN', ''),
            "[TEN_CONG_TY_VIET_TAT]": form_data.get('TEN_CONG_TY_VIET_TAT', ''),
            "[MA_SO_THUE]": form_data.get('MA_SO_THUE', ''),
            "[VON_DIEU_LE_SO]": fmt_money(form_data.get('VON_CU', '')),
            "[VON_DIEU_LE_CHU]": so_thanh_chu(form_data.get('VON_CU', '')),
            "[DDPL_HO_TEN]": ddpl_moi.get('HO_TEN', '') or ddpl_cu.get('HO_TEN', ''),
            "[DDPL_NGAY_SINH]": ddpl_moi.get('NGAY_SINH', '') or ddpl_cu.get('NGAY_SINH', ''),
            "[DDPL_SO_CCCD]": ddpl_moi.get('CCCD', '') or ddpl_cu.get('CCCD', ''),
            "[DDPL_GIOI_TINH]": ddpl_moi.get('GIOI_TINH', '') or ddpl_cu.get('GIOI_TINH', ''),
            "[EMAIL_CONG_TY]": form_data.get('EMAIL_CONG_TY', ''),
            "[SDT_CONG_TY]": form_data.get('SDT_CONG_TY', ''),
        }
        
        sn, xp, tt = parse_address(ddpl_moi.get('DIA_CHI', '') or ddpl_cu.get('DIA_CHI', ''))
        common["[DDPL_DIA_CHI_SO_NHA]"] = sn
        common["[DDPL_DIA_CHI_XA_PHUONG]"] = xp
        common["[DDPL_DIA_CHI_TINH_THANH]"] = tt

        sn_cty, xp_cty, tt_cty = parse_address(form_data.get('DIA_CHI_CTY_CU', ''))
        common["[DIA_CHI_SO_NHA]"] = sn_cty
        common["[DIA_CHI_XA_PHUONG]"] = xp_cty
        common["[DIA_CHI_TINH_THANH]"] = tt_cty

        for fname in os.listdir(work_dir):
            if fname.startswith("~$") or not fname.endswith(".docx"):
                continue
            
            doc_path = os.path.join(work_dir, fname)
            doc = Document(doc_path)
            replacements = dict(common)

            # --- DYNAMIC MULTI-MEMBER LOGIC ---
            # Quyết định and Điều lệ have blocks of text for [TV2_...]
            # We will clone those blocks for TV3, TV4... if members > 2
            if fname in ["01. Quyết định.docx", "02. Điều lệ.docx"]:
                from services.docx_utils import process_dynamic_blocks
                process_dynamic_blocks(doc, members, csh, fmt_money, so_thanh_chu, parse_address)
                # The placeholders inside the blocks were already replaced! 
                # But we might still have other [TV2_] outside? No, they should all be inside.
            
            if "HĐCN" in fname:
                for i, m in enumerate(members):
                    if m.get('HO_TEN', '') in fname:
                        replacements["[DDPL_HO_TEN]"] = csh.get('HO_TEN', '')
                        replacements["[DDPL_SO_CCCD]"] = csh.get('CCCD', '')
                        replacements["[DDPL_NGAY_SINH]"] = csh.get('NGAY_SINH', '')
                        replacements["[DDPL_GIOI_TINH]"] = csh.get('GIOI_TINH', '')
                        
                        sn_csh, xp_csh, tt_csh = parse_address(csh.get('DIA_CHI', ''))
                        replacements["[DDPL_DIA_CHI_SO_NHA]"] = sn_csh
                        replacements["[DDPL_DIA_CHI_XA_PHUONG]"] = xp_csh
                        replacements["[DDPL_DIA_CHI_TINH_THANH]"] = tt_csh

                        replacements["[TV2_HO_TEN]"] = m.get('HO_TEN', '')
                        replacements["[TV2_SO_CCCD]"] = m.get('CCCD', '')
                        replacements["[TV2_NGAY_SINH]"] = m.get('NGAY_SINH', '')
                        replacements["[TV2_GIOI_TINH]"] = m.get('GIOI_TINH', '')
                        
                        sn_m, xp_m, tt_m = parse_address(m.get('DIA_CHI', ''))
                        replacements["[TV2_DIA_CHI_SO_NHA]"] = sn_m
                        replacements["[TV2_DIA_CHI_XA_PHUONG]"] = xp_m
                        replacements["[TV2_DIA_CHI_TINH_THANH]"] = tt_m
                        
                        nhan_cn = m.get('nhan_cn', '')
                        replacements["[TV2_VON_CU_SO]"] = fmt_money(nhan_cn)
                        replacements["[TV2_VON_CU_MOI]"] = so_thanh_chu(nhan_cn)

            if "Giấy chứng nhận" in fname:
                for i, m in enumerate(members):
                    if m.get('HO_TEN', '') in fname:
                        replacements["[TV2_HO_TEN]"] = m.get('HO_TEN', '')
                        replacements["[TV2_SO_CCCD]"] = m.get('CCCD', '')
                        replacements["[TV2_NGAY_SINH]"] = m.get('NGAY_SINH', '')
                        replacements["[TV2_GIOI_TINH]"] = m.get('GIOI_TINH', '')
                        replacements["[TV2_VON_CU_SO]"] = fmt_money(m.get('von', ''))
                        replacements["[TV2_VON_CU_CHU]"] = so_thanh_chu(m.get('von', ''))
                        replacements["[TV2_TY_LE]"] = m.get('ty_le', '')
                        
                        sn_m, xp_m, tt_m = parse_address(m.get('DIA_CHI', ''))
                        replacements["[TV2_DIA_CHI_SO_NHA]"] = sn_m
                        replacements["[TV2_DIA_CHI_XA_PHUONG]"] = xp_m
                        replacements["[TV2_DIA_CHI_TINH_THANH]"] = tt_m

            if fname in ["04. Danh sách thành viên.docx", "05. Danh sách chủ sở hữu hưởng lợi.docx"]:
                try:
                    table = doc.tables[0]
                    # members[0] is mapped to DDPL in the template's table.
                    # members[1] is mapped to TV2 in the template's table.
                    # for members[2:], we clone the TV2 row.
                    row_template_idx = 4 if "Danh sách thành viên" in fname else 3
                    
                    if len(members) > 2 and len(table.rows) > row_template_idx:
                        for m_idx in range(2, len(members)):
                            m = members[m_idx]
                            new_row = clone_row(table, row_template_idx)
                            sn, xp, tt = parse_address(m.get('DIA_CHI', ''))
                            reps = {
                                '[TV2_HO_TEN]': m.get('HO_TEN', ''),
                                '[TV2_SO_CCCD]': m.get('CCCD', ''),
                                '[TV2_NGAY_SINH]': m.get('NGAY_SINH', ''),
                                '[TV2_GIOI_TINH]': m.get('GIOI_TINH', ''),
                                '[TV2_DIA_CHI_SO_NHA]': sn,
                                '[TV2_DIA_CHI_XA_PHUONG]': xp,
                                '[TV2_DIA_CHI_TINH_THANH]': tt,
                                '[TV2_VON_CU_SO]': fmt_money(m.get('von', '')),
                                '[TV2_TY_LE]': m.get('ty_le', '')
                            }
                            # The STT is in cell 0
                            new_row.cells[0].text = str(m_idx + 1)
                            for cell in new_row.cells:
                                for p in cell.paragraphs:
                                    for k, v in reps.items():
                                        if k in p.text:
                                            replace_text_in_paragraph(p, k, str(v))
                    
                    # Now map members[0] to DDPL in table
                    if len(members) > 0:
                        m0 = members[0]
                        sn, xp, tt = parse_address(m0.get('DIA_CHI', ''))
                        replacements.update({
                            '[DDPL_VON_CU_SO]': fmt_money(m0.get('von', '')),
                            '[DDPL_TY_LE]': m0.get('ty_le', '')
                        })
                    
                    # And map members[1] to TV2 in table (handled by the main replacement loop)
                    if len(members) > 1:
                        m1 = members[1]
                        sn, xp, tt = parse_address(m1.get('DIA_CHI', ''))
                        replacements.update({
                            '[TV2_HO_TEN]': m1.get('HO_TEN', ''),
                            '[TV2_SO_CCCD]': m1.get('CCCD', ''),
                            '[TV2_NGAY_SINH]': m1.get('NGAY_SINH', ''),
                            '[TV2_GIOI_TINH]': m1.get('GIOI_TINH', ''),
                            '[TV2_DIA_CHI_SO_NHA]': sn,
                            '[TV2_DIA_CHI_XA_PHUONG]': xp,
                            '[TV2_DIA_CHI_TINH_THANH]': tt,
                            '[TV2_VON_CU_SO]': fmt_money(m1.get('von', '')),
                            '[TV2_TY_LE]': m1.get('ty_le', '')
                        })
                except Exception as e:
                    pass

            for old_text, new_text in replacements.items():
                if new_text is None or new_text == '':
                    continue
                for section in doc.sections:
                    for paragraph in get_all_paragraphs(section.header): replace_text_in_paragraph(paragraph, old_text, new_text)
                    for paragraph in get_all_paragraphs(section.footer): replace_text_in_paragraph(paragraph, old_text, new_text)
                for paragraph in get_all_paragraphs(doc): replace_text_in_paragraph(paragraph, old_text, new_text)
            
            for section in doc.sections:
                for paragraph in get_all_paragraphs(section.header): clean_comma(paragraph)
                for paragraph in get_all_paragraphs(section.footer): clean_comma(paragraph)
            for paragraph in get_all_paragraphs(doc): clean_comma(paragraph)

            doc.save(doc_path)
            
            # Post-process tables and paragraphs for dynamic members
            if "01. Quyết định" in fname or "02. Điều lệ" in fname or "04. Danh sách thành viên" in fname or "05. Danh sách chủ sở hữu hưởng lợi" in fname:
                pass

        # Zip it up
        mem_zip = BytesIO()
        with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(work_dir):
                for file_name in files:
                    if file_name.startswith("~$"): continue
                    file_path = os.path.join(root, file_name)
                    arcname = os.path.relpath(file_path, work_dir)
                    zf.write(file_path, arcname)
        
        return mem_zip.getvalue()
