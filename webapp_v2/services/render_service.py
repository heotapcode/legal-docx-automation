import logging
import json
import os
import re
import copy
import shutil
import tempfile
import zipfile
from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import docx
from docx.enum.text import WD_COLOR_INDEX
from docxtpl import DocxTemplate
from jinja2 import Environment

from config import TEMPLATES_DIR
from services.dia_ban import context_values as dia_ban_context
from services.dia_ban import co_quan_dk_ho_kinh_doanh

logger = logging.getLogger(__name__)

# --- HELPER FUNCTIONS ---

VND_PER_VOTE = 1_000_000  # quy ước số tiền tương ứng 1 phiếu biểu quyết

def _is_negative(s: Any) -> bool:
    return str(s).strip().startswith("-")


def fmt_money(s: Any) -> str:
    if s is None:
        return ""
    digits = re.sub(r"[^\d]", "", str(s))
    if digits:
        return ("-" if _is_negative(s) and int(digits) else "") + "{:,}".format(int(digits))
    return str(s)

def so_thanh_chu(s: Any) -> str:
    if s is None:
        return ""
    digits = re.sub(r"[^\d]", "", str(s))
    if not digits:
        return str(s)
    n = int(digits)
    if n == 0:
        return "Không đồng"

    don_vi = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ"]
    chu_so = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

    def doc_ba_chu_so(val: int, co_nhom_cao: bool) -> str:
        tram = val // 100
        chuc = (val % 100) // 10
        dv = val % 10
        res = ""

        if tram > 0:
            res += chu_so[tram] + " trăm "
            if chuc == 0 and dv > 0:
                res += "linh "
        elif co_nhom_cao:
            res += "không trăm "
            if chuc == 0 and dv > 0:
                res += "linh "

        if chuc > 1:
            res += chu_so[chuc] + " mươi "
            if dv == 1:
                res += "mốt "
            elif dv == 5:
                res += "lăm "
            elif dv > 0:
                res += chu_so[dv] + " "
        elif chuc == 1:
            res += "mười "
            if dv == 1:
                res += "một "
            elif dv == 5:
                res += "lăm "
            elif dv > 0:
                res += chu_so[dv] + " "
        else:
            if dv > 0:
                res += chu_so[dv] + " "

        return res.strip()

    chuoi_kq = ""
    i = 0
    temp_n = n
    while temp_n > 0:
        phan_ba = temp_n % 1000
        co_nhom_cao = (temp_n // 1000) > 0
        if phan_ba > 0:
            doc_phan_ba = doc_ba_chu_so(phan_ba, co_nhom_cao)
            if doc_phan_ba:
                prefix = don_vi[i] + " " if don_vi[i] else ""
                chuoi_kq = doc_phan_ba + " " + prefix + chuoi_kq
        temp_n = temp_n // 1000
        i += 1

    chuoi_kq = chuoi_kq.strip()
    if _is_negative(s):
        chuoi_kq = "âm " + chuoi_kq
    return chuoi_kq.capitalize() + " đồng"

def danh_xung(gioi_tinh: Any) -> str:
    if not gioi_tinh:
        return "Ông/Bà"
    gt = str(gioi_tinh).strip().lower()
    if "nam" in gt:
        return "Ông"
    if "nữ" in gt or "nu" in gt:
        return "Bà"
    return "Ông/Bà"

def format_date_vn(d: Any = None) -> str:
    if d:
        from datetime import date
        if isinstance(d, (datetime, date)):
            dt = d
        elif isinstance(d, str):
            try:
                dt = datetime.strptime(d.strip(), "%d/%m/%Y")
            except ValueError:
                try:
                    dt = datetime.strptime(d.strip(), "%Y-%m-%d")
                except ValueError:
                    dt = datetime.now()
        else:
            dt = datetime.now()
    else:
        dt = datetime.now()
    return f"ngày {dt.day:02d} tháng {dt.month:02d} năm {dt.year}"

WARD_PREFIXES = ("phường", "xã", "thị trấn", "tt.", "tt ", "đặc khu")
DISTRICT_PREFIXES = ("quận", "huyện", "thị xã", "thành phố", "tp.", "tp ", "q.", "h.")


def parse_address_str(addr: str):
    """Tách địa chỉ thành (số nhà/thôn, xã/phường, tỉnh/thành phố).

    Địa chỉ cũ còn cấp huyện (in trên CCCD cấp trước 01/07/2025), vd
    "Tiên Hội, Xã Đông Anh, Huyện Đông Anh, Hà Nội": cấp huyện đã bỏ nên không có ô riêng,
    được giữ kèm xã/phường -> ("Tiên Hội", "Xã Đông Anh, Huyện Đông Anh", "Hà Nội").
    """
    if not addr:
        return "", "", ""
    parts = [p.strip() for p in addr.split(',') if p.strip()]
    tinh_thanh = parts.pop() if len(parts) > 0 else ""

    huyen = ""
    if len(parts) > 1 and parts[-1].lower().startswith(DISTRICT_PREFIXES):
        huyen = parts.pop()

    xa_phuong = ""
    if len(parts) > 0:
        lower = parts[-1].lower()
        if lower.startswith(WARD_PREFIXES):
            xa_phuong = parts.pop()
        elif len(parts) > 1:
            xa_phuong = parts.pop()
    if huyen:
        xa_phuong = f"{xa_phuong}, {huyen}" if xa_phuong else huyen
    so_nha = ", ".join(parts)
    return so_nha, xa_phuong, tinh_thanh

TEMPLATE_ALIASES = {
    # Hoạt động lại trước thời hạn
    "hoạt động lại trước thời hạn": "Hoạt động lại trước thời hạn",
    "hoạt động lại": "Hoạt động lại trước thời hạn",
    "hoạt động trở lại": "Hoạt động lại trước thời hạn",
    "hoạt động trở lại trước thời hạn": "Hoạt động lại trước thời hạn",
    "hoạt động trở lại trước thời hạn tạm dừng": "Hoạt động lại trước thời hạn",
    "tiếp tục kinh doanh": "Hoạt động lại trước thời hạn",
    "tiếp tục kinh doanh trước thời hạn": "Hoạt động lại trước thời hạn",
    "tiếp tục kinh doanh trước thời hạn đã thông báo": "Hoạt động lại trước thời hạn",
    "thông báo tiếp tục kinh doanh": "Hoạt động lại trước thời hạn",
    "thông báo tiếp tục kinh doanh trước thời hạn": "Hoạt động lại trước thời hạn",
    "thông báo về việc tiếp tục kinh doanh": "Hoạt động lại trước thời hạn",
    "thông báo về việc tiếp tục kinh doanh trước thời hạn": "Hoạt động lại trước thời hạn",
    "thông báo hoạt động trở lại trước thời hạn tạm dừng": "Hoạt động lại trước thời hạn",
    "thông báo hoạt động trở lại": "Hoạt động lại trước thời hạn",
    # Tạm dừng
    "tạm dừng công ty tnhh 1 tv": "Tạm dừng công ty TNHH 1 TV",
    "tạm dừng công ty tnhh một thành viên": "Tạm dừng công ty TNHH 1 TV",
    "tạm ngừng công ty tnhh 1 tv": "Tạm dừng công ty TNHH 1 TV",
    "tạm ngừng kinh doanh công ty tnhh 1 tv": "Tạm dừng công ty TNHH 1 TV",
    "tạm dừng công ty tnhh 2 tv": "Tạm dừng công ty TNHH 2 TV",
    "tạm dừng công ty tnhh hai thành viên": "Tạm dừng công ty TNHH 2 TV",
    "tạm ngừng kinh doanh công ty tnhh 2 tv": "Tạm dừng công ty TNHH 2 TV",
    "tạm dừng công ty cổ phần": "Tạm dừng công ty Cổ Phần",
    "tạm ngừng kinh doanh công ty cổ phần": "Tạm dừng công ty Cổ Phần",
    # Thành lập mới
    "thành lập công ty tnhh 1 tv": "Thành lập mới công ty TNHH 1 TV",
    "thành lập cty tnhh 1 tv": "Thành lập mới công ty TNHH 1 TV",
    "thành lập mới cty tnhh 1 tv": "Thành lập mới công ty TNHH 1 TV",
    "thành lập công ty tnhh một thành viên": "Thành lập mới công ty TNHH 1 TV",
    "thành lập công ty tnhh 2 tv": "Thành lập mới công ty TNHH 2 TV",
    "thành lập cty tnhh 2 tv": "Thành lập mới công ty TNHH 2 TV",
    "thành lập mới cty tnhh 2 tv": "Thành lập mới công ty TNHH 2 TV",
    "thành lập công ty tnhh hai thành viên": "Thành lập mới công ty TNHH 2 TV",
    "thành lập công ty cổ phần": "Thành lập mới công ty Cổ Phần",
    "thành lập cty cổ phần": "Thành lập mới công ty Cổ Phần",
    "thành lập mới cty cổ phần": "Thành lập mới công ty Cổ Phần",
    # Giải thể
    "giải thể công ty tnhh 1 tv": "Giải thể công ty TNHH 1 TV",
    "giải thể công ty tnhh một thành viên": "Giải thể công ty TNHH 1 TV",
    "giải thể công ty tnhh 2 tv": "Giải thể công ty TNHH 2 TV",
    "giải thể công ty tnhh hai thành viên": "Giải thể công ty TNHH 2 TV",
    "giải thể công ty cổ phần": "Giải thể công ty Cổ Phần",
    # Chuyển nhượng & chuyển đổi
    "chuyển nhượng công ty tnhh 1 tv": "Chuyển nhượng công ty TNHH 1 TV",
    "chuyển nhượng công ty tnhh 2 tv": "Chuyển nhượng Công ty TNHH 2 TV",
    "chuyển đổi loại hình 1tv sang 2 tv": "Chuyển đổi loại hình 1TV sang 2 TV",
    "chuyển đổi 1tv sang 2tv": "Chuyển đổi loại hình 1TV sang 2 TV",
    # Địa điểm kinh doanh
    "thành lập địa điểm kinh doanh": "Thành lập mới địa điểm kinh doanh",
    "thành lập mới đđkd": "Thành lập mới địa điểm kinh doanh",
    "chấm dứt địa điểm kinh doanh": "Chấm dứt hoạt động địa điểm kinh doanh",
    "chấm dứt hoạt động đđkd": "Chấm dứt hoạt động địa điểm kinh doanh",
    # Cấp lại & Thay đổi
    "cấp lại đăng ký kinh doanh": "Cấp lại giấy đăng ký kinh doanh",
    "cấp lại gđkkd": "Cấp lại giấy đăng ký kinh doanh",
    "thay đổi đăng ký kinh doanh": "Thay đổi nội dung ĐKKD",
    # Giảm vốn
    "giảm vốn công ty cổ phần": "Giảm vốn công ty Cổ Phần",
    "giảm vốn cty cổ phần": "Giảm vốn công ty Cổ Phần",
    "giảm vốn ctcp": "Giảm vốn công ty Cổ Phần",
    "giảm vốn điều lệ công ty cổ phần": "Giảm vốn công ty Cổ Phần",
}

def resolve_template_name(template_name: str) -> str:
    clean = re.sub(r"\s+", " ", template_name.replace("Mẫu ", "").replace("mẫu ", "").strip())
    lower = clean.lower()
    if lower in TEMPLATE_ALIASES:
        return TEMPLATE_ALIASES[lower]
    # Fuzzy keyword heuristics
    if "giảm vốn" in lower:
        if "cổ phần" in lower or "cp" in lower or "ctcp" in lower:
            return "Giảm vốn công ty Cổ Phần"
    if "tiếp tục kinh doanh" in lower or ("hoạt động" in lower and "lại" in lower):
        return "Hoạt động lại trước thời hạn"
    if "tạm dừng" in lower or "tạm ngừng" in lower:
        if "cổ phần" in lower or "cp" in lower:
            return "Tạm dừng công ty Cổ Phần"
        if "1 tv" in lower or "1tv" in lower or "một thành viên" in lower:
            return "Tạm dừng công ty TNHH 1 TV"
        if "2 tv" in lower or "2tv" in lower or "hai thành viên" in lower:
            return "Tạm dừng công ty TNHH 2 TV"
    return clean

TEMPLATE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def template_id_index() -> Dict[str, Path]:
    """Bảng tra {id ASCII trong _schema.json: thư mục bộ mẫu}."""
    index: Dict[str, Path] = {}
    if not TEMPLATES_DIR.exists():
        return index
    for schema_path in TEMPLATES_DIR.glob("*/_schema.json"):
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                tid = json.load(f).get("id")
        except (OSError, ValueError):
            continue
        if isinstance(tid, str) and TEMPLATE_ID_RE.match(tid):
            index[tid] = schema_path.parent
    return index


def validate_template_dir(template_name: str) -> Path:
    # Ưu tiên tra theo id ASCII cố định (vd "tang-von-cong-ty-tnhh-2-tv")
    if TEMPLATE_ID_RE.match(template_name or ""):
        by_id = template_id_index().get(template_name)
        if by_id is not None:
            return by_id

    clean_name = resolve_template_name(template_name)
    if ".." in clean_name or "/" in clean_name or "\\" in clean_name:
        raise ValueError(f"Tên mẫu hồ sơ không hợp lệ: {template_name}")
    
    target_dir = (TEMPLATES_DIR / clean_name).resolve()
    templates_root = TEMPLATES_DIR.resolve()
    
    try:
        target_dir.relative_to(templates_root)
    except ValueError:
        raise ValueError(f"Tên mẫu hồ sơ không hợp lệ: {template_name}")
        
    if not target_dir.exists() or not target_dir.is_dir():
        for d in TEMPLATES_DIR.iterdir():
            if d.is_dir() and re.sub(r"\s+", " ", d.name.strip()).lower() == clean_name.lower():
                return d
        raise FileNotFoundError(f"Không tìm thấy mẫu hồ sơ: {template_name}")
        
    return target_dir

# --- CUSTOM JINJA2 ENVIRONMENT ---

def create_jinja_env() -> Environment:
    env = Environment(autoescape=True)
    env.filters["money"] = fmt_money
    env.filters["fmt_money"] = fmt_money
    env.filters["so_thanh_chu"] = so_thanh_chu
    env.filters["danh_xung"] = danh_xung
    env.filters["co_quan_hkd"] = co_quan_dk_ho_kinh_doanh
    env.filters["upper"] = lambda s: str(s).upper() if s else ""
    env.filters["lower"] = lambda s: str(s).lower() if s else ""
    env.globals["today_vn"] = format_date_vn
    env.globals["now"] = datetime.now
    return env

# --- CONTEXT NORMALIZATION ---

class SafeDict(dict):
    """A dictionary that returns empty string for missing keys instead of raising KeyError"""
    def __missing__(self, key):
        return ""

def merge_cd1tv2tv_data(raw_data: dict, cd1tv_data: dict):
    """Chuyển đổi 1TV -> 2TV: dựng các biến của bộ mẫu từ dữ liệu đã gom (gọi từ
    document_rules._prepare_chuyen_doi_1tv_2tv; cấu trúc cd1tv_data giữ theo wizard riêng cũ)."""
    csh = cd1tv_data.get('csh', {})
    ddpl_cu = cd1tv_data.get('ddplCu', {})
    ddpl_moi = cd1tv_data.get('ddplMoi', {})
    members = cd1tv_data.get('members', [])
    old_comp = cd1tv_data.get('oldCompany', {})
    new_comp = cd1tv_data.get('newCompany', {})
    hinh_thuc_cn = cd1tv_data.get('hinhThucCN') or cd1tv_data.get('hinh_thuc_cn') or 'mot_phan'
    raw_data['hinh_thuc_cn'] = hinh_thuc_cn

    # Company names
    old_name = old_comp.get('name') or raw_data.get('TEN_CONG_TY_VN_CU') or raw_data.get('ten_cong_ty_vn_cu') or ''
    new_name = new_comp.get('nameVn') or raw_data.get('TEN_CONG_TY_VN') or raw_data.get('ten_cong_ty_vn') or old_name
    raw_data['ten_cong_ty_vn_cu'] = old_name
    raw_data['TEN_CONG_TY_VN_CU'] = old_name
    raw_data['ten_cong_ty_vn'] = new_name
    raw_data['TEN_CONG_TY_VN'] = new_name
    raw_data['ten_cong_ty_nn'] = new_comp.get('nameEn') or raw_data.get('TEN_CONG_TY_EN', '')
    raw_data['TEN_CONG_TY_NN'] = raw_data['ten_cong_ty_nn']
    raw_data['ten_cong_ty_viet_tat'] = new_comp.get('nameShort') or raw_data.get('TEN_CONG_TY_VIET_TAT', '')
    raw_data['TEN_CONG_TY_VIET_TAT'] = raw_data['ten_cong_ty_viet_tat']
    raw_data['ma_so_thue'] = old_comp.get('mst') or raw_data.get('MA_SO_THUE', '')
    raw_data['sdt_cong_ty'] = new_comp.get('phone') or raw_data.get('SDT_CONG_TY', '')
    raw_data['email_cong_ty'] = new_comp.get('email') or raw_data.get('EMAIL_CONG_TY', '')

    # Company address
    c_addr = old_comp.get('address') or raw_data.get('DIA_CHI_CTY_CU') or ''
    if c_addr and not raw_data.get('dia_chi_so_nha'):
        c_sn, c_xp, c_tt = parse_address_str(c_addr)
        raw_data['dia_chi_so_nha'] = c_sn
        raw_data['dia_chi_xa_phuong'] = c_xp
        raw_data['dia_chi_tinh_thanh'] = c_tt
        raw_data['dia_chi_day_du'] = c_addr

    # Capital
    von_raw = old_comp.get('von') or raw_data.get('VON_CU') or raw_data.get('von_dieu_le_so', '')
    if von_raw:
        raw_data['von_dieu_le_so'] = fmt_money(von_raw)
        raw_data['von_dieu_le_chu'] = so_thanh_chu(von_raw)
        raw_data['von_cu_so'] = fmt_money(von_raw)
        raw_data['von_cu_chu'] = so_thanh_chu(von_raw)

    # CSH Cu (Chủ sở hữu cũ - Bên bán vốn)
    sn_csh, xp_csh, tt_csh = parse_address_str(csh.get('DIA_CHI', ''))
    raw_data['csh_ho_ten'] = csh.get('HO_TEN', '')
    raw_data['csh_so_cccd'] = csh.get('CCCD', '')
    raw_data['csh_ngay_sinh'] = csh.get('NGAY_SINH', '')
    raw_data['csh_gioi_tinh'] = csh.get('GIOI_TINH', 'Nam')
    raw_data['csh_dia_chi_day_du'] = csh.get('DIA_CHI', '')
    raw_data['csh_dia_chi_so_nha'] = sn_csh
    raw_data['csh_dia_chi_xa_phuong'] = xp_csh
    raw_data['csh_dia_chi_tinh_thanh'] = tt_csh

    # Danh sách thành viên công ty mới
    norm_members = []
    for idx, m in enumerate(members):
        if hinh_thuc_cn == 'mot_phan' and idx == 0:
            m_ht = m.get('ho_ten', '') or csh.get('HO_TEN', '')
            m_cccd = m.get('cccd', '') or csh.get('CCCD', '')
            m_ns = m.get('ngay_sinh', '') or csh.get('NGAY_SINH', '')
            m_gt = m.get('gioi_tinh', 'Nam') or csh.get('GIOI_TINH', 'Nam')
            m_dc = m.get('dia_chi', '') or csh.get('DIA_CHI', '')
        else:
            m_ht = m.get('ho_ten', '')
            m_cccd = m.get('cccd', '')
            m_ns = m.get('ngay_sinh', '')
            m_gt = m.get('gioi_tinh', 'Nam') or 'Nam'
            m_dc = m.get('dia_chi', '')
        sn_m, xp_m, tt_m = parse_address_str(m_dc)
        v_num = m.get('von', '')
        v_cn = m.get('nhan_cn', '')
        norm_members.append({
            'stt': idx + 1,
            'ho_ten': m_ht,
            'so_cccd': m_cccd,
            'ngay_sinh': m_ns,
            'gioi_tinh': m_gt,
            'dia_chi_day_du': m_dc,
            'dia_chi_so_nha': sn_m,
            'dia_chi_xa_phuong': xp_m,
            'dia_chi_tinh_thanh': tt_m,
            'von_so': fmt_money(v_num),
            'von_gop': fmt_money(v_num),
            'von_chu': so_thanh_chu(v_num),
            'ty_le': m.get('ty_le', ''),
            'nhan_cn_so': fmt_money(v_cn),
            'nhan_cn_chu': so_thanh_chu(v_cn) if v_cn else ''
        })
    raw_data['thanh_vien'] = norm_members

    # Người đại diện theo pháp luật mới của công ty 2TV
    if ddpl_moi and ddpl_moi.get('HO_TEN'):
        use_ddpl = ddpl_moi
    elif hinh_thuc_cn == 'toan_bo' and len(norm_members) > 0:
        use_ddpl = {
            'HO_TEN': norm_members[0]['ho_ten'],
            'CCCD': norm_members[0]['so_cccd'],
            'NGAY_SINH': norm_members[0]['ngay_sinh'],
            'GIOI_TINH': norm_members[0]['gioi_tinh'],
            'DIA_CHI': norm_members[0]['dia_chi_day_du']
        }
    else:
        use_ddpl = csh

    sn_d, xp_d, tt_d = parse_address_str(use_ddpl.get('DIA_CHI', ''))
    raw_data['ddpl_ho_ten'] = use_ddpl.get('HO_TEN', '')
    raw_data['ddpl_so_cccd'] = use_ddpl.get('CCCD', '')
    raw_data['ddpl_ngay_sinh'] = use_ddpl.get('NGAY_SINH', '')
    raw_data['ddpl_gioi_tinh'] = use_ddpl.get('GIOI_TINH', 'Nam')
    raw_data['ddpl_dia_chi_day_du'] = use_ddpl.get('DIA_CHI', '')
    raw_data['ddpl_dia_chi_so_nha'] = sn_d
    raw_data['ddpl_dia_chi_xa_phuong'] = xp_d
    raw_data['ddpl_dia_chi_tinh_thanh'] = tt_d

    if ddpl_moi and ddpl_moi.get('HO_TEN'):
        raw_data['ddpl_moi_ho_ten'] = ddpl_moi.get('HO_TEN', '')
        raw_data['ddpl_moi_so_cccd'] = ddpl_moi.get('CCCD', '')
        raw_data['ddpl_moi_ngay_sinh'] = ddpl_moi.get('NGAY_SINH', '')
        raw_data['ddpl_moi_gioi_tinh'] = ddpl_moi.get('GIOI_TINH', 'Nam')
        raw_data['ddpl_moi_dia_chi_day_du'] = ddpl_moi.get('DIA_CHI', '')
        raw_data['ddpl_moi_dia_chi_so_nha'] = sn_d
        raw_data['ddpl_moi_dia_chi_xa_phuong'] = xp_d
        raw_data['ddpl_moi_dia_chi_tinh_thanh'] = tt_d

    # Member 1 & 2 keys
    if len(norm_members) > 0:
        m1 = norm_members[0]
        raw_data['tv1_ho_ten'] = m1['ho_ten']
        raw_data['tv1_so_cccd'] = m1['so_cccd']
        raw_data['tv1_ngay_sinh'] = m1['ngay_sinh']
        raw_data['tv1_gioi_tinh'] = m1['gioi_tinh']
        raw_data['tv1_dia_chi_day_du'] = m1['dia_chi_day_du']
        raw_data['tv1_dia_chi_so_nha'] = m1['dia_chi_so_nha']
        raw_data['tv1_dia_chi_xa_phuong'] = m1['dia_chi_xa_phuong']
        raw_data['tv1_dia_chi_tinh_thanh'] = m1['dia_chi_tinh_thanh']
        raw_data['tv1_von_so'] = m1['von_so']
        raw_data['tv1_von_chu'] = m1['von_chu']
        raw_data['tv1_ty_le'] = m1['ty_le']

        raw_data['ddpl_ty_le'] = m1['ty_le']
        raw_data['ddpl_von_cu_so'] = m1['von_so']
        raw_data['ddpl_von_cu_chu'] = m1['von_chu']

    if len(norm_members) > 1:
        m2 = norm_members[1]
        raw_data['tv2_ho_ten'] = m2['ho_ten']
        raw_data['tv2_so_cccd'] = m2['so_cccd']
        raw_data['tv2_ngay_sinh'] = m2['ngay_sinh']
        raw_data['tv2_gioi_tinh'] = m2['gioi_tinh']
        raw_data['tv2_dia_chi_day_du'] = m2['dia_chi_day_du']
        raw_data['tv2_dia_chi_so_nha'] = m2['dia_chi_so_nha']
        raw_data['tv2_dia_chi_xa_phuong'] = m2['dia_chi_xa_phuong']
        raw_data['tv2_dia_chi_tinh_thanh'] = m2['dia_chi_tinh_thanh']
        v2 = m2['nhan_cn_so'] or m2['von_so']
        v2_chu = m2['nhan_cn_chu'] or m2['von_chu']
        raw_data['tv2_von_cu_so'] = v2
        raw_data['tv2_von_cu_chu'] = v2_chu
        raw_data['tv2_von_cu_moi'] = v2_chu
        raw_data['tv2_ty_le'] = m2['ty_le']

    # Build transfer transactions list
    cn_raw = cd1tv_data.get('chuyen_nhuong') or raw_data.get('chuyen_nhuong') or []
    if not cn_raw and len(norm_members) > 0:
        csh_ben_a = {
            'ho_ten': raw_data.get('csh_ho_ten', '') or csh.get('HO_TEN', ''),
            'so_cccd': raw_data.get('csh_so_cccd', '') or csh.get('CCCD', ''),
            'ngay_sinh': raw_data.get('csh_ngay_sinh', '') or csh.get('NGAY_SINH', ''),
            'gioi_tinh': raw_data.get('csh_gioi_tinh', 'Nam') or csh.get('GIOI_TINH', 'Nam'),
            'dia_chi_day_du': raw_data.get('csh_dia_chi_day_du', '') or csh.get('DIA_CHI', ''),
            'dia_chi_so_nha': raw_data.get('csh_dia_chi_so_nha', ''),
            'dia_chi_xa_phuong': raw_data.get('csh_dia_chi_xa_phuong', ''),
            'dia_chi_tinh_thanh': raw_data.get('csh_dia_chi_tinh_thanh', '')
        }
        target_members = norm_members if hinh_thuc_cn == 'toan_bo' else norm_members[1:]
        for m in target_members:
            v_amt = m.get('nhan_cn_so') or m.get('von_so')
            if v_amt and str(v_amt).strip() != '0':
                cn_raw.append({
                    'ben_a': csh_ben_a,
                    'ben_b': m,
                    'von_cn_so': v_amt,
                    'von_cn_chu': m.get('nhan_cn_chu') or m.get('von_chu'),
                    'ty_le_cn': m.get('ty_le', ''),
                    'gia_tri_cn_so': v_amt
                })
    raw_data['chuyen_nhuong'] = cn_raw

def normalize_context(raw_data: Dict[str, Any], ma_nganh_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    ctx = SafeDict()

    # Copy raw data with both original case and lowercase
    for k, v in raw_data.items():
        ctx[k] = v if v is not None else ""
        ctx[k.lower()] = v if v is not None else ""
        ctx[k.upper()] = v if v is not None else ""

    # Parse company address
    so_nha = ctx.get("dia_chi_so_nha") or ctx.get("DIA_CHI_SO_NHA") or ""
    xa_phuong = ctx.get("dia_chi_xa_phuong") or ctx.get("DIA_CHI_XA_PHUONG") or ""
    quan_huyen = ctx.get("dia_chi_quan_huyen") or ctx.get("DIA_CHI_QUAN_HUYEN") or ""
    tinh_thanh = ctx.get("dia_chi_tinh_thanh") or ctx.get("DIA_CHI_TINH_THANH") or ""
    addr_parts = [p for p in [so_nha, xa_phuong, quan_huyen, tinh_thanh] if p]
    full_addr = ctx.get("dia_chi_day_du") or ctx.get("DIA_CHI_DAY_DU") or ", ".join(addr_parts)

    ctx["dia_chi"] = {
        "so_nha": so_nha,
        "xa_phuong": xa_phuong,
        "quan_huyen": quan_huyen,
        "tinh_thanh": tinh_thanh,
        "day_du": full_addr,
        "full": full_addr
    }
    ctx["dia_chi_day_du"] = full_addr
    ctx["DIA_CHI_DAY_DU"] = full_addr

    # Parse Địa điểm kinh doanh address (DDKD)
    ddkd_sn = ctx.get("ddkd_dia_chi_so_nha") or ctx.get("dia_chi_ddkd_so_nha") or ctx.get("DDKD_DIA_CHI_SO_NHA") or ""
    ddkd_xp = ctx.get("ddkd_dia_chi_xa_phuong") or ctx.get("dia_chi_ddkd_xa_phuong") or ctx.get("DDKD_DIA_CHI_XA_PHUONG") or ""
    ddkd_tt = ctx.get("ddkd_dia_chi_tinh_thanh") or ctx.get("dia_chi_ddkd_tinh_thanh") or ctx.get("DDKD_DIA_CHI_TINH_THANH") or ""
    ddkd_parts = [p for p in [ddkd_sn, ddkd_xp, ddkd_tt] if p]
    ddkd_full = ctx.get("ddkd_dia_chi_day_du") or ctx.get("DDKD_DIA_CHI_DAY_DU") or ", ".join(ddkd_parts)

    ctx["ddkd_dia_chi_so_nha"] = ddkd_sn
    ctx["DDKD_DIA_CHI_SO_NHA"] = ddkd_sn
    ctx["dia_chi_ddkd_so_nha"] = ddkd_sn
    ctx["ddkd_dia_chi_xa_phuong"] = ddkd_xp
    ctx["DDKD_DIA_CHI_XA_PHUONG"] = ddkd_xp
    ctx["dia_chi_ddkd_xa_phuong"] = ddkd_xp
    ctx["ddkd_dia_chi_tinh_thanh"] = ddkd_tt
    ctx["DDKD_DIA_CHI_TINH_THANH"] = ddkd_tt
    ctx["dia_chi_ddkd_tinh_thanh"] = ddkd_tt
    ctx["ddkd_dia_chi_day_du"] = ddkd_full
    ctx["DDKD_DIA_CHI_DAY_DU"] = ddkd_full

    # DDPL normalization
    ddpl_raw = ctx.get("ddpl") if isinstance(ctx.get("ddpl"), dict) else {}
    ddpl_gt = ddpl_raw.get("gioi_tinh") or ctx.get("ddpl_gioi_tinh") or ctx.get("DDPL_GIOI_TINH") or "Nam"
    ddpl_dx = danh_xung(ddpl_gt)
    ddpl_ho_ten = (ddpl_raw.get("ho_ten") or ctx.get("ddpl_ho_ten") or ctx.get("DDPL_HO_TEN") or "").upper()
    ddpl_cccd = ddpl_raw.get("so_cccd") or ctx.get("ddpl_so_cccd") or ctx.get("DDPL_SO_CCCD") or ""
    ddpl_ns = ddpl_raw.get("ngay_sinh") or ctx.get("ddpl_ngay_sinh") or ctx.get("DDPL_NGAY_SINH") or ""
    ddpl_sn = ddpl_raw.get("dia_chi_so_nha") or ctx.get("ddpl_dia_chi_so_nha") or ctx.get("DDPL_DIA_CHI_SO_NHA") or ""
    ddpl_xp = ddpl_raw.get("dia_chi_xa_phuong") or ctx.get("ddpl_dia_chi_xa_phuong") or ctx.get("DDPL_DIA_CHI_XA_PHUONG") or ""
    ddpl_qh = ddpl_raw.get("dia_chi_quan_huyen") or ctx.get("ddpl_dia_chi_quan_huyen") or ctx.get("DDPL_DIA_CHI_QUAN_HUYEN") or ""
    ddpl_tt = ddpl_raw.get("dia_chi_tinh_thanh") or ctx.get("ddpl_dia_chi_tinh_thanh") or ctx.get("DDPL_DIA_CHI_TINH_THANH") or ""
    ddpl_parts = [p for p in [ddpl_sn, ddpl_xp, ddpl_qh, ddpl_tt] if p]
    ddpl_full = ddpl_raw.get("dia_chi_day_du") or ctx.get("ddpl_dia_chi_day_du") or ctx.get("DDPL_DIA_CHI_DAY_DU") or ", ".join(ddpl_parts)

    ddpl_dict = SafeDict({
        "ho_ten": ddpl_ho_ten,
        "gioi_tinh": ddpl_gt,
        "danh_xung": ddpl_dx,
        "so_cccd": ddpl_cccd,
        "ngay_sinh": ddpl_ns,
        "dia_chi_so_nha": ddpl_sn,
        "dia_chi_xa_phuong": ddpl_xp,
        "dia_chi_quan_huyen": ddpl_qh,
        "dia_chi_tinh_thanh": ddpl_tt,
        "dia_chi_day_du": ddpl_full,
        "dia_chi": ddpl_full
    })
    ctx["ddpl"] = ddpl_dict

    # Flatten DDPL
    ctx["ddpl_ho_ten"] = ddpl_ho_ten
    ctx["DDPL_HO_TEN"] = ddpl_ho_ten
    ctx["ddpl_gioi_tinh"] = ddpl_gt
    ctx["DDPL_GIOI_TINH"] = ddpl_gt
    ctx["ddpl_danh_xung"] = ddpl_dx
    ctx["DDPL_DANH_XUNG"] = ddpl_dx
    ctx["ddpl_so_cccd"] = ddpl_cccd
    ctx["DDPL_SO_CCCD"] = ddpl_cccd
    ctx["ddpl_ngay_sinh"] = ddpl_ns
    ctx["DDPL_NGAY_SINH"] = ddpl_ns
    ctx["ddpl_dia_chi_so_nha"] = ddpl_sn
    ctx["DDPL_DIA_CHI_SO_NHA"] = ddpl_sn
    ctx["ddpl_dia_chi_xa_phuong"] = ddpl_xp
    ctx["DDPL_DIA_CHI_XA_PHUONG"] = ddpl_xp
    ctx["ddpl_dia_chi_quan_huyen"] = ddpl_qh
    ctx["DDPL_DIA_CHI_QUAN_HUYEN"] = ddpl_qh
    ctx["ddpl_dia_chi_tinh_thanh"] = ddpl_tt
    ctx["DDPL_DIA_CHI_TINH_THANH"] = ddpl_tt
    ctx["ddpl_dia_chi_day_du"] = ddpl_full
    ctx["DDPL_DIA_CHI_DAY_DU"] = ddpl_full

    # DDPL CŨ normalization
    ddpl_cu_raw = ctx.get("ddpl_cu") if isinstance(ctx.get("ddpl_cu"), dict) else {}
    cu_gt = ddpl_cu_raw.get("gioi_tinh") or ctx.get("ddpl_cu_gioi_tinh") or ctx.get("DDPL_CU_GIOI_TINH") or "Nam"
    cu_dx = danh_xung(cu_gt)
    cu_ht = (ddpl_cu_raw.get("ho_ten") or ctx.get("ddpl_cu_ho_ten") or ctx.get("DDPL_CU_HO_TEN") or "").upper()
    cu_cccd = ddpl_cu_raw.get("so_cccd") or ctx.get("ddpl_cu_so_cccd") or ctx.get("DDPL_CU_SO_CCCD") or ""
    cu_ns = ddpl_cu_raw.get("ngay_sinh") or ctx.get("ddpl_cu_ngay_sinh") or ctx.get("DDPL_CU_NGAY_SINH") or ""
    cu_addr = ddpl_cu_raw.get("dia_chi_day_du") or ctx.get("ddpl_cu_dia_chi_day_du") or ctx.get("DDPL_CU_DIA_CHI_DAY_DU") or ""

    ddpl_cu_dict = SafeDict({
        "ho_ten": cu_ht,
        "gioi_tinh": cu_gt,
        "danh_xung": cu_dx,
        "so_cccd": cu_cccd,
        "ngay_sinh": cu_ns,
        "dia_chi_day_du": cu_addr
    })
    ctx["ddpl_cu"] = ddpl_cu_dict
    ctx["ddpl_cu_danh_xung"] = cu_dx
    ctx["ddpl_cu_ho_ten"] = cu_ht
    ctx["DDPL_CU_HO_TEN"] = cu_ht
    ctx["ddpl_cu_gioi_tinh"] = cu_gt
    ctx["DDPL_CU_GIOI_TINH"] = cu_gt
    ctx["ddpl_cu_so_cccd"] = cu_cccd
    ctx["DDPL_CU_SO_CCCD"] = cu_cccd
    ctx["ddpl_cu_ngay_sinh"] = cu_ns
    ctx["DDPL_CU_NGAY_SINH"] = cu_ns
    ctx["ddpl_cu_dia_chi_day_du"] = cu_addr
    ctx["DDPL_CU_DIA_CHI_DAY_DU"] = cu_addr

    # DDPL MỚI normalization (fallback to DDPL if empty)
    ddpl_moi_raw = ctx.get("ddpl_moi") if isinstance(ctx.get("ddpl_moi"), dict) else {}
    moi_gt = ddpl_moi_raw.get("gioi_tinh") or ctx.get("ddpl_moi_gioi_tinh") or ctx.get("DDPL_MOI_GIOI_TINH") or ddpl_gt
    moi_dx = danh_xung(moi_gt)
    moi_ht = (ddpl_moi_raw.get("ho_ten") or ctx.get("ddpl_moi_ho_ten") or ctx.get("DDPL_MOI_HO_TEN") or ddpl_ho_ten).upper()
    moi_cccd = ddpl_moi_raw.get("so_cccd") or ctx.get("ddpl_moi_so_cccd") or ctx.get("DDPL_MOI_SO_CCCD") or ddpl_cccd
    moi_ns = ddpl_moi_raw.get("ngay_sinh") or ctx.get("ddpl_moi_ngay_sinh") or ctx.get("DDPL_MOI_NGAY_SINH") or ddpl_ns
    moi_addr = ddpl_moi_raw.get("dia_chi_day_du") or ctx.get("ddpl_moi_dia_chi_day_du") or ctx.get("DDPL_MOI_DIA_CHI_DAY_DU") or ddpl_full
    moi_sn, moi_xp, moi_tt = parse_address_str(moi_addr)

    ctx["ddpl_moi_ho_ten"] = moi_ht
    ctx["DDPL_MOI_HO_TEN"] = moi_ht
    ctx["ddpl_moi_gioi_tinh"] = moi_gt
    ctx["DDPL_MOI_GIOI_TINH"] = moi_gt
    ctx["ddpl_moi_so_cccd"] = moi_cccd
    ctx["DDPL_MOI_SO_CCCD"] = moi_cccd
    ctx["ddpl_moi_ngay_sinh"] = moi_ns
    ctx["DDPL_MOI_NGAY_SINH"] = moi_ns
    ctx["ddpl_moi_dia_chi_day_du"] = moi_addr
    ctx["DDPL_MOI_DIA_CHI_DAY_DU"] = moi_addr
    ctx["ddpl_moi_dia_chi_so_nha"] = moi_sn
    ctx["DDPL_MOI_DIA_CHI_SO_NHA"] = moi_sn
    ctx["ddpl_moi_dia_chi_xa_phuong"] = moi_xp
    ctx["DDPL_MOI_DIA_CHI_XA_PHUONG"] = moi_xp
    ctx["ddpl_moi_dia_chi_tinh_thanh"] = moi_tt
    ctx["DDPL_MOI_DIA_CHI_TINH_THANH"] = moi_tt

    # Có thay đổi người đại diện không: so CCCD của ĐDPL cũ và ĐDPL mới (thiếu một trong hai -> giữ mặc định "có")
    if "ddpl_changed" not in ctx and cu_cccd and moi_cccd:
        ctx["ddpl_changed"] = str(cu_cccd).strip() != str(moi_cccd).strip()

    # Capital / Money fields
    von_raw = ctx.get("von_dieu_le_so") or ctx.get("VON_DIEU_LE_SO") or ctx.get("von_dieu_le") or ctx.get("von_moi_so") or ctx.get("VON_MOI_SO") or ""
    if von_raw:
        v_num = re.sub(r"[^\d]", "", str(von_raw))
        if v_num:
            v_fmt = fmt_money(v_num)
            v_chu = so_thanh_chu(v_num)
            ctx["von_dieu_le_so"] = v_fmt
            ctx["VON_DIEU_LE_SO"] = v_fmt
            ctx["von_moi_so"] = v_fmt
            ctx["VON_MOI_SO"] = v_fmt
            v_chu_final = ctx.get("von_dieu_le_chu") or ctx.get("VON_DIEU_LE_CHU") or ctx.get("von_moi_chu") or ctx.get("VON_MOI_CHU") or v_chu
            ctx["von_dieu_le_chu"] = v_chu_final
            ctx["VON_DIEU_LE_CHU"] = v_chu_final
            ctx["von_moi_chu"] = v_chu_final
            ctx["VON_MOI_CHU"] = v_chu_final

    von_cu_raw = ctx.get("von_cu_so") or ctx.get("VON_CU_SO") or ctx.get("von_cu") or ""
    if von_cu_raw:
        vc_num = re.sub(r"[^\d]", "", str(von_cu_raw))
        if vc_num:
            vc_fmt = fmt_money(vc_num)
            vc_chu = so_thanh_chu(vc_num)
            ctx["von_cu_so"] = vc_fmt
            ctx["VON_CU_SO"] = vc_fmt
            ctx["von_cu_chu"] = ctx.get("von_cu_chu") or ctx.get("VON_CU_CHU") or vc_chu
            ctx["VON_CU_CHU"] = ctx["von_cu_chu"]

    # Share count calculations (mệnh giá 10.000 VNĐ/cổ phần)
    v_n = re.sub(r"[^\d]", "", str(ctx.get("von_dieu_le_so") or ""))
    if v_n:
        ctx["so_luong_cp_moi"] = f"{int(v_n) // 10000:,}".replace(',', '.')
    vc_n = re.sub(r"[^\d]", "", str(ctx.get("von_cu_so") or ""))
    if vc_n:
        ctx["so_luong_cp_cu"] = f"{int(vc_n) // 10000:,}".replace(',', '.')

    # Members list (thanh_vien)
    thanh_vien = ctx.get("thanh_vien") or []
    if isinstance(thanh_vien, list):
        norm_tv = []
        tong_von_num = 0
        tong_phieu_num = 0  # cộng phiếu từng người để tổng khớp với các dòng chi tiết
        for idx, tv in enumerate(thanh_vien):
            t_gt = tv.get("gioi_tinh") or "Nam"
            t_dx = danh_xung(t_gt)
            t_ht = (tv.get("ho_ten") or "").upper()
            t_cccd = tv.get("so_cccd") or ""
            t_ns = tv.get("ngay_sinh") or ""
            t_sn = tv.get("dia_chi_so_nha") or ""
            t_xp = tv.get("dia_chi_xa_phuong") or ""
            t_qh = tv.get("dia_chi_quan_huyen") or ""
            t_tt = tv.get("dia_chi_tinh_thanh") or ""
            t_parts = [p for p in [t_sn, t_xp, t_qh, t_tt] if p]
            t_full = tv.get("dia_chi_day_du") or tv.get("dia_chi") or ", ".join(t_parts)

            t_von = tv.get("von_gop") or tv.get("von_so") or ""
            t_von_num = re.sub(r"[^\d]", "", str(t_von))
            t_von_fmt = fmt_money(t_von_num) if t_von_num else t_von
            t_von_chu = so_thanh_chu(t_von_num) if t_von_num else ""
            t_tyle = tv.get("ty_le") or ""

            # Giữ các trường thêm (vd so_gcn, ngay_gcn) rồi ghi đè bằng giá trị đã chuẩn hóa
            item = SafeDict({k: v for k, v in tv.items() if isinstance(k, str)})
            item.update({
                "stt": idx + 1,
                "ho_ten": t_ht,
                "gioi_tinh": t_gt,
                "danh_xung": t_dx,
                "so_cccd": t_cccd,
                "ngay_sinh": t_ns,
                "dia_chi_so_nha": t_sn,
                "dia_chi_xa_phuong": t_xp,
                "dia_chi_quan_huyen": t_qh,
                "dia_chi_tinh_thanh": t_tt,
                "dia_chi_day_du": t_full,
                "dia_chi": t_full,
                "von_gop": t_von_fmt,
                "von_so": t_von_fmt,
                "von_chu": t_von_chu,
                "ty_le": t_tyle,
                # Quy ước 1.000.000 đồng = 1 phiếu biểu quyết (Biên bản họp HĐTV)
                "so_phieu": f"{int(t_von_num) // VND_PER_VOTE:,}".replace(",", ".") if t_von_num else "",
            })
            norm_tv.append(item)
            if t_von_num:
                tong_von_num += int(t_von_num)
                tong_phieu_num += int(t_von_num) // VND_PER_VOTE

            # Export tv1_*, tv2_*, tv_moi_1_*, tv_moi_2_*
            pfx = f"tv{idx+1}_"
            pfx_moi = f"tv_moi_{idx+1}_"
            for k_sub, v_sub in item.items():
                ctx[f"{pfx}{k_sub}"] = v_sub
                ctx[f"{pfx.upper()}{k_sub.upper()}"] = v_sub
                ctx[f"{pfx_moi}{k_sub}"] = v_sub
                ctx[f"{pfx_moi.upper()}{k_sub.upper()}"] = v_sub

        ctx["thanh_vien"] = norm_tv
        if tong_von_num:
            if not ctx.get("tong_von_gop"):
                ctx["tong_von_gop"] = fmt_money(tong_von_num)
            ctx["tong_so_phieu"] = f"{tong_phieu_num:,}".replace(",", ".")

        # DDPL tỷ lệ / tỷ lệ biểu quyết & vốn mới nếu template cần
        ddpl_match = None
        if ddpl_cccd:
            for tv in norm_tv:
                if tv.get("so_cccd") == ddpl_cccd:
                    ddpl_match = tv
                    break
        if not ddpl_match and ddpl_ho_ten:
            for tv in norm_tv:
                if tv.get("ho_ten") == ddpl_ho_ten:
                    ddpl_match = tv
                    break
        if not ddpl_match and norm_tv:
            ddpl_match = norm_tv[0]

        if ddpl_match:
            if not ctx.get("ddpl_ty_le") and not ctx.get("DDPL_TY_LE"):
                ctx["ddpl_ty_le"] = ddpl_match.get("ty_le", "")
                ctx["DDPL_TY_LE"] = ddpl_match.get("ty_le", "")
            if not ctx.get("ddpl_von_gop"):
                ctx["ddpl_von_gop"] = ddpl_match.get("von_gop", "")
            # Chưa nhập giới tính ĐDPL: lấy danh xưng của thành viên tương ứng
            ddpl_gt_input = ddpl_raw.get("gioi_tinh") or raw_data.get("ddpl_gioi_tinh") or raw_data.get("DDPL_GIOI_TINH")
            if not ddpl_gt_input and ddpl_match.get("gioi_tinh"):
                if ddpl_match.get("danh_xung"):
                    ctx["ddpl_danh_xung"] = ddpl_match["danh_xung"]
                    ctx["DDPL_DANH_XUNG"] = ddpl_match["danh_xung"]
            if not ctx.get("ddpl_von_moi_so"):
                ctx["ddpl_von_moi_so"] = ddpl_match.get("von_gop", "")
                ctx["DDPL_VON_MOI_SO"] = ddpl_match.get("von_gop", "")
            # Fallback ngày sinh nếu ĐDPL chưa có ngày sinh
            if not ctx.get("ddpl_ngay_sinh") or not ctx.get("DDPL_NGAY_SINH"):
                m_ns = ddpl_match.get("ngay_sinh", "")
                if m_ns:
                    ctx["ddpl_ngay_sinh"] = m_ns
                    ctx["DDPL_NGAY_SINH"] = m_ns
                    if isinstance(ctx.get("ddpl"), dict):
                        ctx["ddpl"]["ngay_sinh"] = m_ns
            # Fallback số CCCD nếu ĐDPL chưa có
            if not ctx.get("ddpl_so_cccd") or not ctx.get("DDPL_SO_CCCD"):
                m_cccd = ddpl_match.get("so_cccd", "")
                if m_cccd:
                    ctx["ddpl_so_cccd"] = m_cccd
                    ctx["DDPL_SO_CCCD"] = m_cccd
                    if isinstance(ctx.get("ddpl"), dict):
                        ctx["ddpl"]["so_cccd"] = m_cccd
            # Fallback địa chỉ nếu ĐDPL chưa có
            if not ctx.get("ddpl_dia_chi_day_du") or not ctx.get("DDPL_DIA_CHI_DAY_DU"):
                m_addr = ddpl_match.get("dia_chi_day_du") or ddpl_match.get("dia_chi", "")
                if m_addr:
                    ctx["ddpl_dia_chi_day_du"] = m_addr
                    ctx["DDPL_DIA_CHI_DAY_DU"] = m_addr
                    if isinstance(ctx.get("ddpl"), dict):
                        ctx["ddpl"]["dia_chi_day_du"] = m_addr

    # Industry codes (ma_nganh)
    if ma_nganh_list:
        ctx["ma_nganh"] = ma_nganh_list
    elif "ma_nganh" in ctx and isinstance(ctx["ma_nganh"], list):
        pass
    else:
        ctx["ma_nganh"] = []

    # Secretary (Thư ký) fallback
    if not ctx.get("thu_ky_ho_ten"):
        other_sh = [tv.get("ho_ten") for tv in norm_tv if (tv.get("ho_ten") or "").upper() != ddpl_ho_ten] if isinstance(thanh_vien, list) else []
        ctx["thu_ky_ho_ten"] = other_sh[0] if other_sh else ddpl_ho_ten
    if not ctx.get("thu_ky_danh_xung"):
        tk = (ctx.get("thu_ky_ho_ten") or "").upper()
        tk_match = next((tv for tv in norm_tv if tv.get("ho_ten") == tk), None) if isinstance(thanh_vien, list) else None
        if tk_match:
            ctx["thu_ky_danh_xung"] = tk_match.get("danh_xung", "Ông/Bà")
        elif tk and tk == (ddpl_ho_ten or "").upper():
            ctx["thu_ky_danh_xung"] = ctx.get("ddpl_danh_xung") or "Ông/Bà"
        else:
            ctx["thu_ky_danh_xung"] = "Ông/Bà"
    # Địa danh nơi lập văn bản / cơ quan đăng ký (ô chọn tỉnh/thành phố, mặc định Hà Nội)
    ctx.update(dia_ban_context(raw_data.get("tinh_dang_ky")))
    # Người nhận ủy quyền (Bên B của Giấy ủy quyền): cấu hình dùng chung, sửa trên trang quản trị
    from services import uy_quyen
    for k, v in uy_quyen.context_values().items():
        ctx.setdefault(k, v)
    # Ngày lập văn bản: lấy từ trường ngay_lap (DD/MM/YYYY) hoặc ngày hiện tại
    ctx["ngay_lap"] = format_date_vn(raw_data.get("ngay_lap") or None)
    ngay_lap_match = re.search(r"(\d{2}) tháng (\d{2}) năm (\d{4})", ctx["ngay_lap"])
    ctx["ngay_lap_ngan"] = "/".join(ngay_lap_match.groups()) if ngay_lap_match else ""
    ctx["so_luong_co_dong"] = f"{len(norm_tv)}/{len(norm_tv)}" if isinstance(thanh_vien, list) and norm_tv else "3/3"

    # Signer defaults
    if not ctx.get("chuc_danh_ky") and not ctx.get("CHUC_DANH_KY"):
        ctx["chuc_danh_ky"] = "CHỦ SỞ HỮU"
        ctx["CHUC_DANH_KY"] = "CHỦ SỞ HỮU"
    if not ctx.get("chuc_vu_ky") and not ctx.get("CHUC_VU_KY"):
        ctx["chuc_vu_ky"] = "GIÁM ĐỐC"
        ctx["CHUC_VU_KY"] = "GIÁM ĐỐC"

    return ctx

# --- DOCX POST-PROCESSING FOR MEMBER AND MA NGANH TABLES ---

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
        ht = str(sh.get("HO_TEN") or sh.get("ho_ten", "")).upper()
        cells[0].text = ht
        ty_le_str = str(sh.get("TY_LE") or sh.get("ty_le", "0"))
        try:
            ty_le_val = float(ty_le_str.replace('%', '').strip())
        except ValueError:
            ty_le_val = 0.0

        # Tính số cổ phần và số vốn TRƯỚC TĂNG tại Mục IV (Thành phần dự họp)
        if vc_int > 0 and ty_le_val > 0:
            v_cu_sh = int(round(vc_int * (ty_le_val / 100.0)))
            sl_cp_cu = f"{v_cu_sh // 10000:,}".replace(',', '.')
        else:
            v_raw = str(sh.get("VON_GOP") or sh.get("von_gop") or sh.get("von_so", "0"))
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
            ht = str(sh.get("HO_TEN") or sh.get("ho_ten", "")).upper()
            v_raw = str(sh.get("VON_GOP") or sh.get("von_gop") or sh.get("von_so", "0"))
            v_num = re.sub(r'[^\d]', '', v_raw)
            v_fmt = fmt_money(v_num) if v_num else "0"
            v_int = int(v_num) if v_num else 0
            sl_cp = f"{v_int // 10000:,}".replace(',', '.') if v_int else "0"
            ty_le = str(sh.get("TY_LE") or sh.get("ty_le", ""))
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
        ht = str(sh.get("HO_TEN") or sh.get("ho_ten", "")).upper()
        cells[0].text = ht
        ty_le_str = str(sh.get("TY_LE") or sh.get("ty_le", "0"))
        try:
            ty_le_val = float(ty_le_str.replace('%', '').strip())
        except ValueError:
            ty_le_val = 0.0

        # Tính số cổ phần và số vốn TRƯỚC GIẢM tại Mục IV (Thành phần dự họp)
        if vc_int > 0 and ty_le_val > 0:
            v_cu_sh = int(round(vc_int * (ty_le_val / 100.0)))
            sl_cp_cu = f"{v_cu_sh // 10000:,}".replace(',', '.')
        else:
            v_raw = str(sh.get("VON_GOP") or sh.get("von_gop") or sh.get("von_so", "0"))
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
            ht = str(sh.get("HO_TEN") or sh.get("ho_ten", "")).upper()
            v_raw = str(sh.get("VON_GOP") or sh.get("von_gop") or sh.get("von_so", "0"))
            v_num = re.sub(r'[^\d]', '', v_raw)
            v_fmt = fmt_money(v_num) if v_num else "0"
            v_int = int(v_num) if v_num else 0
            sl_cp = f"{v_int // 10000:,}".replace(',', '.') if v_int else "0"
            ty_le = str(sh.get("TY_LE") or sh.get("ty_le", ""))
            p_sh = p_target.insert_paragraph_before(f"- Cổ đông {ht}: sở hữu {sl_cp} cổ phần phổ thông (giá trị {v_fmt} đồng), chiếm {ty_le}% tổng số vốn điều lệ;")
            p_sh.style = 'Normal'

def populate_bbh_tang_von_2tv(doc: docx.Document, members_list: List[Dict[str, Any]]):
    try:
        lines = []
        n = len(members_list)
        lines.append(f"Tham gia cuộc họp có tất cả {n:02d}/{n:02d} thành viên, sở hữu và đại diện cho 100 % vốn điều lệ công ty, cụ thể gồm:")
        for i, m in enumerate(members_list):
            ht = str(m.get("HO_TEN") or m.get("ho_ten", "")).upper()
            v_raw = str(m.get("VON_GOP") or m.get("von_gop") or m.get("von_so", "0"))
            v_num = re.sub(r'[^\d]', '', v_raw)
            v_fmt = fmt_money(v_num) if v_num else "0"
            v_chu = so_thanh_chu(v_num) if v_num else ""
            ty_le = str(m.get("TY_LE") or m.get("ty_le", ""))
            lines.append(f"Họ và tên: {ht}")
            lines.append(f"Số vốn góp: {v_fmt} VNĐ ({v_chu}), chiếm {ty_le}% tổng số vốn điều lệ.")
            lines.append(f"Giấy chứng nhận đăng ký vốn góp số: {i+1:02d}/2026/GCN cấp ngày …./…./20….")

        replace_section_between(doc, "4. Thành phần dự họp:", "Chủ tọa cuộc họp:", lines)

        # Cập nhật đoạn quy ước biểu quyết linh hoạt cho N thành viên
        vote_parts = []
        for m in members_list:
            ht = str(m.get("HO_TEN") or m.get("ho_ten", "")).upper()
            ty_le = str(m.get("TY_LE") or m.get("ty_le", ""))
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
            ht = str(sh.get("HO_TEN") or sh.get("ho_ten", "")).upper()
            cells[1].text = ht
            v_raw = str(sh.get("VON_GOP") or sh.get("von_gop") or sh.get("von_so", "0"))
            v_num = re.sub(r'[^\\d]', '', v_raw)
            v_int = int(v_num) if v_num else 0
            sl_cp = v_int // 10000 if v_int else 0
            total_cp += sl_cp
            total_val += v_int
            sl_cp_str = f"{sl_cp:,}".replace(',', '.')
            v_fmt = f"{v_int:,}".replace(',', '.')
            ty_le = str(sh.get("TY_LE") or sh.get("ty_le", ""))
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
        sh1_ht = str(sh1.get("HO_TEN") or sh1.get("ho_ten", "")).upper()
        sh2_ht = str(sh2.get("HO_TEN") or sh2.get("ho_ten", "")).upper()

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

def complete_person_address(p: Dict[str, Any]) -> Dict[str, Any]:
    """Bổ sung địa chỉ cho một người: có địa chỉ đầy đủ thì tách ra số nhà/xã/tỉnh, và ngược lại."""
    p = dict(p)
    full = p.get("dia_chi_day_du") or p.get("dia_chi") or ""
    parts = [p.get(k, "") for k in ("dia_chi_so_nha", "dia_chi_xa_phuong", "dia_chi_tinh_thanh")]
    if full and not any(parts):
        p["dia_chi_so_nha"], p["dia_chi_xa_phuong"], p["dia_chi_tinh_thanh"] = parse_address_str(full)
    elif not full:
        full = ", ".join(x for x in parts if x)
    p["dia_chi_day_du"] = full
    return p


def resolve_list_refs(schema: Dict[str, Any], context: Dict[str, Any]) -> None:
    """Thay các ô select có options_from trong list (vd chuyen_nhuong[i].ben_a = "1") bằng người được chọn,
    lấy từ danh sách đã chuẩn hóa trong context (thanh_vien đã có dia_chi_day_du...)."""
    from services.schema_engine import resolve_refs

    resolved = resolve_refs(schema, context)
    for step in schema.get("steps", []):
        for f in step.get("fields", []):
            refs = [sub["key"] for sub in f.get("item", []) if sub.get("options_from")]
            if f.get("type") != "list" or not refs or f["key"] not in resolved:
                continue
            items = []
            for item in resolved[f["key"]]:
                for k in refs:
                    item[k] = complete_person_address(item[k])
                    if item[k].get("ho_ten"):
                        item[k]["ho_ten"] = str(item[k]["ho_ten"]).upper()  # tên người viết hoa như các văn bản khác
                items.append(item)
            context[f["key"]] = items
            context[f["key"].upper()] = items


# --- CORE RENDER FUNCTION ---

def render_documents(
    template_name: str,
    raw_data: Dict[str, Any],
    ma_nganh_list: Optional[List[Dict[str, Any]]] = None,
    special_payload: Optional[Dict[str, Any]] = None,
    template_dir: Optional[Path] = None,
) -> bytes:
    """ZIP các file hồ sơ. `template_dir` (tùy chọn): sinh từ thư mục này thay cho bộ mẫu đang dùng,
    vd bản nháp ở trang quản trị (services/template_store.py)."""
    template_dir = Path(template_dir) if template_dir is not None else validate_template_dir(template_name)

    # Merge special_payload into raw_data if provided
    merged_data = dict(raw_data)
    if special_payload:
        if "chuyen_nhuong" in special_payload and special_payload["chuyen_nhuong"]:
            merged_data["chuyen_nhuong"] = special_payload["chuyen_nhuong"]

    schema_path = template_dir / "_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8")) if schema_path.exists() else {}

    if schema.get("prepare"):
        from services import document_rules
        document_rules.PREPARERS[schema["prepare"]](merged_data)

    context = normalize_context(merged_data, ma_nganh_list)
    resolve_list_refs(schema, context)
    jinja_env = create_jinja_env()

    chuyen_nhuong_list = context.get("chuyen_nhuong") or []
    tv_moi_list = context.get("thanh_vien") or []

    # Quy tắc sinh file nằm trong khối "documents" của _schema.json (services/document_rules.py)
    from services import document_rules
    from services.schema_engine import eval_condition

    rule_data = dict(context)
    rule_data.update(
        tv_moi=tv_moi_list,
        chuyen_nhuong=chuyen_nhuong_list,
        ddpl_changed=bool(context.get("ddpl_changed", True)),
    )
    with tempfile.TemporaryDirectory() as tmp_out:
        out_dir = Path(tmp_out)
        render_errors = []

        for entry in document_rules.plan_documents(schema, template_dir):
            fname = entry["file"]
            tpl_file = template_dir / fname
            if not eval_condition(entry.get("when"), rule_data):
                continue
            try:
                # Sinh lặp: một file cho mỗi phần tử (danh sách rỗng -> điền một lần như bình thường)
                items = (rule_data.get(entry["repeat_for"]) or []) if entry.get("repeat_for") else []
                if items:
                    build = document_rules.REPEATERS[entry["repeat_with"]]
                    for i, item in enumerate(items):
                        out_name, sub_ctx = build(context, item, i, items, fname)
                        tpl = DocxTemplate(str(tpl_file))
                        tpl.render(sub_ctx, jinja_env)
                        tpl.save(str(out_dir / out_name))
                    continue

                tpl = DocxTemplate(str(tpl_file))
                tpl.render(context, jinja_env)
                out_path = out_dir / fname
                tpl.save(str(out_path))

                hooks = entry.get("post") or []
                # fill_nganh_table: false -> mẫu tự dựng bảng ngành bằng {%tr for n in ma_nganh %}
                fill_nganh = bool(ma_nganh_list) and entry.get("fill_nganh_table", True)
                if fill_nganh or (hooks and tv_moi_list):
                    doc = docx.Document(str(out_path))
                    if fill_nganh:
                        populate_ma_nganh_table(doc, ma_nganh_list)
                    if tv_moi_list:
                        for hook in hooks:
                            document_rules.HOOKS[hook](doc, context, tv_moi_list)
                    doc.save(str(out_path))

            except Exception as e:
                err_msg = f"{fname}: {type(e).__name__} - {str(e)}"
                logger.exception("Lỗi khi render %s", fname)
                render_errors.append(err_msg)

        docx_count = len([f for f in out_dir.iterdir() if f.is_file() and f.suffix == ".docx"])
        if render_errors:
            if docx_count == 0:
                raise RuntimeError("Toàn bộ tài liệu render thất bại:\n" + "\n".join(render_errors))
            warning_file = out_dir / "_CANH_BAO_LOI_HO_SO.txt"
            with open(warning_file, "w", encoding="utf-8") as wf:
                wf.write("CẢNH BÁO QUAN TRỌNG TỪ HỆ THỐNG:\n")
                wf.write("=" * 50 + "\n")
                wf.write("Một số file trong bộ hồ sơ gặp lỗi trong quá trình tự động điền và không thể xuất bản:\n\n")
                for err in render_errors:
                    wf.write(f"- {err}\n")
                wf.write("\nCác file còn lại vẫn được điền thành công. Vui lòng kiểm tra lại thông tin đầu vào.\n")

        # Áp dụng tiêu chuẩn văn bản hành chính (Times New Roman, xóa highlight, chuẩn hóa font)
        from services.docx_standardizer import standardize_document
        for f in out_dir.iterdir():
            if f.is_file() and f.suffix == ".docx":
                try:
                    doc = docx.Document(str(f))
                    standardize_document(doc)
                    doc.save(str(f))
                except Exception as e:
                    logger.exception("Lỗi chuẩn hóa văn bản %s", f.name)

        # Pack into ZIP
        zip_buf = BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(out_dir.iterdir()):
                if f.is_file():
                    zf.write(str(f), arcname=f.name)

        return zip_buf.getvalue()
