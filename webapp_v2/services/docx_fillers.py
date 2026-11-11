"""Điền bảng và đoạn văn vào file Word SAU khi docxtpl đã điền biến: danh sách thành viên, chủ sở hữu hưởng lợi,
bảng ngành nghề, Điều lệ, Quyết định, Biên bản họp.

Các hàm này được gọi qua khóa "post" của _schema.json (services/document_rules.py: HOOKS) hoặc trực tiếp từ
render_service.render_documents (bảng ngành). Tách từ render_service.py; render_service vẫn xuất lại các tên này.
Lỗi khi điền không làm hỏng cả bộ hồ sơ: ghi log và bỏ qua bước đó.
"""
import copy
import logging
import re
from typing import Any, Dict, List

import docx

from services.text_format import danh_xung, fmt_money, so_thanh_chu

logger = logging.getLogger(__name__)

def populate_dstv(doc: docx.Document, members: List[Dict[str, Any]], is_tang_von: bool = False):
    if not members or len(doc.tables) == 0:
        return
    table = doc.tables[0]
    if len(table.rows) < 4:
        return
    template_tr = copy.deepcopy(table.rows[3]._tr)

    while len(table.rows) > 3:
        table._tbl.remove(table.rows[-1]._tr)

    for i, m in enumerate(members):
        new_tr = copy.deepcopy(template_tr)
        table._tbl.append(new_tr)
        cells = table.rows[-1].cells
        cells[0].text = str(i + 1)
        cells[1].text = str(m.get('HO_TEN') or m.get('ho_ten', '')).upper()
        cells[2].text = str(m.get('NGAY_SINH') or m.get('ngay_sinh', ''))
        cells[3].text = str(m.get('GIOI_TINH') or m.get('gioi_tinh', ''))
        cells[4].text = f"Số định danh cá nhân: {m.get('SO_CCCD') or m.get('so_cccd', '')}"
        if len(cells) > 5:
            cells[5].text = "Việt Nam"
        if len(cells) > 6:
            cells[6].text = "Kinh"
        if len(cells) > 7:
            cells[7].text = str(m.get('DIA_CHI') or m.get('dia_chi_day_du', ''))
        von = str(m.get('VON_GOP') or m.get('von_so', ''))
        if len(cells) > 8:
            cells[8].text = fmt_money(von)
        if len(cells) > 9:
            cells[9].text = str(m.get('TY_LE') or m.get('ty_le', ''))
        if len(cells) > 10:
            cells[10].text = f"Đồng Việt Nam\n{fmt_money(von)} đồng Việt Nam"
        if len(cells) > 11:
            if is_tang_von:
                cells[11].text = "…/…/2026"
            else:
                cells[11].text = "Trong thời hạn 90 ngày, kể từ ngày được cấp Giấy chứng nhận đăng ký doanh nghiệp"
        if len(cells) > 12:
            cells[12].text = ""
        if len(cells) > 13:
            cells[13].text = ""

def populate_cshhl(doc: docx.Document, members: List[Dict[str, Any]]):
    if not members or len(doc.tables) == 0:
        return
    table = doc.tables[0]
    if len(table.rows) < 4:
        return
    template_tr = copy.deepcopy(table.rows[3]._tr)

    while len(table.rows) > 3:
        table._tbl.remove(table.rows[-1]._tr)

    for i, m in enumerate(members):
        new_tr = copy.deepcopy(template_tr)
        table._tbl.append(new_tr)
        cells = table.rows[-1].cells
        cells[0].text = str(i + 1)
        cells[1].text = str(m.get('HO_TEN') or m.get('ho_ten', '')).upper()
        cells[2].text = str(m.get('NGAY_SINH') or m.get('ngay_sinh', ''))
        cells[3].text = str(m.get('GIOI_TINH') or m.get('gioi_tinh', ''))
        cells[4].text = f"Số định danh cá nhân: {m.get('SO_CCCD') or m.get('so_cccd', '')}"
        if len(cells) > 5:
            cells[5].text = "Việt Nam"
        if len(cells) > 6:
            cells[6].text = "Kinh"
        if len(cells) > 7:
            cells[7].text = str(m.get('DIA_CHI') or m.get('dia_chi_day_du', ''))
        if len(cells) > 8:
            cells[8].text = str(m.get('TY_LE') or m.get('ty_le', ''))
        if len(cells) > 9:
            cells[9].text = str(m.get('TY_LE') or m.get('ty_le', ''))

