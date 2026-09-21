import os
import shutil
import tempfile
import zipfile
import re
import datetime
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from io import BytesIO
from config import TEMPLATES_DIR
from services.word_service import get_all_paragraphs, clean_comma, replace_text_in_paragraph

def fmt_money(s):
    s = str(s).replace(",", "").replace(".", "").strip()
    if s.isdigit():
        return "{:,}".format(int(s))
    return s

def so_thanh_chu(s):
    s = str(s).replace(",", "").replace(".", "").strip()
    if not s.isdigit():
        return s
    n = int(s)
    if n == 0:
        return "Không đồng"

    don_vi = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ"]
    chu_so = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

    def doc_ba_chu_so(n):
        tram = n // 100
        chuc = (n % 100) // 10
        dv = n % 10
        result = ""
        if tram > 0:
            result += chu_so[tram] + " trăm "
            if chuc == 0 and dv > 0:
                result += "lẻ "
        if chuc > 1:
            result += chu_so[chuc] + " mươi "
            if dv == 1:
                result += "mốt "
            elif dv == 5:
                result += "lăm "
            elif dv > 0:
                result += chu_so[dv] + " "
        elif chuc == 1:
            result += "mười "
            if dv == 1:
                result += "một "
            elif dv == 5:
                result += "lăm "
            elif dv > 0:
                result += chu_so[dv] + " "
        else:
            if dv > 0:
                result += chu_so[dv] + " "
        return result.strip()

    chuoi_kq = ""
    i = 0
    while n > 0:
        phan_ba = n % 1000
        if phan_ba > 0:
            doc_phan_ba = doc_ba_chu_so(phan_ba)
            if doc_phan_ba:
                chuoi_kq = doc_phan_ba + " " + don_vi[i] + " " + chuoi_kq
        n = n // 1000
        i += 1

    chuoi_kq = chuoi_kq.strip().capitalize()
    if chuoi_kq.endswith(" "):
        chuoi_kq = chuoi_kq[:-1]
    return chuoi_kq + " đồng"

def parse_address(addr):
    parts = [p.strip() for p in addr.split(',')]
    tinh_thanh = parts.pop() if len(parts) > 0 else ""
    xa_phuong = ""
    if len(parts) > 0:
        lower = parts[-1].lower()
        if lower.startswith('phường') or lower.startswith('xã') or lower.startswith('thị trấn') or lower.startswith('tt'):
            xa_phuong = parts.pop()
        else:
            parts.pop() # ignore district
    if len(parts) > 0 and not xa_phuong:
        xa_phuong = parts.pop()
    so_nha = ", ".join(parts)
    return so_nha, xa_phuong, tinh_thanh