def populate_ma_nganh_table(doc: docx.Document, ma_nganh_list: List[Dict[str, Any]]):
    if not ma_nganh_list:
        return

    for table in doc.tables:
        try:
            if len(table.rows) == 0:
                continue
            row0_text = [c.text.strip().upper() for c in table.rows[0].cells]
            has_ma = any("MÃ NGÀNH" in t for t in row0_text)
            has_ten = any("TÊN NGÀNH" in t for t in row0_text)

            # Bảng "ngành bỏ khỏi danh sách" / "ngành sửa đổi" không phải danh sách ngành đã chọn
            removal = any("BỎ KHỎI" in t or "SỬA ĐỔI" in t for t in row0_text)

            if has_ma and has_ten and not removal:
                col_stt = None
                col_ten = None
                col_ma = None
                col_chinh = None

                for idx, t in enumerate(row0_text):
                    if "STT" in t:
                        col_stt = idx
                    elif "TÊN NGÀNH" in t:
                        col_ten = idx
                    elif "MÃ NGÀNH" in t:
                        col_ma = idx
                    elif "CHÍNH" in t:
                        col_chinh = idx

                # Clear existing content rows except header
                while len(table.rows) > 1:
                    table._tbl.remove(table.rows[1]._tr)

                # Add rows
                for i, nganh in enumerate(ma_nganh_list):
                    row_cells = table.add_row().cells
                    if col_stt is not None:
                        row_cells[col_stt].text = str(i + 1)
                    if col_ten is not None:
                        row_cells[col_ten].text = str(nganh.get("ten", ""))
                    if col_ma is not None:
                        row_cells[col_ma].text = str(nganh.get("ma", ""))
                    if col_chinh is not None:
                        is_main = nganh.get("is_main") or i == 0
                        row_cells[col_chinh].text = "X" if is_main else ""

                    # Ma nganh text standard
                    for cell in row_cells:
                        for p in cell.paragraphs:
                            for run in p.runs:
                                run.font.name = "Times New Roman"
        except Exception as e:
            logger.exception("Lỗi khi filling ma_nganh table")

def replace_section_between(doc: docx.Document, start_prefix: str, end_prefix: str, new_lines: list):
    p_start = None
    p_end = None
    for p in doc.paragraphs:
        if start_prefix in p.text and p_start is None:
            p_start = p
        elif end_prefix in p.text and p_start is not None and p_end is None:
            p_end = p
            break

    if not p_start or not p_end:
        return

    parent = p_start._p.getparent()
    children = list(parent)
    try:
        idx1 = children.index(p_start._p)
        idx2 = children.index(p_end._p)
    except ValueError:
        return

    for elem in children[idx1 + 1:idx2]:
        parent.remove(elem)

    for line in new_lines:
        p_new = p_end.insert_paragraph_before(line)
        p_new.style = 'Normal'

def populate_qd_tables(doc: docx.Document, members_list: list, csh_info: dict, hinh_thuc_cn: str = 'mot_phan'):
    try:
        # Table 2: Cơ cấu vốn cũ (Chủ sở hữu cũ 100%)
        if len(doc.tables) > 1:
            t2 = doc.tables[1]
            if len(t2.rows) >= 2 and len(t2.columns) >= 6:
                r = t2.rows[1]
                r.cells[0].text = "1"
                r.cells[1].text = csh_info.get("ho_ten", "")
                r.cells[2].text = csh_info.get("dia_chi_day_du", "")
                r.cells[3].text = str(csh_info.get("von_cu_so", ""))
                r.cells[4].text = "100"
                r.cells[5].text = str(csh_info.get("so_cccd", ""))

        # Table 3 (Cơ cấu góp vốn mới) & Table 7 (Danh sách thành viên sau chuyển đổi)
        for t_idx in [2, 6]:
            if len(doc.tables) > t_idx:
                t = doc.tables[t_idx]
                if len(t.rows) >= 2 and len(t.columns) >= 6:
                    template_tr = copy.deepcopy(t.rows[1]._tr)
                    while len(t.rows) > 1:
                        t._tbl.remove(t.rows[-1]._tr)
                    for i, m in enumerate(members_list):
                        new_tr = copy.deepcopy(template_tr)
                        t._tbl.append(new_tr)
                        cells = t.rows[-1].cells
                        cells[0].text = str(i + 1)
                        cells[1].text = m.get("ho_ten", "")
                        cells[2].text = m.get("dia_chi_day_du", "")
                        cells[3].text = str(m.get("von_so", ""))
                        cells[4].text = str(m.get("ty_le", ""))
                        cells[5].text = str(m.get("so_cccd", ""))

        # Table 8: Chữ ký Chủ sở hữu cũ
        if len(doc.tables) > 7:
            t8 = doc.tables[7]
            if len(t8.rows) >= 1 and len(t8.rows[0].cells) >= 2:
                c = t8.rows[0].cells[1]
                if "CHỦ SỞ HỮU CÔNG TY" in c.text:
                    c.text = f"CHỦ SỞ HỮU CÔNG TY\n\n\n\n\n{csh_info.get('ho_ten', '')}"

        # Danh sách động Mục 1.1 và Mục 1.2
        receiving_members = members_list if hinh_thuc_cn == "toan_bo" else members_list[1:]
        letters = ["a", "b", "c", "d", "e", "f", "g", "h"]

        # Mục 1.1: Thành viên thêm phần vốn góp
        if receiving_members:
            lines_11 = []
            for i, m in enumerate(receiving_members):
                m_dx = danh_xung(m.get("gioi_tinh", "Nam"))
                m_ht = m.get("ho_ten", "")
                if len(receiving_members) > 1:
                    lines_11.append(f"{letters[i]}) Thành viên nhận chuyển nhượng: {m_ht}")
                lines_11.append(f"Họ chữ đệm và tên: {m_ht}")
                lines_11.append(f"Giới tính: {m.get('gioi_tinh', 'Nam')}")
                lines_11.append(f"Ngày sinh: {m.get('ngay_sinh', '')}")
                lines_11.append(f"Số định danh cá nhân: {m.get('so_cccd', '')}")
                lines_11.append(f"Địa chỉ liên lạc: {m.get('dia_chi_day_du', '')}")
                lines_11.append(f"{m_dx} {m_ht} cam kết không vi phạm tại điều 18 Luật doanh nghiệp.")
                if i < len(receiving_members) - 1:
                    lines_11.append("")

            replace_section_between(doc, "1.1 Thành viên thêm phần vốn góp", "1.2. Nội dung thay đổi", lines_11)

            # Mục 1.2: Nội dung thay đổi phần vốn góp, tỷ lệ góp vốn
            csh_name = csh_info.get("ho_ten", "")
            csh_gt = csh_info.get("gioi_tinh", "Nam")
            csh_dx = danh_xung(csh_gt).lower()
            lines_12 = []
            for m in receiving_members:
                m_dx = danh_xung(m.get("gioi_tinh", "Nam"))
                m_name = m.get("ho_ten", "")
                m_von = m.get("nhan_cn_so") or m.get("von_so", "")
                m_chu = m.get("nhan_cn_chu") or m.get("von_chu", "")
                lines_12.append(f"- {m_dx} {m_name} nhận chuyển nhượng phần vốn góp từ {csh_dx} {csh_name} là {m_von} đồng ({m_chu}).")

            replace_section_between(doc, "1.2. Nội dung thay đổi", "1.3. Thời điểm góp vốn", lines_12)

        # Mục 5: Thành viên công ty (Tất cả thành viên công ty mới)
        if members_list:
            lines_5 = []
            for i, m in enumerate(members_list):
                if i > 0:
                    lines_5.append("Và:")
                lines_5.append(f"Họ chữ đệm và tên: {m.get('ho_ten', '')}")
                lines_5.append(f"Giới tính: {m.get('gioi_tinh', 'Nam')}")
                lines_5.append(f"Ngày sinh: {m.get('ngay_sinh', '')}")
                lines_5.append(f"Số định danh cá nhân: {m.get('so_cccd', '')}")
                lines_5.append(f"Địa chỉ liên lạc: {m.get('dia_chi_day_du', '')}")

            replace_section_between(doc, "5. Thành viên công ty:", "6. Cơ cấu góp vốn:", lines_5)

    except Exception as e:
        logger.exception("Lỗi khi populating QD tables")