def generate_cn2tv_documents(cn2tv_data: dict) -> bytes:
    company = cn2tv_data.get('company', {})
    ddpl_cu = cn2tv_data.get('ddpl_cu', {})
    ddpl_moi = cn2tv_data.get('ddpl_moi', {})
    tv_cu = cn2tv_data.get('tv_cu', [])
    tv_moi = cn2tv_data.get('tv_moi', [])
    cn_list = cn2tv_data.get('chuyen_nhuong', [])
    
    ddpl_changed = ddpl_cu.get('SO_CCCD') != ddpl_moi.get('SO_CCCD')
    template_path = os.path.join(TEMPLATES_DIR, "Mẫu Chuyển nhượng Công ty TNHH 2 TV")

    with tempfile.TemporaryDirectory() as temp_dir:
        work_dir = os.path.join(temp_dir, "work")
        os.makedirs(work_dir)

        # Copy static files
        static_files = [
            "01. Thông báo bổ sung cập nhật.docx",
            "03. Danh sách thành viên.docx",
            "04. Danh sách chủ sở hữu hưởng lợi.docx",
            "05. Giấy ủy quyền.docx",
            "08. Quyết định.docx",
        ]
        if ddpl_changed:
            static_files.append("02. Thông báo thay đổi người đại diện theo pháp luật.docx")

        for fname in static_files:
            src = os.path.join(template_path, fname)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(work_dir, fname))

        # Copy Hợp đồng
        hd_template = os.path.join(template_path, "06. Hợp đồng chuyển nhượng.docx")
        for i, cn in enumerate(cn_list):
            suffix = chr(ord('a') + i)
            ben_a = tv_cu[int(cn['ben_a'])]
            ben_b = tv_moi[int(cn['ben_b'])]
            fname = f"06{suffix}. Hợp đồng chuyển nhượng ({ben_a.get('HO_TEN', '')} - {ben_b.get('HO_TEN', '')}).docx"
            fname = re.sub(r'[<>:"/\\|?*]', '_', fname)
            if os.path.exists(hd_template): shutil.copy2(hd_template, os.path.join(work_dir, fname))

        # Copy Biên bản thanh lý
        bb_template = os.path.join(template_path, "07. Biên bản thanh lý.docx")
        for i, cn in enumerate(cn_list):
            suffix = chr(ord('a') + i)
            ben_a = tv_cu[int(cn['ben_a'])]
            ben_b = tv_moi[int(cn['ben_b'])]
            fname = f"07{suffix}. Biên bản thanh lý ({ben_a.get('HO_TEN', '')} - {ben_b.get('HO_TEN', '')}).docx"
            fname = re.sub(r'[<>:"/\\|?*]', '_', fname)
            if os.path.exists(bb_template): shutil.copy2(bb_template, os.path.join(work_dir, fname))

        # Copy Xác nhận góp vốn
        xnv_template = os.path.join(template_path, "09. Xác nhận góp vốn 1.docx")
        for i, tv in enumerate(tv_moi):
            fname = f"09_{i+1}. Xác nhận góp vốn - {tv.get('HO_TEN', '')}.docx"
            fname = re.sub(r'[<>:"/\\|?*]', '_', fname)
            if os.path.exists(xnv_template): shutil.copy2(xnv_template, os.path.join(work_dir, fname))

        # Build replacement map
        common = {
            "[TEN_CONG_TY_VN]": company.get('TEN_CONG_TY_VN', ''),
            "[MA_SO_THUE]": company.get('MA_SO_THUE', ''),
            "[VON_DIEU_LE_SO]": fmt_money(company.get('VON_DIEU_LE_SO', '')),
            "[VON_DIEU_LE_CHU]": company.get('VON_DIEU_LE_CHU', ''),
            "[DDPL_CU_HO_TEN]": ddpl_cu.get('HO_TEN', ''),
            "[DDPL_CU_NGAY_SINH]": ddpl_cu.get('NGAY_SINH', ''),
            "[DDPL_CU_SO_CCCD]": ddpl_cu.get('SO_CCCD', ''),
            "[DDPL_CU_GIOI_TINH]": ddpl_cu.get('GIOI_TINH', ''),
            "[DDPL_CU_DIA_CHI_DAY_DU]": ddpl_cu.get('DIA_CHI', ''),
            "[DDPL_CU_DIA_CHI_SO_NHA]": ddpl_cu.get('DIA_CHI_SO_NHA', ''),
            "[DDPL_CU_DIA_CHI_XA_PHUONG]": ddpl_cu.get('DIA_CHI_XA_PHUONG', ''),
            "[DDPL_CU_DIA_CHI_TINH_THANH]": ddpl_cu.get('DIA_CHI_TINH_THANH', ''),
            "[DDPL_MOI_HO_TEN]": ddpl_moi.get('HO_TEN', ''),
            "[DDPL_MOI_NGAY_SINH]": ddpl_moi.get('NGAY_SINH', ''),
            "[DDPL_MOI_SO_CCCD]": ddpl_moi.get('SO_CCCD', ''),
            "[DDPL_MOI_GIOI_TINH]": ddpl_moi.get('GIOI_TINH', ''),
            "[DDPL_MOI_DIA_CHI_DAY_DU]": ddpl_moi.get('DIA_CHI', ''),
            "[DDPL_MOI_DIA_CHI_SO_NHA]": ddpl_moi.get('DIA_CHI_SO_NHA', ''),
            "[DDPL_MOI_DIA_CHI_XA_PHUONG]": ddpl_moi.get('DIA_CHI_XA_PHUONG', ''),
            "[DDPL_MOI_DIA_CHI_TINH_THANH]": ddpl_moi.get('DIA_CHI_TINH_THANH', ''),
        }
        
        # fallback if address split missing
        for pre, obj in [("[DDPL_CU_", ddpl_cu), ("[DDPL_MOI_", ddpl_moi)]:
            if not obj.get('DIA_CHI_TINH_THANH') and obj.get('DIA_CHI'):
                sn, xp, tt = parse_address(obj.get('DIA_CHI'))
                common[f"{pre}DIA_CHI_SO_NHA]"] = sn
                common[f"{pre}DIA_CHI_XA_PHUONG]"] = xp
                common[f"{pre}DIA_CHI_TINH_THANH]"] = tt

        for fname in os.listdir(work_dir):
            if fname.startswith("~$") or not fname.endswith(".docx"):
                continue
            
            doc_path = os.path.join(work_dir, fname)
            doc = Document(doc_path)
            replacements = dict(common)

            # Contract specific
            if fname.startswith("06") and "Hợp đồng" in fname:
                cn_idx = ord(fname[2]) - ord('a') if len(fname) > 2 and fname[2].isalpha() else 0
                if cn_idx < len(cn_list):
                    cn = cn_list[cn_idx]
                    ben_a = tv_cu[int(cn['ben_a'])]
                    ben_b = tv_moi[int(cn['ben_b'])]
                    replacements.update({
                        "[BEN_A_HO_TEN]": ben_a.get('HO_TEN', ''),
                        "[BEN_A_NGAY_SINH]": ben_a.get('NGAY_SINH', ''),
                        "[BEN_A_SO_CCCD]": ben_a.get('SO_CCCD', ''),
                        "[BEN_A_GIOI_TINH]": ben_a.get('GIOI_TINH', ''),
                        "[BEN_A_DIA_CHI_DAY_DU]": ben_a.get('DIA_CHI', ''),
                        "[BEN_B_HO_TEN]": ben_b.get('HO_TEN', ''),
                        "[BEN_B_NGAY_SINH]": ben_b.get('NGAY_SINH', ''),
                        "[BEN_B_SO_CCCD]": ben_b.get('SO_CCCD', ''),
                        "[BEN_B_GIOI_TINH]": ben_b.get('GIOI_TINH', ''),
                        "[BEN_B_DIA_CHI_DAY_DU]": ben_b.get('DIA_CHI', ''),
                        "[GIA_TRI_CN_SO]": fmt_money(cn.get('von', '')),
                        "[GIA_TRI_CN_CHU]": so_thanh_chu(str(cn.get('von', ''))),
                        "[GIA_TRI_CN_TY_LE]": cn.get('ty_le', '')
                    })
                    for b_prefix, b_obj in [("[BEN_A_", ben_a), ("[BEN_B_", ben_b)]:
                        if not b_obj.get('DIA_CHI_TINH_THANH') and b_obj.get('DIA_CHI'):
                            sn, xp, tt = parse_address(b_obj.get('DIA_CHI'))
                            replacements[f"{b_prefix}DIA_CHI_SO_NHA]"] = sn
                            replacements[f"{b_prefix}DIA_CHI_XA_PHUONG]"] = xp
                            replacements[f"{b_prefix}DIA_CHI_TINH_THANH]"] = tt

            if fname.startswith("07") and "Biên bản" in fname:
                cn_idx = ord(fname[2]) - ord('a') if len(fname) > 2 and fname[2].isalpha() else 0
                if cn_idx < len(cn_list):
                    cn = cn_list[cn_idx]
                    ben_a = tv_cu[int(cn['ben_a'])]
                    ben_b = tv_moi[int(cn['ben_b'])]
                    replacements.update({
                        "[BEN_A_HO_TEN]": ben_a.get('HO_TEN', ''),
                        "[BEN_A_NGAY_SINH]": ben_a.get('NGAY_SINH', ''),
                        "[BEN_A_SO_CCCD]": ben_a.get('SO_CCCD', ''),
                        "[BEN_A_GIOI_TINH]": ben_a.get('GIOI_TINH', ''),
                        "[BEN_A_DIA_CHI_DAY_DU]": ben_a.get('DIA_CHI', ''),
                        "[BEN_B_HO_TEN]": ben_b.get('HO_TEN', ''),
                        "[BEN_B_NGAY_SINH]": ben_b.get('NGAY_SINH', ''),
                        "[BEN_B_SO_CCCD]": ben_b.get('SO_CCCD', ''),
                        "[BEN_B_GIOI_TINH]": ben_b.get('GIOI_TINH', ''),
                        "[BEN_B_DIA_CHI_DAY_DU]": ben_b.get('DIA_CHI', ''),
                        "[GIA_TRI_CN_TY_LE]": cn.get('ty_le', '')
                    })
                    for b_prefix, b_obj in [("[BEN_A_", ben_a), ("[BEN_B_", ben_b)]:
                        if not b_obj.get('DIA_CHI_TINH_THANH') and b_obj.get('DIA_CHI'):
                            sn, xp, tt = parse_address(b_obj.get('DIA_CHI'))
                            replacements[f"{b_prefix}DIA_CHI_SO_NHA]"] = sn
                            replacements[f"{b_prefix}DIA_CHI_XA_PHUONG]"] = xp
                            replacements[f"{b_prefix}DIA_CHI_TINH_THANH]"] = tt

            if fname.startswith("09_") and "Xác nhận" in fname:
                match = re.match(r'09_(\d+)', fname)
                if match:
                    tv_idx = int(match.group(1)) - 1
                    if tv_idx < len(tv_moi):
                        tv = tv_moi[tv_idx]
                        replacements.update({
                            "[TV_MOI_1_HO_TEN]": tv.get('HO_TEN', ''),
                            "[TV_MOI_1_NGAY_SINH]": tv.get('NGAY_SINH', ''),
                            "[TV_MOI_1_SO_CCCD]": tv.get('SO_CCCD', ''),
                            "[TV_MOI_1_GIOI_TINH]": tv.get('GIOI_TINH', ''),
                            "[TV_MOI_1_DIA_CHI_DAY_DU]": tv.get('DIA_CHI', ''),
                            "[TV_MOI_1_VON_SO]": fmt_money(tv.get('VON_GOP', '')),
                            "[TV_MOI_1_TY_LE]": tv.get('TY_LE', '')
                        })
            
            # Global TV moi for table
            if len(tv_moi) >= 1:
                tv = tv_moi[0]
                replacements.update({
                    "[TV_MOI_1_HO_TEN]": tv.get('HO_TEN', ''),
                    "[TV_MOI_1_NGAY_SINH]": tv.get('NGAY_SINH', ''),
                    "[TV_MOI_1_SO_CCCD]": tv.get('SO_CCCD', ''),
                    "[TV_MOI_1_GIOI_TINH]": tv.get('GIOI_TINH', ''),
                    "[TV_MOI_1_DIA_CHI_DAY_DU]": tv.get('DIA_CHI', ''),
                    "[TV_MOI_1_VON_SO]": fmt_money(tv.get('VON_GOP', '')),
                    "[TV_MOI_1_TY_LE]": tv.get('TY_LE', '')
                })
            if len(tv_moi) >= 2:
                tv = tv_moi[1]
                replacements.update({
                    "[TV_MOI_2_HO_TEN]": tv.get('HO_TEN', ''),
                    "[TV_MOI_2_NGAY_SINH]": tv.get('NGAY_SINH', ''),
                    "[TV_MOI_2_SO_CCCD]": tv.get('SO_CCCD', ''),
                    "[TV_MOI_2_GIOI_TINH]": tv.get('GIOI_TINH', ''),
                    "[TV_MOI_2_DIA_CHI_DAY_DU]": tv.get('DIA_CHI', ''),
                    "[TV_MOI_2_VON_SO]": fmt_money(tv.get('VON_GOP', '')),
                    "[TV_MOI_2_TY_LE]": tv.get('TY_LE', '')
                })

            # CSHHL table logic (>= 25%)
            if fname == "04. Danh sách chủ sở hữu hưởng lợi.docx":
                cshhl = [m for m in tv_moi if float(str(m.get('TY_LE', '0')).replace(',', '.')) >= 25]
                if len(cshhl) >= 1:
                    tv = cshhl[0]
                    replacements.update({
                        "[CSHHL_1_HO_TEN]": tv.get('HO_TEN', ''),
                        "[CSHHL_1_NGAY_SINH]": tv.get('NGAY_SINH', ''),
                        "[CSHHL_1_SO_CCCD]": tv.get('SO_CCCD', ''),
                        "[CSHHL_1_GIOI_TINH]": tv.get('GIOI_TINH', ''),
                        "[CSHHL_1_DIA_CHI_DAY_DU]": tv.get('DIA_CHI', ''),
                        "[CSHHL_1_TY_LE]": tv.get('TY_LE', '')
                    })
                else:
                    replacements.update({
                        "[CSHHL_1_HO_TEN]": " ", "[CSHHL_1_NGAY_SINH]": " ", "[CSHHL_1_SO_CCCD]": " ",
                        "[CSHHL_1_DIA_CHI_DAY_DU]": " ", "[CSHHL_1_TY_LE]": " "
                    })

            # Replace text in document
            for old_text, new_text in replacements.items():
                if new_text is None or new_text == '':
                    continue
                for section in doc.sections:
                    for paragraph in get_all_paragraphs(section.header):
                        replace_text_in_paragraph(paragraph, old_text, new_text)
                    for paragraph in get_all_paragraphs(section.footer):
                        replace_text_in_paragraph(paragraph, old_text, new_text)
                for paragraph in get_all_paragraphs(doc):
                    replace_text_in_paragraph(paragraph, old_text, new_text)

            # Cleanup commas
            for section in doc.sections:
                for paragraph in get_all_paragraphs(section.header): clean_comma(paragraph)
                for paragraph in get_all_paragraphs(section.footer): clean_comma(paragraph)
            for paragraph in get_all_paragraphs(doc): clean_comma(paragraph)

            doc.save(doc_path)

        # Zip it up
        mem_zip = BytesIO()
        with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(work_dir):
                for file_name in files:
                    if file_name.startswith("~$"):
                        continue
                    file_path = os.path.join(root, file_name)
                    arcname = os.path.relpath(file_path, work_dir)
                    zf.write(file_path, arcname)
        
        return mem_zip.getvalue()