def populate_dieu_le(doc: docx.Document, members_list: list):
    try:
        thutu_words = [
            "nhất", "hai", "ba", "tư", "năm", "sáu", "bảy", "tám", "chín", "mười",
            "mười một", "mười hai", "mười ba", "mười bốn", "mười lăm"
        ]
        letters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]

        # 1. Khoản 2 Điều 6: Phần vốn góp của các thành viên
        lines_members = []
        for i, m in enumerate(members_list):
            stt_word = thutu_words[i] if i < len(thutu_words) else str(i + 1)
            letter = letters[i] if i < len(letters) else f"m{i+1}"
            lines_members.append(f"{letter})  Thành viên thứ {stt_word}:")
            lines_members.append(f"Họ chữ đệm và tên: {m.get('ho_ten', '')}")
            lines_members.append(f"Giới tính: {m.get('gioi_tinh', 'Nam')}")
            lines_members.append(f"Ngày sinh: {m.get('ngay_sinh', '')}")
            lines_members.append(f"Số định danh cá nhân: {m.get('so_cccd', '')}")
            lines_members.append(f"Địa chỉ liên lạc: {m.get('dia_chi_day_du', '')}")
            v_so = m.get('von_so', '')
            ty_le = m.get('ty_le', '')
            lines_members.append(f"Sở hữu phần vốn góp có giá trị là {v_so} đồng, chiếm {ty_le}% vốn điều lệ;")
            if i < len(members_list) - 1:
                lines_members.append("")

        replace_section_between(doc, "2.  Phần vốn góp, giá trị phần vốn góp", "Điều 7. Quyền của thành viên", lines_members)

        # 2. Bảng chữ ký thành viên cuối Điều lệ
        if len(doc.tables) >= 3:
            t = doc.tables[-1]
            while len(t.rows) > 0:
                t._tbl.remove(t.rows[-1]._tr)

            for i in range(0, len(members_list), 2):
                row = t.add_row()
                m1 = members_list[i]
                m2 = members_list[i + 1] if i + 1 < len(members_list) else None

                row.cells[0].text = f"\n\n\n\n{m1.get('ho_ten', '')}"
                if m2:
                    row.cells[1].text = f"\n\n\n\n{m2.get('ho_ten', '')}"
                else:
                    row.cells[1].text = ""
    except Exception as e:
        logger.exception("Lỗi khi populating Dieu le")

def populate_dieu_le_tlm_2tv(doc: docx.Document, members_list: list):
    try:
        thutu_words = [
            "nhất", "hai", "ba", "tư", "năm", "sáu", "bảy", "tám", "chín", "mười",
            "mười một", "mười hai", "mười ba", "mười bốn", "mười lăm"
        ]
        letters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
        lines = []
        for i, m in enumerate(members_list):
            stt_word = thutu_words[i] if i < len(thutu_words) else str(i + 1)
            letter = letters[i] if i < len(letters) else f"m{i+1}"
            lines.append(f"{letter})  Thành viên thứ {stt_word}:")
            lines.append(f"Họ, chữ đệm và tên: {m.get('ho_ten', '')}")
            lines.append(f"Ngày, tháng, năm sinh: {m.get('ngay_sinh', '')}")
            lines.append(f"Giới tính: {m.get('gioi_tinh', 'Nam')}")
            lines.append(f"Số định danh cá nhân: {m.get('so_cccd', '')}")
            lines.append(f"Địa chỉ liên lạc: {m.get('dia_chi_day_du', '')}")
            v_so = m.get('von_so', '') or m.get('von_gop', '')
            ty_le = m.get('ty_le', '')
            lines.append(f"Sở hữu phần vốn góp có giá trị là {v_so} đồng, chiếm {ty_le}% vốn điều lệ; thời điểm góp vốn: Trong thời hạn 90 ngày, kể từ ngày được cấp Giấy chứng nhận đăng ký doanh nghiệp")
            if i < len(members_list) - 1:
                lines.append("")

        replace_section_between(doc, "2.  Phần vốn góp, giá trị phần vốn góp", "3. Thành viên phải góp vốn cho công ty", lines)

        # Table 3 chữ ký ở cuối Điều lệ
        if len(doc.tables) >= 3:
            t = doc.tables[-1]
            while len(t.rows) > 0:
                t._tbl.remove(t.rows[-1]._tr)

            for i in range(0, len(members_list), 2):
                row = t.add_row()
                m1 = members_list[i]
                m2 = members_list[i + 1] if i + 1 < len(members_list) else None

                row.cells[0].text = f"\n\n\n\n{m1.get('ho_ten', '')}"
                if m2:
                    row.cells[1].text = f"\n\n\n\n{m2.get('ho_ten', '')}"
                else:
                    row.cells[1].text = ""
    except Exception as e:
        logger.exception("Lỗi khi in populate_dieu_le_tlm_2tv")

def populate_dieu_le_tlm_cp(doc: docx.Document, shareholders_list: list, von_dieu_le_so: str = "", von_dieu_le_chu: str = ""):
    try:
        # 1. Điều 3. Danh sách cổ đông sáng lập
        lines_d3 = []
        for i, sh in enumerate(shareholders_list):
            lines_d3.append(f"{i + 1}. Họ, chữ đệm và tên: {sh.get('ho_ten', '')}")
            lines_d3.append(f"Ngày, tháng, năm sinh: {sh.get('ngay_sinh', '')}")
            lines_d3.append(f"Giới tính: {sh.get('gioi_tinh', 'Nam')}")
            lines_d3.append(f"Số định danh cá nhân: {sh.get('so_cccd', '')}")
            lines_d3.append(f"Địa chỉ liên lạc: {sh.get('dia_chi_day_du', '')}")
            if i < len(shareholders_list) - 1:
                lines_d3.append("")

        replace_section_between(doc, "Điều 3. Danh sách cổ đông sáng lập", "Điều 4. Người đại diện theo pháp luật", lines_d3)

        # 2. Chi tiết cổ phần và tỷ lệ góp vốn sau Điều 6
        v_num = re.sub(r'[^\d]', '', str(von_dieu_le_so))
        v_int = int(v_num) if v_num else 0
        tong_cp = f"{v_int // 10000:,}".replace(',', '.') if v_int else "0"
        tong_cp_chu = so_thanh_chu(str(v_int // 10000)) + " cổ phần" if v_int else ""

        lines_shares = []
        lines_shares.append(f"Số vốn này được chia thành: {tong_cp} cổ phần ({tong_cp_chu})")
        lines_shares.append("Mệnh giá mỗi cổ phần: 10.000 đồng (Mười nghìn đồng)/cổ phần)")
        lines_shares.append("Trong đó:")
        lines_shares.append(f"Số cổ phần dự kiến chào bán: {tong_cp} cổ phần, trị giá: {von_dieu_le_so} VNĐ ({von_dieu_le_chu} đồng)")
        lines_shares.append("Tỷ lệ % vốn góp của các cổ đông sáng lập góp vốn cụ thể như sau:")
        for sh in shareholders_list:
            v_sh_raw = str(sh.get('von_gop') or sh.get('von_so', '0'))
            v_sh_num = re.sub(r'[^\d]', '', v_sh_raw)
            v_sh_int = int(v_sh_num) if v_sh_num else 0
            sl_cp_sh = f"{v_sh_int // 10000:,}".replace(',', '.') if v_sh_int else "0"
            v_sh_fmt = fmt_money(v_sh_num) if v_sh_num else "0"
            v_sh_chu = so_thanh_chu(v_sh_num) if v_sh_num else ""
            ty_le_sh = str(sh.get('ty_le', ''))
            lines_shares.append(f"- Cổ đông {sh.get('ho_ten', '')}: sở hữu {sl_cp_sh} cổ phần (chiếm {ty_le_sh}% vốn điều lệ), trị giá {v_sh_fmt} đồng ({v_sh_chu}).")

        replace_section_between(doc, "Vốn góp bằng tiền mặt:", "Vốn điều lệ có thể tăng hoặc giảm", lines_shares)

        # 3. Chữ ký cổ đông sáng lập ở cuối Điều lệ
        p_found = None
        for p in doc.paragraphs:
            if "Chữ kỹ của các cổ đông sáng lập" in p.text or "Chữ ký của các cổ đông sáng lập" in p.text:
                p_found = p
                break
        if p_found:
            parent = p_found._p.getparent()
            table = doc.add_table(rows=0, cols=2)
            parent.insert(parent.index(p_found._p) + 1, table._tbl)
            for i in range(0, len(shareholders_list), 2):
                row = table.add_row()
                sh1 = shareholders_list[i]
                sh2 = shareholders_list[i + 1] if i + 1 < len(shareholders_list) else None
                row.cells[0].text = f"\n\n\n\n{sh1.get('ho_ten', '')}"
                if sh2:
                    row.cells[1].text = f"\n\n\n\n{sh2.get('ho_ten', '')}"
                else:
                    row.cells[1].text = ""
    except Exception as e:
        logger.exception("Lỗi khi in populate_dieu_le_tlm_cp")

def populate_cdsl(doc: docx.Document, shareholders: List[Dict[str, Any]]):
    if not shareholders or len(doc.tables) == 0:
        return
    table = doc.tables[0]
    if len(table.rows) < 6:
        return
    template_tr = copy.deepcopy(table.rows[5]._tr)

    while len(table.rows) > 5:
        table._tbl.remove(table.rows[-1]._tr)

    for i, sh in enumerate(shareholders):
        new_tr = copy.deepcopy(template_tr)
        table._tbl.append(new_tr)
        cells = table.rows[-1].cells
        cells[0].text = str(i + 1)
        cells[1].text = str(sh.get('HO_TEN') or sh.get('ho_ten', '')).upper()
        cells[2].text = str(sh.get('NGAY_SINH') or sh.get('ngay_sinh', ''))
        cells[3].text = str(sh.get('GIOI_TINH') or sh.get('gioi_tinh', 'Nam'))
        cccd = str(sh.get('SO_CCCD') or sh.get('so_cccd', ''))
        cells[4].text = f"Số định danh cá nhân: {cccd}"
        cells[5].text = "Việt Nam"
        cells[6].text = "Kinh"
        cells[7].text = str(sh.get('DIA_CHI') or sh.get('dia_chi_day_du', ''))

        v_raw = str(sh.get('VON_GOP') or sh.get('von_gop') or sh.get('von_so', '0'))
        v_num = re.sub(r'[^\d]', '', v_raw)
        v_int = int(v_num) if v_num else 0
        v_fmt = fmt_money(v_num) if v_num else "0"
        sl_cp = f"{v_int // 10000:,}".replace(',', '.') if v_int else "0"
        ty_le = str(sh.get('TY_LE') or sh.get('ty_le', ''))

        cells[8].text = sl_cp
        cells[9].text = f"Đồng Việt Nam  {v_fmt} đồng Việt Nam"
        cells[10].text = ty_le
        cells[11].text = sl_cp
        cells[12].text = f"Đồng Việt Nam  {v_fmt} đồng Việt Nam"
        cells[13].text = "0"
        cells[14].text = "0"
        cells[15].text = f"Đồng Việt Nam  {v_fmt} đồng Việt Nam"
        cells[16].text = "Trong thời hạn 90 ngày, kể từ ngày được cấp Giấy chứng nhận đăng ký doanh nghiệp"
        cells[17].text = ""
        cells[18].text = ""

def populate_bbh_tang_von_cp(doc: docx.Document, shareholders: List[Dict[str, Any]], von_cu_so: str = "", von_moi_so: str = ""):
    if not shareholders or len(doc.tables) < 2:
        return
    t2 = doc.tables[1]
    if len(t2.rows) == 0:
        return
    template_tr = copy.deepcopy(t2.rows[0]._tr)
    while len(t2.rows) > 0:
        t2._tbl.remove(t2.rows[-1]._tr)

    vc_num = re.sub(r'[^\d]', '', str(von_cu_so))
    vc_int = int(vc_num) if vc_num else 0

    for i, sh in enumerate(shareholders):
        new_tr = copy.deepcopy(template_tr)
        t2._tbl.append(new_tr)
        cells = t2.rows[-1].cells
        ht = str(sh.get("ho_ten", "")).upper()
        cells[0].text = ht
        ty_le_str = str(sh.get("ty_le", "0"))
        try:
            ty_le_val = float(ty_le_str.replace('%', '').strip())
        except ValueError:
            ty_le_val = 0.0

        # Tính số cổ phần và số vốn TRƯỚC TĂNG tại Mục IV (Thành phần dự họp)
        if vc_int > 0 and ty_le_val > 0:
            v_cu_sh = int(round(vc_int * (ty_le_val / 100.0)))
            sl_cp_cu = f"{v_cu_sh // 10000:,}".replace(',', '.')
        else:
            v_raw = str(sh.get("von_gop") or sh.get("von_so", "0"))
            v_num = re.sub(r'[^\d]', '', v_raw)
            v_int = int(v_num) if v_num else 0
            sl_cp_cu = f"{v_int // 10000:,}".replace(',', '.') if v_int else "0"

        cells[1].text = f"Cổ đông số {i+1:02d}, sở hữu {sl_cp_cu} cổ phần phổ thông, tương đương {sl_cp_cu} số phiếu biểu quyết, chiếm {ty_le_str}% tổng số phiếu biểu quyết của công ty;"

    # Bổ sung cơ cấu sở hữu cổ phần SAU TĂNG vào Mục V.1
    p_target = None
    for p in doc.paragraphs:
        if "Tài sản góp vốn sau khi thay đổi" in p.text:
            p_target = p
            break
    if p_target:
        p_head = p_target.insert_paragraph_before("Cơ cấu sở hữu cổ phần của các cổ đông sau khi tăng vốn:")
        p_head.style = 'Normal'
        for i, sh in enumerate(shareholders):
            ht = str(sh.get("ho_ten", "")).upper()
            v_raw = str(sh.get("von_gop") or sh.get("von_so", "0"))
            v_num = re.sub(r'[^\d]', '', v_raw)
            v_fmt = fmt_money(v_num) if v_num else "0"
            v_int = int(v_num) if v_num else 0
            sl_cp = f"{v_int // 10000:,}".replace(',', '.') if v_int else "0"
            ty_le = str(sh.get("ty_le", ""))
            p_sh = p_target.insert_paragraph_before(f"- Cổ đông {ht}: sở hữu {sl_cp} cổ phần phổ thông (giá trị {v_fmt} đồng), chiếm {ty_le}% tổng số vốn điều lệ;")
            p_sh.style = 'Normal'

def populate_bbh_giam_von_cp(doc: docx.Document, shareholders: List[Dict[str, Any]], von_cu_so: str = "", von_moi_so: str = ""):
    if not shareholders or len(doc.tables) < 2:
        return
    t2 = doc.tables[1]
    if len(t2.rows) == 0:
        return
    template_tr = copy.deepcopy(t2.rows[0]._tr)
    while len(t2.rows) > 0:
        t2._tbl.remove(t2.rows[-1]._tr)

    vc_num = re.sub(r'[^\d]', '', str(von_cu_so))
    vc_int = int(vc_num) if vc_num else 0

    for i, sh in enumerate(shareholders):
        new_tr = copy.deepcopy(template_tr)
        t2._tbl.append(new_tr)
        cells = t2.rows[-1].cells
        ht = str(sh.get("ho_ten", "")).upper()
        cells[0].text = ht
        ty_le_str = str(sh.get("ty_le", "0"))
        try:
            ty_le_val = float(ty_le_str.replace('%', '').strip())
        except ValueError:
            ty_le_val = 0.0

        # Tính số cổ phần và số vốn TRƯỚC GIẢM tại Mục IV (Thành phần dự họp)
        if vc_int > 0 and ty_le_val > 0:
            v_cu_sh = int(round(vc_int * (ty_le_val / 100.0)))
            sl_cp_cu = f"{v_cu_sh // 10000:,}".replace(',', '.')
        else:
            v_raw = str(sh.get("von_gop") or sh.get("von_so", "0"))
            v_num = re.sub(r'[^\d]', '', v_raw)
            v_int = int(v_num) if v_num else 0
            sl_cp_cu = f"{v_int // 10000:,}".replace(',', '.') if v_int else "0"

        cells[1].text = f"Cổ đông số {i+1:02d}, sở hữu {sl_cp_cu} cổ phần phổ thông, tương đương {sl_cp_cu} số phiếu biểu quyết, chiếm {ty_le_str}% tổng số phiếu biểu quyết của công ty;"

    # Bổ sung cơ cấu sở hữu cổ phần SAU GIẢM vào Mục V.1
    p_target = None
    for p in doc.paragraphs:
        if "Tài sản góp vốn sau khi thay đổi" in p.text:
            p_target = p
            break
    if p_target:
        p_head = p_target.insert_paragraph_before("Cơ cấu sở hữu cổ phần của các cổ đông sau khi giảm vốn:")
        p_head.style = 'Normal'
        for i, sh in enumerate(shareholders):
            ht = str(sh.get("ho_ten", "")).upper()
            v_raw = str(sh.get("von_gop") or sh.get("von_so", "0"))
            v_num = re.sub(r'[^\d]', '', v_raw)
            v_fmt = fmt_money(v_num) if v_num else "0"
            v_int = int(v_num) if v_num else 0
            sl_cp = f"{v_int // 10000:,}".replace(',', '.') if v_int else "0"
            ty_le = str(sh.get("ty_le", ""))
            p_sh = p_target.insert_paragraph_before(f"- Cổ đông {ht}: sở hữu {sl_cp} cổ phần phổ thông (giá trị {v_fmt} đồng), chiếm {ty_le}% tổng số vốn điều lệ;")
            p_sh.style = 'Normal'

def populate_bbh_tang_von_2tv(doc: docx.Document, members_list: List[Dict[str, Any]]):
    try:
        lines = []
        n = len(members_list)
        lines.append(f"Tham gia cuộc họp có tất cả {n:02d}/{n:02d} thành viên, sở hữu và đại diện cho 100 % vốn điều lệ công ty, cụ thể gồm:")
        for i, m in enumerate(members_list):
            ht = str(m.get("ho_ten", "")).upper()
            v_raw = str(m.get("von_gop") or m.get("von_so", "0"))
            v_num = re.sub(r'[^\d]', '', v_raw)
            v_fmt = fmt_money(v_num) if v_num else "0"
            v_chu = so_thanh_chu(v_num) if v_num else ""
            ty_le = str(m.get("ty_le", ""))
            lines.append(f"Họ và tên: {ht}")
            lines.append(f"Số vốn góp: {v_fmt} VNĐ ({v_chu}), chiếm {ty_le}% tổng số vốn điều lệ.")
            lines.append(f"Giấy chứng nhận đăng ký vốn góp số: {i+1:02d}/2026/GCN cấp ngày …./…./20….")

        replace_section_between(doc, "4. Thành phần dự họp:", "Chủ tọa cuộc họp:", lines)

        # Cập nhật đoạn quy ước biểu quyết linh hoạt cho N thành viên
        vote_parts = []
        for m in members_list:
            ht = str(m.get("ho_ten", "")).upper()
            ty_le = str(m.get("ty_le", ""))
            vote_parts.append(f"{ht} có {ty_le} phiếu biểu quyết, tương ứng với {ty_le}% vốn điều lệ.")
        vote_text = (
            "Công ty quy ước 1.000.000 đồng tương ứng với 1 phiếu biểu quyết. Vậy "
            + " ".join(vote_parts)
            + " Cuộc họp đã tiến hành biểu quyết lấy ý kiến trực tiếp của các thành viên công ty về các vấn đề nêu trên như sau:"
        )
        for p in doc.paragraphs:
            if "Công ty quy ước 1.000.000 đồng tương ứng với 1 phiếu biểu quyết" in p.text:
                p.text = vote_text
                break
    except Exception as e:
        logger.exception("Lỗi khi in populate_bbh_tang_von_2tv")

def populate_bbh_giai_the_cp(doc: docx.Document, shareholders: List[Dict[str, Any]], von_dieu_le_so: str = ""):
    try:
        if len(doc.tables) < 2:
            return
        t2 = doc.tables[1]
        if len(t2.rows) < 2:
            return
        template_tr = copy.deepcopy(t2.rows[1]._tr)
        while len(t2.rows) > 2:
            t2._tbl.remove(t2.rows[1]._tr)

        total_tr = t2.rows[1]._tr
        total_cp = 0
        total_val = 0
        for i, sh in enumerate(shareholders):
            new_tr = copy.deepcopy(template_tr)
            total_tr.addprevious(new_tr)
            cells = t2.rows[i + 1].cells
            cells[0].text = str(i + 1)
            ht = str(sh.get("ho_ten", "")).upper()
            cells[1].text = ht
            v_raw = str(sh.get("von_gop") or sh.get("von_so", "0"))
            v_num = re.sub(r'[^\\d]', '', v_raw)
            v_int = int(v_num) if v_num else 0
            sl_cp = v_int // 10000 if v_int else 0
            total_cp += sl_cp
            total_val += v_int
            sl_cp_str = f"{sl_cp:,}".replace(',', '.')
            v_fmt = f"{v_int:,}".replace(',', '.')
            ty_le = str(sh.get("ty_le", ""))
            cells[2].text = sl_cp_str
            cells[3].text = sl_cp_str
            cells[4].text = v_fmt
            cells[5].text = ty_le

        t_row = t2.rows[-1]
        t_row.cells[2].text = f"{total_cp:,}".replace(',', '.')
        t_row.cells[3].text = f"{total_cp:,}".replace(',', '.')
        t_row.cells[4].text = f"{total_val:,}".replace(',', '.')
        t_row.cells[5].text = "100"

        sh1 = shareholders[0]
        sh2 = shareholders[1] if len(shareholders) > 1 else sh1
        sh1_ht = str(sh1.get("ho_ten", "")).upper()
        sh2_ht = str(sh2.get("ho_ten", "")).upper()

        if len(doc.tables) >= 3:
            t3 = doc.tables[2]
            if len(t3.rows) >= 2:
                t3.rows[0].cells[1].text = f"Ông {sh1_ht} – Chủ tịch Hội đồng quản trị của công ty"
                t3.rows[1].cells[1].text = f"Ông {sh2_ht} – Cổ Đông của công ty"

        if len(doc.tables) >= 4:
            t4 = doc.tables[3]
            if len(t4.rows) >= 1:
                t4.rows[0].cells[0].text = f"Thư ký cuộc họp\n\n\n\n{sh2_ht}"
                t4.rows[0].cells[1].text = f"Chủ tọa – Chủ tịch HĐQT\n\n\n\n{sh1_ht}"

        if len(doc.tables) >= 6:
            t6 = doc.tables[5]
            if len(t6.rows) >= 1:
                t6.rows[0].cells[0].text = f"ĐẠI DIỆN THEO PHÁP LUẬT\nGiám đốc\n\n\n\n{sh1_ht}"
                t6.rows[0].cells[1].text = f"TM. ĐẠI HỘI ĐỒNG CỔ ĐÔNG\nCHỦ TỊCH HĐQT\n\n\n\n{sh1_ht}"
    except Exception as e:
        logger.exception("Lỗi khi in populate_bbh_giai_the_cp")
