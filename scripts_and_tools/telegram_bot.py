import os
import shutil
import zipfile
import tempfile
import json
import asyncio
import base64
import time
import httpx
import pythoncom
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import win32com.client
from wizard_cn2tv import (
    get_wizard, handle_wizard_start, handle_wizard_message,
    handle_wizard_callback, handle_wizard_vneid
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
BASE_DIR = r"c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word"
MA_NGANH_JSON = os.path.join(BASE_DIR, "ma_nganh_nghe.json")
PROFILES_JSON  = os.path.join(BASE_DIR, "company_profiles.json")

# Các trường lưu vào profile (thông tin ổn định của công ty)
PROFILE_FIELDS = [
    "TEN_CONG_TY_VN", "TEN_CONG_TY_EN", "TEN_CONG_TY_VIET_TAT", "MA_SO_THUE",
    "DIA_CHI_SO_NHA", "DIA_CHI_XA_PHUONG", "DIA_CHI_QUAN_HUYEN", "DIA_CHI_TINH_THANH",
    "SDT_CONG_TY", "EMAIL_CONG_TY",
    "DDPL_HO_TEN", "DDPL_NGAY_SINH", "DDPL_SO_CCCD", "DDPL_GIOI_TINH",
    "DDPL_DIA_CHI_SO_NHA", "DDPL_DIA_CHI_XA_PHUONG", "DDPL_DIA_CHI_QUAN_HUYEN",
    "DDPL_DIA_CHI_TINH_THANH", "DDPL_DIA_CHI_DAY_DU",
    "VON_DIEU_LE_SO", "VON_DIEU_LE_CHU",
]

DKKD_SECTIONS = {
    "A1": "Thay đổi tên doanh nghiệp",
    "A2": "Thay đổi địa chỉ trụ sở chính",
    "A3": "Thay đổi thành viên CT TNHH",
    "A4": "Thay đổi vốn điều lệ",
    "A5": "Thay đổi ngành, nghề KD",
    "A6": "Thay đổi thông tin đăng ký thuế",
    "A7": "Thay đổi chủ sở hữu hưởng lợi",
}

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
    "Doanh nghiệp cam kết hoàn toàn chịu trách nhiệm",
    "Điều 2.",
]

DKKD_COMPANY_TYPES = {
    "1tv": {"label": "Công ty TNHH 1 TV", "CHUC_DANH_KY": "CHỦ SỞ HỮU", "CHUC_VU_KY": "GIÁM ĐỐC"},
    "2tv": {"label": "Công ty TNHH 2 TV", "CHUC_DANH_KY": "HỘI ĐỒNG THÀNH VIÊN", "CHUC_VU_KY": "GIÁM ĐỐC"},
    "cp":  {"label": "Công ty Cổ Phần", "CHUC_DANH_KY": "ĐẠI HỘI ĐỒNG CỔ ĐÔNG", "CHUC_VU_KY": "GIÁM ĐỐC"},
}

# ===================== BẢNG ROUTING TEMPLATE =====================
# (loai_hinh, thu_tuc) → tên folder (bỏ prefix "Mẫu ")
TEMPLATE_ROUTE = {
    # --- TLM (Thành lập mới) ---
    ("cp",  "tlm"): "Thành lập mới công ty Cổ Phần",
    ("1tv", "tlm"): "Thành lập mới công  ty TNHH 1 TV",
    ("2tv", "tlm"): "Thành lập mới công ty TNHH 2 TV",
    ("dkkd","tlm"): "Thành lập mới địa điểm kinh doanh",
    # --- Tạm ngừng ---
    ("cp",  "tam_ngung"): "Tạm dừng công ty Cổ Phần",
    ("1tv", "tam_ngung"): "Tạm dừng công ty TNHH 1 TV",
    ("2tv", "tam_ngung"): "Tạm dừng công ty TNHH 2 TV",
    # --- Giải thể ---
    ("cp",  "giai_the"): "Giải thể công ty Cổ Phần",
    ("1tv", "giai_the"): "Giải thể công ty TNHH 1 TV",
    ("2tv", "giai_the"): "Giải thể công ty TNHH 2 TV",
    # --- Hoạt động lại ---
    ("cp",  "hoat_dong_lai"): "Hoạt động lại trước thời hạn",
    ("1tv", "hoat_dong_lai"): "Hoạt động lại trước thời hạn",
    ("2tv", "hoat_dong_lai"): "Hoạt động lại trước thời hạn",
    # --- Thay đổi nội dung ĐKDN ---
    ("cp",  "thay_doi_dkkd"): "Thay đổi nội dung ĐKKD",
    ("1tv", "thay_doi_dkkd"): "Thay đổi nội dung ĐKKD",
    ("2tv", "thay_doi_dkkd"): "Thay đổi nội dung ĐKKD",
    # --- Chuyển nhượng ---
    ("1tv", "chuyen_nhuong"): "Chuyển nhượng công ty TNHH 1 TV",
    ("2tv", "chuyen_nhuong"): "Chuyển nhượng Công ty TNHH 2 TV",
    # --- Chuyển đổi loại hình ---
    ("1tv", "chuyen_doi"): "Chuyển đổi loại hình 1TV sang 2 TV",
    # --- Tăng vốn ---
    ("cp",  "tang_von"): "tăng vốn công ty cổ phần",
    ("2tv", "tang_von"): "tăng vốn công ty TNHH 2TV",
    # --- Chấm dứt ĐĐKD ---
    ("cp",  "cham_dut_ddkd"): "Chấm dứt hoạt động địa điểm kinh doanh",
    ("1tv", "cham_dut_ddkd"): "Chấm dứt hoạt động địa điểm kinh doanh",
    ("2tv", "cham_dut_ddkd"): "Chấm dứt hoạt động địa điểm kinh doanh",
    # --- Cấp lại ĐKKD ---
    ("cp",  "cap_lai"): "Cấp lại giấy đăng ký kinh doanh",
    ("1tv", "cap_lai"): "Cấp lại giấy đăng ký kinh doanh",
    ("2tv", "cap_lai"): "Cấp lại giấy đăng ký kinh doanh",
}

# Thủ tục nhánh "Thay đổi" — hiện sau khi tra MST + biết loại hình
PROCEDURES_THAY_DOI = [
    ("tam_ngung",    "⏸️ Tạm ngừng"),
    ("giai_the",     "🗑️ Giải thể"),
    ("hoat_dong_lai","▶️ Hoạt động lại"),
    ("thay_doi_dkkd","📝 Thay đổi nội dung ĐKKD"),
    ("chuyen_nhuong","🔄 Chuyển nhượng"),
    ("chuyen_doi",   "🔀 Chuyển đổi loại hình"),
    ("tang_von",     "💰 Tăng vốn"),
    ("cham_dut_ddkd","📍 Chấm dứt ĐĐKD"),
    ("cap_lai",      "📄 Cấp lại ĐKKD"),
]


def detect_company_type(company_name):
    """Nhận diện loại hình DN từ tên công ty trả về từ API."""
    name = company_name.upper()
    if "MỘT THÀNH VIÊN" in name or "1 THÀNH VIÊN" in name:
        return "1tv"
    if "CỔ PHẦN" in name:
        return "cp"
    if "TNHH" in name or "TRÁCH NHIỆM HỮU HẠN" in name:
        return "2tv"  # TNHH mà không phải 1TV → 2TV
    return None

# ===================== HELPERS =====================

def load_profiles():
    """Đọc danh sách profile công ty đã lưu."""
    if os.path.exists(PROFILES_JSON):
        with open(PROFILES_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_company_profile(mst, replacements):
    """Lưu profile công ty theo MST."""
    profiles = load_profiles()
    profile = {k: replacements.get(k, "") for k in PROFILE_FIELDS if replacements.get(k)}
    profile["_saved_at"] = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")
    profiles[mst] = profile
    with open(PROFILES_JSON, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)

def delete_company_profile(mst):
    """Xóa profile công ty."""
    profiles = load_profiles()
    if mst in profiles:
        del profiles[mst]
        with open(PROFILES_JSON, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        return True
    return False


def get_templates():
    templates = []
    if os.path.exists(BASE_DIR):
        for f in os.listdir(BASE_DIR):
            if os.path.isdir(os.path.join(BASE_DIR, f)) and f.startswith("Mẫu "):
                templates.append(f.replace("Mẫu ", ""))
    return templates

def get_template_keys(template_name):
    json_path = os.path.join(BASE_DIR, "folder_keys.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(template_name, [])
    return []

def load_ma_nganh():
    if os.path.exists(MA_NGANH_JSON):
        with open(MA_NGANH_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def build_vneid_prefilled(context):
    """Tạo dict dữ liệu từ VNeID đã lưu để điền sẵn vào form"""
    ddpl = context.user_data.get("ddpl_info", {})
    tv2  = context.user_data.get("tv2_info", {})
    d = {
        "DDPL_HO_TEN":             ddpl.get("ho_ten", ""),
        "DDPL_NGAY_SINH":          ddpl.get("ngay_sinh", ""),
        "DDPL_SO_CCCD":            ddpl.get("so_cccd", ""),
        "DDPL_GIOI_TINH":          ddpl.get("gioi_tinh", ""),
        "DDPL_DIA_CHI_SO_NHA":     ddpl.get("dia_chi_so_nha", ""),
        "DDPL_DIA_CHI_XA_PHUONG":  ddpl.get("dia_chi_xa_phuong", ""),
        "DDPL_DIA_CHI_QUAN_HUYEN": ddpl.get("dia_chi_quan_huyen", ""),
        "DDPL_DIA_CHI_TINH_THANH": ddpl.get("dia_chi_tinh_thanh", ""),
        "DDPL_DIA_CHI_DAY_DU":     ddpl.get("dia_chi", ""),
        "TV2_HO_TEN":              tv2.get("ho_ten", ""),
        "TV2_NGAY_SINH":           tv2.get("ngay_sinh", ""),
        "TV2_SO_CCCD":             tv2.get("so_cccd", ""),
        "TV2_DIA_CHI_SO_NHA":      tv2.get("dia_chi_so_nha", ""),
        "TV2_DIA_CHI_XA_PHUONG":   tv2.get("dia_chi_xa_phuong", ""),
        "TV2_DIA_CHI_QUAN_HUYEN":  tv2.get("dia_chi_quan_huyen", ""),
        "TV2_DIA_CHI_TINH_THANH":  tv2.get("dia_chi_tinh_thanh", ""),
        "TV2_DIA_CHI_DAY_DU":      tv2.get("dia_chi", ""),
    }
    if context.user_data.get("selected_ma_nganh"):
        d["MA_NGANH_NGHE"] = context.user_data["selected_ma_nganh"]
    return d

def build_prefilled_form(template_name, keys, context):
    """Tạo bảng form đã điền sẵn từ VNeID + profile công ty, trả về (form_text, empty_keys)"""
    pre = build_vneid_prefilled(context)
    # Merge auto-fields từ ĐKKD (loại hình công ty)
    dkkd_auto = context.user_data.get("dkkd_auto_fields", {})
    for k, v in dkkd_auto.items():
        if v:
            pre[k] = v
    # Merge profile công ty (ưu tiên thấp hơn VNeID)
    profile_data = context.user_data.get("loaded_profile", {})
    for k, v in profile_data.items():
        if v and not pre.get(k):  # chỉ điền nếu VNeID chưa có
            pre[k] = v
    form_lines = [f"Mẫu: {template_name}"]
    empty_keys = []
    for k in keys:
        val = pre.get(k, "")
        form_lines.append(f"{k}: {val}")
        if not val:
            empty_keys.append(k)
    return "\n".join(form_lines), empty_keys

def backup_template_folder(template_dir):
    """Tự động backup folder mẫu gốc trước khi chuẩn hóa."""
    import datetime
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(template_dir, f"_backup_{date_str}")
    os.makedirs(backup_dir, exist_ok=True)
    for f in os.listdir(template_dir):
        if f.startswith("_backup"):
            continue
        src = os.path.join(template_dir, f)
        if os.path.isfile(src) and (f.endswith(".doc") or f.endswith(".docx")):
            shutil.copy2(src, os.path.join(backup_dir, f))
    return backup_dir


def scan_remaining_placeholders(folder_path):
    """Quét các placeholder [KEY] còn sót trong file Word sau khi điền."""
    import re
    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    remaining = {}  # {filename: [key1, key2, ...]}
    try:
        files = [f for f in os.listdir(folder_path) if (f.endswith(".doc") or f.endswith(".docx")) and not f.startswith("~$")]
        for fname in files:
            fpath = os.path.join(folder_path, fname)
            doc = None
            for attempt in range(3):
                try:
                    doc = word.Documents.Open(fpath, ReadOnly=True, ConfirmConversions=False)
                    break
                except:
                    time.sleep(1)
            if not doc:
                continue
            text = doc.Content.Text
            doc.Close(False)
            found = re.findall(r'\[([A-Z][A-Z0-9_]{2,})\]', text)
            if found:
                remaining[fname] = list(dict.fromkeys(found))  # unique, preserve order
    finally:
        word.Quit()
    return remaining


def process_word_files(folder_path, replacements, dkkd_selected=None):
    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    wdYellow = 7
    wdFindStop = 0

    try:
        files = [f for f in os.listdir(folder_path) if f.endswith(".doc") or f.endswith(".docx")]
        for file in files:
            if file.startswith("~$"): continue
            path = os.path.join(folder_path, file)
            # Retry mở file nếu Word đang bận (lỗi COM -2147418111)
            doc = None
            for attempt in range(5):
                try:
                    doc = word.Documents.Open(
                        path,
                        ReadOnly=False,
                        ConfirmConversions=False,
                        Format=0
                    )
                    break
                except Exception as e:
                    if attempt < 4:
                        time.sleep(1)
                    else:
                        raise
            if doc is None:
                continue

            possible_keys = [
                "TEN_CONG_TY_VN", "TEN_CONG_TY_EN", "TEN_CONG_TY_VIET_TAT", "MA_SO_THUE",
                "DIA_CHI_SO_NHA", "DIA_CHI_XA_PHUONG", "DIA_CHI_QUAN_HUYEN", "DIA_CHI_TINH_THANH",
                "DDPL_HO_TEN", "DDPL_SO_CCCD", "DDPL_NGAY_SINH", "DDPL_GIOI_TINH",
                "DDPL_DIA_CHI_SO_NHA", "DDPL_DIA_CHI_XA_PHUONG", "DDPL_DIA_CHI_TINH_THANH",
                "DDPL_DIA_CHI_QUAN_HUYEN", "DDPL_DIA_CHI_DAY_DU",
                "VON_DIEU_LE_SO", "VON_DIEU_LE_CHU", "SDT_CONG_TY", "EMAIL_CONG_TY",
                "DDPL_CU_HO_TEN", "DDPL_CU_NGAY_SINH", "DDPL_CU_SO_CCCD", "DDPL_CU_DIA_CHI_DAY_DU",
                "NGUOI_DUOC_UY_QUYEN_HO_TEN", "NGUOI_DUOC_UY_QUYEN_CCCD", "NGUOI_DUOC_UY_QUYEN_NGAY_SINH",
                "NGUOI_DUOC_UY_QUYEN_DIA_CHI", "NGUOI_DUOC_UY_QUYEN_SDT", "NGUOI_DUOC_UY_QUYEN_EMAIL",
                "VON_CU_SO", "VON_CU_CHU", "VON_MOI_SO", "VON_MOI_CHU",
                "DDPL_DIA_CHI_DAY_DU", "DDPL_VON_CU_SO", "DDPL_VON_CU_CHU", "DDPL_VON_MOI_SO", "DDPL_TY_LE",
                "TV2_HO_TEN", "TV2_NGAY_SINH", "TV2_SO_CCCD", "TV2_GIOI_TINH",
                "TV2_DIA_CHI_DAY_DU", "TV2_DIA_CHI_SO_NHA",
                "TV2_DIA_CHI_XA_PHUONG", "TV2_DIA_CHI_QUAN_HUYEN", "TV2_DIA_CHI_TINH_THANH",
                "TV2_VON_CU_SO", "TV2_VON_CU_CHU", "TV2_VON_CU_MOI", "TV2_VON_MOI_SO", "TV2_VON_MOI_CHU", "TV2_TY_LE",
                "MA_NGANH_NGHE",
                "NAM", "SO_QUYET_DINH", "SO_GIAY_CHUNG_NHAN",
                "TEN_CONG_TY_NN", "TEN_CONG_TY_VIET_TAT",
                "CHUC_DANH_KY", "CHUC_VU_KY",
            ]
            for pk in possible_keys:
                if pk not in replacements:
                    replacements[pk] = ""

            for key, val in replacements.items():
                placeholder = f"[{key}]"
                for story in doc.StoryRanges:
                    while story:
                        rng = story.Duplicate
                        while True:
                            rng.Find.ClearFormatting()
                            rng.Find.Text = placeholder
                            rng.Find.Forward = True
                            rng.Find.Wrap = wdFindStop
                            rng.Find.Format = False
                            rng.Find.MatchCase = False
                            rng.Find.MatchWholeWord = False
                            rng.Find.MatchWildcards = False
                            rng.Find.MatchSoundsLike = False
                            rng.Find.MatchAllWordForms = False
                            found = rng.Find.Execute()
                            if not found:
                                break
                            rng.Text = val
                            rng.HighlightColorIndex = wdYellow
                            rng.Collapse(0)
                        story = story.NextStoryRange

            # Dọn dấu phẩy thừa
            for story in doc.StoryRanges:
                while story:
                    for old, new in [(" ,", ","), (", ,", ","), (": ,", ": "), (":,", ": ")]:
                        rng = story.Duplicate
                        rng.Find.Execute(old, False, False, False, False, False, True, 1, False, new, 2)
                    story = story.NextStoryRange

            # Điền bảng mã ngành nghề (nếu có list mã ngành)
            if "MA_NGANH_NGHE_LIST" in replacements:
                nganh_list = replacements["MA_NGANH_NGHE_LIST"]
                for table in doc.Tables:
                    try:
                        row1_text = [cell.Range.Text.strip().replace('\r\a', '').replace('\r', '') for cell in table.Rows(1).Cells]
                        if 'Mã ngành' in row1_text and 'Tên ngành' in row1_text:
                            col_stt = row1_text.index('STT') + 1 if 'STT' in row1_text else None
                            col_ten = row1_text.index('Tên ngành') + 1 if 'Tên ngành' in row1_text else None
                            col_ma = row1_text.index('Mã ngành') + 1 if 'Mã ngành' in row1_text else None
                            col_chinh = row1_text.index('Ngành nghề kinh doanh chính') + 1 if 'Ngành nghề kinh doanh chính' in row1_text else None
                            
                            while table.Rows.Count > 1:
                                table.Rows(2).Delete()
                            
                            for i, nganh in enumerate(nganh_list):
                                new_row = table.Rows.Add()
                                new_row.Range.HighlightColorIndex = 7 # wdYellow
                                if col_stt:
                                    new_row.Cells(col_stt).Range.Text = str(i + 1)
                                    new_row.Cells(col_stt).Range.HighlightColorIndex = 7
                                if col_ten:
                                    new_row.Cells(col_ten).Range.Text = nganh['ten']
                                    new_row.Cells(col_ten).Range.HighlightColorIndex = 7
                                if col_ma:
                                    new_row.Cells(col_ma).Range.Text = nganh['ma']
                                    new_row.Cells(col_ma).Range.HighlightColorIndex = 7
                                if col_chinh and i == 0:
                                    new_row.Cells(col_chinh).Range.Text = 'X'
                                    new_row.Cells(col_chinh).Range.HighlightColorIndex = 7
                    except Exception:
                        pass

            # Xóa các mục ĐKKD không được chọn
            if dkkd_selected is not None:
                remove_unselected_sections(doc, dkkd_selected)

            doc.Save()
            doc.Close(False)
    finally:
        word.Quit()


def remove_unselected_sections(doc, selected_sections):
    """Xóa các mục ĐKKD không được chọn khỏi document."""
    found = []
    for code, marker in DKKD_SECTION_MARKERS:
        rng = doc.Content.Duplicate
        rng.Find.ClearFormatting()
        rng.Find.Text = marker
        rng.Find.Forward = True
        rng.Find.Wrap = 0
        rng.Find.MatchCase = False
        if rng.Find.Execute():
            para_start = rng.Paragraphs(1).Range.Start
            found.append((code, para_start))

    if not found:
        return

    found.sort(key=lambda x: x[1])

    end_pos = doc.Content.End
    for em in DKKD_END_MARKERS:
        rng = doc.Content.Duplicate
        rng.Find.ClearFormatting()
        rng.Find.Text = em
        rng.Find.Forward = True
        rng.Find.Wrap = 0
        if rng.Find.Execute():
            end_pos = rng.Paragraphs(1).Range.Start
            break

    to_delete = []
    for i, (code, start) in enumerate(found):
        if code not in selected_sections:
            end = found[i + 1][1] if i + 1 < len(found) else end_pos
            to_delete.append((start, end))

    for start, end in reversed(to_delete):
        if end > start:
            doc.Range(start, end).Delete()


def build_dkkd_keyboard(selected):
    """Tạo InlineKeyboard multi-select cho các mục ĐKKD."""
    keyboard = []
    for code, name in DKKD_SECTIONS.items():
        icon = "✅" if code in selected else "⬜"
        keyboard.append([InlineKeyboardButton(f"{icon} {code}. {name}", callback_data=f"dkkd_{code}")])
    keyboard.append([InlineKeyboardButton("📋 Xác nhận chọn", callback_data="dkkd_confirm")])
    return InlineKeyboardMarkup(keyboard)


# ===================== SEARCH MÃ NGÀNH (LOCAL) =====================

def normalize_vi(text: str) -> str:
    VIET_MAP = {
        'à':'a','á':'a','ả':'a','ã':'a','ạ':'a',
        'ă':'a','ắ':'a','ặ':'a','ằ':'a','ẳ':'a','ẵ':'a',
        'â':'a','ấ':'a','ầ':'a','ẩ':'a','ẫ':'a','ậ':'a',
        'è':'e','é':'e','ẻ':'e','ẽ':'e','ẹ':'e',
        'ê':'e','ế':'e','ề':'e','ể':'e','ễ':'e','ệ':'e',
        'ì':'i','í':'i','ỉ':'i','ĩ':'i','ị':'i',
        'ò':'o','ó':'o','ỏ':'o','õ':'o','ọ':'o',
        'ô':'o','ố':'o','ồ':'o','ổ':'o','ỗ':'o','ộ':'o',
        'ơ':'o','ớ':'o','ờ':'o','ở':'o','ỡ':'o','ợ':'o',
        'ù':'u','ú':'u','ủ':'u','ũ':'u','ụ':'u',
        'ư':'u','ứ':'u','ừ':'u','ử':'u','ữ':'u','ự':'u',
        'ỳ':'y','ý':'y','ỷ':'y','ỹ':'y','ỵ':'y','đ':'d',
        'À':'a','Á':'a','Ả':'a','Ã':'a','Ạ':'a',
        'Ă':'a','Ắ':'a','Ặ':'a','Ằ':'a','Ẳ':'a','Ẵ':'a',
        'Â':'a','Ấ':'a','Ầ':'a','Ẩ':'a','Ẫ':'a','Ậ':'a',
        'È':'e','É':'e','Ẻ':'e','Ẽ':'e','Ẹ':'e',
        'Ê':'e','Ế':'e','Ề':'e','Ể':'e','Ễ':'e','Ệ':'e',
        'Ì':'i','Í':'i','Ỉ':'i','Ĩ':'i','Ị':'i',
        'Ò':'o','Ó':'o','Ỏ':'o','Õ':'o','Ọ':'o',
        'Ô':'o','Ố':'o','Ồ':'o','Ổ':'o','Ỗ':'o','Ộ':'o',
        'Ơ':'o','Ớ':'o','Ờ':'o','Ở':'o','Ỡ':'o','Ợ':'o',
        'Ù':'u','Ú':'u','Ủ':'u','Ũ':'u','Ụ':'u',
        'Ư':'u','Ứ':'u','Ừ':'u','Ử':'u','Ữ':'u','Ự':'u',
        'Ỳ':'y','Ý':'y','Ỷ':'y','Ỹ':'y','Ỵ':'y','Đ':'d',
    }
    return text.lower().translate(str.maketrans(VIET_MAP))


async def search_ma_nganh_ai(mo_ta: str) -> tuple[str, list]:
    """Gọi Gemini AI (có Google Search) để lấy mã ngành gợi ý và tư vấn, sau đó map với bảng 2026"""
    prompt = f"""Tôi đang tìm mã ngành nghề kinh doanh cấp 4 hoặc cấp 5 tại Việt Nam cho hoạt động sau: "{mo_ta}".
Sử dụng công cụ tìm kiếm Google để tìm kiếm các văn bản, hướng dẫn mới nhất về mã ngành nghề này (theo Quyết định 27/2018/QĐ-TTg).
Yêu cầu trả về đúng định dạng sau:
[TU_VAN]
Viết đoạn tư vấn tóm tắt (giống Google AI Overview) về mã ngành chính xác nhất và các mã ngành liên quan, các trường hợp ngoại trừ.
Lưu ý: Nếu cần in đậm hãy dùng thẻ <b>, in nghiêng dùng thẻ <i>. KHÔNG DÙNG markdown (**, *).
[/TU_VAN]
[MA_NGANH]
["mã_số_1", "mã_số_2", "mã_số_3", "mã_số_4", "mã_số_5"]
[/MA_NGANH]
Lưu ý: Phần [MA_NGANH] CHỈ trả về một mảng JSON các mã số dạng chuỗi (không giải thích thêm)."""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"googleSearch": {}}]
    }
    
    suggested_codes = []
    tu_van_text = ""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                
                # Bóc tách TU_VAN
                if "[TU_VAN]" in text and "[/TU_VAN]" in text:
                    tu_van_text = text.split("[TU_VAN]")[1].split("[/TU_VAN]")[0].strip()
                
                # Bóc tách MA_NGANH
                if "[MA_NGANH]" in text and "[/MA_NGANH]" in text:
                    json_text = text.split("[MA_NGANH]")[1].split("[/MA_NGANH]")[0].strip()
                    json_text = json_text.replace("```json", "").replace("```", "").strip()
                    suggested_codes = json.loads(json_text)
    except Exception as e:
        print(f"Lỗi gọi Gemini search mã ngành: {e}")
        pass
    
    all_nganh = load_ma_nganh()
    nganh_cap5 = [n for n in all_nganh if len(n.get("ma", "")) == 5]
    
    results = []
    seen = set()
    
    # 1. Map từ gợi ý của AI vào file JSON
    if suggested_codes and isinstance(suggested_codes, list):
        for code in suggested_codes:
            code = str(code).strip()
            if not code: continue
            for n in nganh_cap5:
                # Trùng khớp chính xác cấp 5 HOẶC trùng tiền tố (nếu AI trả về cấp 3, cấp 4)
                if n["ma"] == code or (len(code) < 5 and n["ma"].startswith(code)):
                    if n["ma"] not in seen:
                        results.append({"ma": n["ma"], "ten": n["ten"], "ly_do": "AI Đề xuất"})
                        seen.add(n["ma"])
            if len(results) >= 5:
                break
    
    # 2. Fallback tìm kiếm local (từ khóa) nếu AI không trả về hoặc chưa đủ 5 mã
    if len(results) < 5:
        mo_ta_norm = normalize_vi(mo_ta)
        keywords = [kw for kw in mo_ta_norm.split() if len(kw) >= 2]

        scored = []
        for n in nganh_cap5:
            if n["ma"] in seen: continue
            ten_norm = normalize_vi(n["ten"])
            score = 0
            for kw in keywords:
                if kw in ten_norm:
                    score += len(kw)
            if mo_ta_norm in ten_norm:
                score += 20
            words = ten_norm.split()
            if words and keywords and any(k in words[:3] for k in keywords):
                score += 5
            if score > 0:
                scored.append((score, n))

        scored.sort(key=lambda x: x[0], reverse=True)
        for score, n in scored:
            results.append({"ma": n["ma"], "ten": n["ten"], "ly_do": "Khớp từ khóa"})
            seen.add(n["ma"])
            if len(results) >= 5:
                break

    return tu_van_text, results[:5]


# ===================== GEMINI VISION - ĐỌC ẢNH VNEID =====================

async def extract_vneid_info(image_bytes: bytes) -> dict:
    """Dùng Gemini Vision để trích xuất thông tin từ ảnh VNeID"""
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = """Đây là ảnh chụp màn hình VNeID (ứng dụng căn cước công dân điện tử của Việt Nam).
Hãy trích xuất chính xác các thông tin sau và trả về JSON thuần túy (không có markdown, không có ```json):
{
  "ho_ten": "họ và tên đầy đủ",
  "ngay_sinh": "ngày sinh định dạng DD/MM/YYYY",
  "gioi_tinh": "Nam hoặc Nữ",
  "so_cccd": "số căn cước công dân (12 chữ số)",
  "dia_chi": "địa chỉ thường trú đầy đủ (nguyên văn)",
  "dia_chi_so_nha": "phần địa chỉ cụ thể: số nhà, ngõ, thôn, xóm, tổ dân phố (KHÔNG bao gồm xã/phường và tỉnh/thành)",
  "dia_chi_xa_phuong": "tên xã hoặc phường hoặc thị trấn (ví dụ: Xã Đông Anh, Phường Cầu Giấy)",
  "dia_chi_quan_huyen": "tên quận hoặc huyện hoặc thị xã nếu có (ví dụ: Huyện Đông Anh, Quận Cầu Giấy), để trống nếu không có",
  "dia_chi_tinh_thanh": "tên tỉnh hoặc thành phố (ví dụ: Thành Phố Hà Nội, Tỉnh Bắc Ninh)"
}
Ví dụ địa chỉ 'Tiên Hội, Xã Đông Anh, Thành Phố Hà Nội' thì:
- dia_chi_so_nha = 'Tiên Hội'
- dia_chi_xa_phuong = 'Xã Đông Anh'
- dia_chi_quan_huyen = ''
- dia_chi_tinh_thanh = 'Thành Phố Hà Nội'
Nếu không tìm thấy thông tin nào, để trống chuỗi "". Chỉ trả về JSON, không thêm gì khác."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}}
            ]
        }]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code != 200:
            err_msg = resp.text
            raise Exception(f"Gemini API Error {resp.status_code}: {err_msg}")
        data = resp.json()

    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)



# ===================== BOT HANDLERS =====================

async def handle_wizard_callback_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wrapper cho wizard callback."""
    handled = await handle_wizard_callback(update, context)
    if not handled:
        await update.callback_query.answer("❌ Wizard không hoạt động. /start để bắt đầu lại.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏢 Thành lập mới", callback_data="nav_tlm")],
        [InlineKeyboardButton("📝 Thay đổi / Thủ tục khác", callback_data="nav_thaydoi")],
    ])
    welcome = (
        "Xin chào! Tôi là <b>Trợ Lý Hồ Sơ Tự Động</b> 🤖\n\n"
        "📋 Chọn nhóm thủ tục bên dưới:\n\n"
        "🏢 <b>Thành lập mới</b> — Đăng ký DN / ĐĐKD mới\n"
        "📝 <b>Thay đổi / Thủ tục khác</b> — Tạm ngừng, giải thể, chuyển nhượng...\n\n"
        "💡 <i>Bạn cũng có thể:</i>\n"
        "📸 Gửi ảnh VNeID để trích xuất thông tin\n"
        "/nganh [mô tả] — Tra mã ngành nghề\n"
        "/profiles — Xem & nạp profile công ty đã lưu\n"
        "/reset — Xóa dữ liệu phiên làm việc"
    )
    await update.message.reply_text(welcome, parse_mode='HTML', reply_markup=keyboard)

    # Thanh nút cố định dưới cùng chat
    persistent_kb = ReplyKeyboardMarkup(
        [
            [KeyboardButton("🏠 Menu chính"), KeyboardButton("📂 Profiles")],
            [KeyboardButton("🔍 Tra mã ngành"), KeyboardButton("🔄 Làm lại")],
        ],
        resize_keyboard=True
    )
    await update.message.reply_text("👇 Dùng nút bên dưới để thao tác nhanh:", reply_markup=persistent_kb)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /reset - xóa toàn bộ dữ liệu phiên làm việc hiện tại"""
    keys_to_clear = [
        'selected_template', 'ddpl_info', 'tv2_info',
        'selected_ma_nganh', 'nganh_results', 'waiting_nganh_choice',
        'vneid_target', '_build_current_data'
    ]
    for k in keys_to_clear:
        context.user_data.pop(k, None)

    await update.message.reply_text(
        "🔄 Đã xóa toàn bộ dữ liệu!\n\n"
        "Bây giờ anh có thể bắt đầu lại từ đầu.\n"
        "Gõ /start để chọn lại loại hồ sơ."
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý ảnh VNeID - trích xuất và tự động điền vào bảng thông tin"""
    await update.message.reply_text("📸 Đang phân tích ảnh VNeID, vui lòng đợi...")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(file.file_path)
            image_bytes = resp.content

        info = await extract_vneid_info(image_bytes)
        # ── Wizard VNeID hook ──
        if get_wizard(context):
            handled = await handle_wizard_vneid(update, context, info)
            if handled:
                return

        person_type = context.user_data.get("vneid_target", "DDPL")

        ho_ten            = info.get("ho_ten", "")
        ngay_sinh         = info.get("ngay_sinh", "")
        so_cccd           = info.get("so_cccd", "")
        dia_chi           = info.get("dia_chi", "")
        gioi_tinh         = info.get("gioi_tinh", "")
        dia_chi_so_nha    = info.get("dia_chi_so_nha", "")
        dia_chi_xa_phuong = info.get("dia_chi_xa_phuong", "")
        dia_chi_quan_huyen= info.get("dia_chi_quan_huyen", "")
        dia_chi_tinh_thanh= info.get("dia_chi_tinh_thanh", "")

        if not ho_ten:
            await update.message.reply_text("❌ Không đọc được thông tin từ ảnh. Vui lòng chụp rõ hơn và thử lại.")
            return

        if person_type == "TV2":
            context.user_data["tv2_info"] = info
            prefix = "TV2"
            label = "Thành viên 2"
        else:
            context.user_data["ddpl_info"] = info
            prefix = "DDPL"
            label = "Người đại diện pháp luật"

        # Bước 1: Hiển thị thông tin trích xuất
        msg_info = (
            f"✅ Đã trích xuất thông tin <b>{label}</b> từ VNeID:\n\n"
            f"👤 Họ tên: <b>{ho_ten}</b>\n"
            f"🎂 Ngày sinh: {ngay_sinh}\n"
            f"🪪 Số CCCD: {so_cccd}\n"
            f"⚥ Giới tính: {gioi_tinh}\n"
            f"🏠 Số nhà/Thôn: {dia_chi_so_nha}\n"
            f"🏘 Xã/Phường: {dia_chi_xa_phuong}\n"
            f"🏙 Quận/Huyện: {dia_chi_quan_huyen or '(không có)'}\n"
            f"📍 Tỉnh/TP: {dia_chi_tinh_thanh}"
        )
        await update.message.reply_text(msg_info, parse_mode='HTML')

        # Bước 2: Tự động điền vào bảng form nếu đã chọn template
        selected_template = context.user_data.get("selected_template")
        if selected_template:
            keys = get_template_keys(selected_template)
            if not keys:
                keys = ["TEN_CONG_TY_VN", "MA_SO_THUE",
                        f"{prefix}_HO_TEN", f"{prefix}_NGAY_SINH", f"{prefix}_SO_CCCD",
                        f"{prefix}_DIA_CHI_SO_NHA", f"{prefix}_DIA_CHI_XA_PHUONG", f"{prefix}_DIA_CHI_TINH_THANH"]

            form_text, empty_keys = build_prefilled_form(selected_template, keys, context)

            note = ""
            if empty_keys:
                show = ', '.join(empty_keys[:4])
                more = f" (+{len(empty_keys)-4} trường nữa)" if len(empty_keys) > 4 else ""
                note = f"\n⚠️ Còn <b>{len(empty_keys)} trường cần bổ sung</b>: <i>{show}{more}</i>"

            filled_msg = (
                f"📋 Bảng thông tin <b>Mẫu {selected_template}</b> — đã điền từ VNeID:{note}\n\n"
                f"CHẠM VÀO ĐOẠN CODE ĐỂ COPY, bổ sung phần còn thiếu rồi gửi lại:\n\n"
                f"<pre>{form_text}</pre>"
            )
            await update.message.reply_text(filled_msg, parse_mode='HTML')
        else:
            await update.message.reply_text(
                f"💡 Thông tin {label} đã lưu!\n"
                "📸 Gửi thêm ảnh VNeID người khác, hoặc\n"
                "👇 Chọn loại hồ sơ để xem bảng thông tin đã điền sẵn."
            )

        context.user_data["vneid_target"] = "TV2" if person_type == "DDPL" else "DDPL"

    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi đọc ảnh: {str(e)}")


async def handle_nganh_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /nganh [mô tả]"""
    args = context.args
    if not args:
        await update.message.reply_text(
            "🔍 Cú pháp: /nganh [mô tả ngành nghề]\n\n"
            "Ví dụ:\n"
            "/nganh bán lẻ hàng tạp hóa\n"
            "/nganh xây dựng nhà ở dân dụng\n"
            "/nganh vận chuyển hàng hóa bằng xe tải"
        )
        return

    mo_ta = " ".join(args)
    await update.message.reply_text(f"🔍 Đang tìm mã ngành cho: <b>{mo_ta}</b>...", parse_mode='HTML')

    try:
        tu_van_text, results = await search_ma_nganh_ai(mo_ta)
        if not results:
            await update.message.reply_text("❌ Không tìm thấy mã ngành phù hợp. Thử mô tả chi tiết hơn nhé.")
            return

        # Gửi lời tư vấn AI trước (nếu có)
        if tu_van_text:
            msg_tuvan = f"💡 <b>TƯ VẤN TỪ AI:</b>\n{tu_van_text}"
            try:
                await update.message.reply_text(msg_tuvan, parse_mode='HTML')
            except Exception:
                # Fallback gửi text thô nếu HTML bị lỗi format
                await update.message.reply_text(f"💡 TƯ VẤN TỪ AI:\n{tu_van_text}")

        msg = f"📋 Top {len(results)} mã ngành chuẩn 2026 phù hợp với <b>{mo_ta}</b>:\n\n"
        for i, r in enumerate(results, 1):
            msg += f"<b>{i}. Mã: {r['ma']}</b>\n"
            msg += f"   📌 {r['ten']}\n\n"
        msg += "💬 Gõ mã ngành bạn muốn chọn (VD: <code>47711</code>) để lưu vào hồ sơ.\nHoặc /nganh [mô tả khác] để tìm lại."

        context.user_data["nganh_results"] = results
        context.user_data["waiting_nganh_choice"] = True
        await update.message.reply_text(msg, parse_mode='HTML')

    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi tra cứu mã ngành: {str(e)}")


async def handle_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý callback xác nhận tạo hồ sơ hoặc sửa lại."""
    import datetime
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "confirm_edit":
        selected_template = context.user_data.get('selected_template', '')
        keys = get_template_keys(selected_template) or ["TEN_CONG_TY_VN", "MA_SO_THUE", "DDPL_HO_TEN"]
        form_text, _ = build_prefilled_form(selected_template, keys, context)
        await query.edit_message_text(
            f"✏️ <b>Nhập lại thông tin</b> — chỉnh sửa rồi gửi lại:\n\n<pre>{form_text}</pre>",
            parse_mode='HTML'
        )
        return

    if data == "confirm_create":
        replacements = context.user_data.get('pending_replacements', {})
        template_dir   = context.user_data.get('pending_template_dir', '')
        selected_template = context.user_data.get('selected_template', 'HoSo')
        dkkd_sel = context.user_data.get('dkkd_selected')

        if not template_dir or not os.path.exists(template_dir):
            await query.edit_message_text("❌ Không tìm thấy thư mục mẫu. Vui lòng /start lại.")
            return

        await query.edit_message_text("⏳ Đang tạo hồ sơ, vui lòng đợi...")

        try:
            temp_dir = tempfile.mkdtemp()
            work_dir = os.path.join(temp_dir, "HoSo")
            shutil.copytree(template_dir, work_dir)

            process_word_files(work_dir, replacements, dkkd_selected=dkkd_sel)

            # #2 — Quét placeholder còn sót
            remaining = scan_remaining_placeholders(work_dir)
            warn_msg = ""
            if remaining:
                warn_lines = ["⚠️ <b>Còn placeholder chưa điền:</b>"]
                for fname, keys in remaining.items():
                    warn_lines.append(f"• <i>{fname}</i>: " + ", ".join(f"[{k}]" for k in keys))
                warn_msg = "\n".join(warn_lines)

            # #5 — Tên ZIP chuẩn: MST_MauHoSo_YYYYMMDD.zip
            mst = replacements.get("MA_SO_THUE", "").strip().replace(" ", "") or "NoMST"
            date_str = datetime.datetime.now().strftime("%Y%m%d")
            safe_template = selected_template.replace(" ", "").replace("/", "-")
            zip_filename = f"{mst}_{safe_template}_{date_str}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(work_dir):
                    for file in files:
                        if not file.startswith("~$"):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, work_dir)
                            zipf.write(file_path, arcname)

            with open(zip_path, 'rb') as f:
                await update.effective_message.reply_document(document=f, filename=zip_filename)

            # Gửi cảnh báo placeholder sót (nếu có)
            if warn_msg:
                await update.effective_message.reply_text(warn_msg, parse_mode='HTML')

            shutil.rmtree(temp_dir)

            # Hỏi lưu profile (#4)
            mst = replacements.get("MA_SO_THUE", "").strip()
            ten = replacements.get("TEN_CONG_TY_VN", "")
            if mst:
                profiles = load_profiles()
                already_saved = mst in profiles
                label = "🔄 Cập nhật profile" if already_saved else "💾 Lưu profile"
                note = " (đã có, bấm để cập nhật)" if already_saved else ""
                kb = InlineKeyboardMarkup([[
                    InlineKeyboardButton(f"{label}: {ten or mst}{note}",
                                         callback_data=f"save_profile_{mst}")
                ]])
                await update.effective_message.reply_text(
                    f"✅ Hồ sơ đã tạo xong!\n💡 Bấm để lưu thông tin công ty để dùng lại lần sau:",
                    reply_markup=kb
                )
            else:
                await update.effective_message.reply_text("✅ Hồ sơ đã tạo xong!")

            # Lưu snapshot dữ liệu cho nút 💾 (phải lưu TRƯỚC khi clear)
            if mst:
                context.user_data['profile_snapshot'] = dict(replacements)

            # Clear session (giữ lại profile_snapshot để dùng khi user bấm nút 💾)
            for key in ['selected_template', 'ddpl_info', 'tv2_info', 'selected_ma_nganh',
                        'selected_ma_nganh_list', 'nganh_results', 'waiting_nganh_choice',
                        'dkkd_selected', 'dkkd_auto_fields', 'dkkd_company_type',
                        'pending_replacements', 'pending_template_dir']:
                context.user_data.pop(key, None)

        except Exception as e:
            await update.effective_message.reply_text(f"❌ Lỗi khi xử lý file: {str(e)}")


async def handle_save_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lưu profile công ty khi người dùng bấm nút 💾."""
    query = update.callback_query
    await query.answer()
    mst = query.data.replace("save_profile_", "")
    # Đọc từ profile_snapshot (lưu trước khi clear session)
    replacements = context.user_data.get("profile_snapshot", {})
    if not replacements:
        # Fallback: thử pending_replacements
        replacements = context.user_data.get("pending_replacements", {})
    if not replacements:
        await query.edit_message_text("⚠️ Phiên làm việc đã hết hạn. Vui lòng tạo hồ sơ lại rồi bấm lưu ngay sau đó.")
        return
    save_company_profile(mst, replacements)
    ten = replacements.get("TEN_CONG_TY_VN", mst)
    # Xóa snapshot sau khi lưu xong
    context.user_data.pop('profile_snapshot', None)
    await query.edit_message_text(
        f"💾 <b>Đã lưu profile:</b>\n"
        f"• MST: <code>{mst}</code>\n"
        f"• Tên: {ten}\n\n"
        f"Lần sau chỉ cần gõ /profiles và chọn công ty — bot sẽ tự điền sẵn!",
        parse_mode='HTML'
    )


async def handle_profiles_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /profiles — xem danh sách công ty đã lưu và chọn để nạp."""
    profiles = load_profiles()
    if not profiles:
        await update.message.reply_text("📂 Chưa có profile công ty nào được lưu.\n\nSau khi tạo hồ sơ, bấm 💾 để lưu thông tin công ty.")
        return

    msg = f"📂 <b>Danh sách {len(profiles)} công ty đã lưu:</b>\n\n"
    keyboard = []
    for mst, profile in profiles.items():
        ten = profile.get("TEN_CONG_TY_VN", "Không rõ")
        saved_at = profile.get("_saved_at", "")
        msg += f"• <code>{mst}</code> — {ten}"
        if saved_at:
            msg += f" <i>({saved_at})</i>"
        msg += "\n"
        short_name = ten[:25] + "..." if len(ten) > 25 else ten
        keyboard.append([
            InlineKeyboardButton(f"📥 {mst} — {short_name}", callback_data=f"load_profile_{mst}"),
            InlineKeyboardButton("🗑️", callback_data=f"del_profile_{mst}")
        ])

    msg += "\nBấm <b>📥 Nạp</b> để điền sẵn vào form tiếp theo, hoặc <b>🗑️</b> để xóa."
    await update.message.reply_text(msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_profile_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý nạp/xóa profile từ /profiles."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("load_profile_"):
        mst = data.replace("load_profile_", "")
        profiles = load_profiles()
        profile = profiles.get(mst, {})
        if not profile:
            await query.answer("❌ Profile không tồn tại!", show_alert=True)
            return
        context.user_data["loaded_profile"] = profile
        ten = profile.get("TEN_CONG_TY_VN", mst)
        ddpl = profile.get("DDPL_HO_TEN", "")
        await query.edit_message_text(
            f"✅ <b>Đã nạp profile:</b>\n"
            f"• MST: <code>{mst}</code>\n"
            f"• Công ty: {ten}\n"
            f"• ĐDPL: {ddpl}\n\n"
            f"Gõ /start để chọn loại hồ sơ — thông tin sẽ được điền sẵn!",
            parse_mode='HTML'
        )

    elif data.startswith("del_profile_"):
        mst = data.replace("del_profile_", "")
        if delete_company_profile(mst):
            await query.answer(f"🗑️ Đã xóa profile {mst}", show_alert=True)
            # Refresh danh sách
            profiles = load_profiles()
            if profiles:
                keyboard = []
                msg = f"📂 <b>Còn lại {len(profiles)} công ty:</b>\n\n"
                for m, p in profiles.items():
                    ten = p.get("TEN_CONG_TY_VN", "Không rõ")
                    msg += f"• <code>{m}</code> — {ten}\n"
                    short = ten[:25] + "..." if len(ten) > 25 else ten
                    keyboard.append([
                        InlineKeyboardButton(f"📥 {m} — {short}", callback_data=f"load_profile_{m}"),
                        InlineKeyboardButton("🗑️", callback_data=f"del_profile_{m}")
                    ])
                await query.edit_message_text(msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await query.edit_message_text("📂 Không còn profile nào được lưu.")
        else:
            await query.answer("❌ Không tìm thấy profile!", show_alert=True)




async def handle_nav_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý navigation: TLM / Thay đổi / chọn thủ tục."""
    query = update.callback_query
    await query.answer()
    data = query.data

    # ── Nhánh TLM: chọn loại hình ──
    if data == "nav_tlm":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏢 Cổ Phần", callback_data="tlm_cp")],
            [InlineKeyboardButton("🏢 TNHH 1 Thành viên", callback_data="tlm_1tv")],
            [InlineKeyboardButton("🏢 TNHH 2 Thành viên", callback_data="tlm_2tv")],
            [InlineKeyboardButton("📍 Địa điểm kinh doanh", callback_data="tlm_dkkd")],
            [InlineKeyboardButton("◀️ Quay lại", callback_data="nav_back_start")],
        ])
        await query.edit_message_text(
            "🏢 <b>THÀNH LẬP MỚI</b>\n\n"
            "Chọn loại hình doanh nghiệp:",
            parse_mode='HTML', reply_markup=kb
        )
        return

    # TLM → chọn xong loại hình → vào form
    if data.startswith("tlm_"):
        loai = data.replace("tlm_", "")
        template_name = TEMPLATE_ROUTE.get((loai, "tlm"))
        if not template_name:
            await query.edit_message_text("❌ Không tìm thấy mẫu tương ứng.")
            return
        context.user_data['selected_template'] = template_name
        context.user_data['nav_company_type'] = loai
        # Tự set CHUC_DANH_KY / CHUC_VU_KY
        type_info = DKKD_COMPANY_TYPES.get(loai)
        if type_info:
            context.user_data["dkkd_auto_fields"] = {
                "CHUC_DANH_KY": type_info["CHUC_DANH_KY"],
                "CHUC_VU_KY": type_info["CHUC_VU_KY"],
            }
        keys = get_template_keys(template_name)
        if not keys:
            keys = ["TEN_CONG_TY_VN", "MA_SO_THUE", "DDPL_HO_TEN", "DDPL_NGAY_SINH",
                    "DDPL_SO_CCCD", "DDPL_DIA_CHI_SO_NHA", "DDPL_DIA_CHI_XA_PHUONG", "DDPL_DIA_CHI_TINH_THANH"]
        form_text, empty_keys = build_prefilled_form(template_name, keys, context)
        note = ""
        if empty_keys:
            show = ", ".join(empty_keys[:4])
            more = f" (+{len(empty_keys)-4} trường nữa)" if len(empty_keys) > 4 else ""
            note = f"\n⚠️ Còn <b>{len(empty_keys)} trường cần bổ sung</b>: <i>{show}{more}</i>"
        msg = (
            f"✅ Mẫu: <b>{template_name}</b>{note}\n\n"
            "CHẠM VÀO ĐOẠN CODE ĐỂ COPY, bổ sung phần còn trống rồi gửi lại:\n\n"
            f"<pre>{form_text}</pre>"
        )
        await query.edit_message_text(msg, parse_mode='HTML')
        return

    # ── Nhánh Thay đổi: hỏi nhập MST ──
    if data == "nav_thaydoi":
        context.user_data['nav_waiting_mst'] = True
        await query.edit_message_text(
            "📝 <b>THAY ĐỔI / THỦ TỤC KHÁC</b>\n\n"
            "Vui lòng nhập <b>Mã số thuế (MST)</b> của công ty:\n\n"
            "<i>Bot sẽ tự tra cứu tên, địa chỉ, loại hình DN</i>",
            parse_mode='HTML'
        )
        return

    # ── User chọn loại hình thủ công (khi auto-detect thất bại) ──
    if data.startswith("nav_type_"):
        loai = data.replace("nav_type_", "")
        context.user_data['nav_company_type'] = loai
        type_info = DKKD_COMPANY_TYPES.get(loai)
        if type_info:
            context.user_data["dkkd_auto_fields"] = {
                "CHUC_DANH_KY": type_info["CHUC_DANH_KY"],
                "CHUC_VU_KY": type_info["CHUC_VU_KY"],
            }
            context.user_data["dkkd_company_type"] = type_info["label"]
        # Hiện menu thủ tục
        await show_procedure_menu(query, context, loai)
        return

    # ── User chọn thủ tục cụ thể ──
    if data.startswith("proc_"):
        proc_code = data.replace("proc_", "")
        loai = context.user_data.get('nav_company_type', '2tv')
        template_name = TEMPLATE_ROUTE.get((loai, proc_code))
        if not template_name:
            await query.edit_message_text(
                f"❌ Thủ tục này chưa có mẫu cho loại hình {loai.upper()}.\n"
                "Vui lòng /start để chọn lại."
            )
            return
        context.user_data['selected_template'] = template_name

        # Special: Chuyển nhượng 2TV → vào wizard
        if proc_code == "chuyen_nhuong" and loai == "2tv":
            await handle_wizard_start(update, context)
            return

        # Special: ĐKKD → vào luồng chọn A1-A7
        if proc_code == "thay_doi_dkkd":
            context.user_data['dkkd_selected'] = set()
            msg = (
                f"✅ Loại hình: <b>{DKKD_COMPANY_TYPES.get(loai, {}).get('label', loai)}</b>\n\n"
                "📋 <b>Chọn nội dung thay đổi</b> cần có trong hồ sơ:\n"
                "(Bấm để chọn/bỏ chọn, sau đó bấm Xác nhận)"
            )
            await query.edit_message_text(msg, parse_mode='HTML', reply_markup=build_dkkd_keyboard(set()))
            return

        # Các thủ tục khác → hiện form
        keys = get_template_keys(template_name)
        if not keys:
            keys = ["TEN_CONG_TY_VN", "MA_SO_THUE", "DDPL_HO_TEN", "DDPL_NGAY_SINH",
                    "DDPL_SO_CCCD", "DDPL_DIA_CHI_SO_NHA", "DDPL_DIA_CHI_XA_PHUONG", "DDPL_DIA_CHI_TINH_THANH"]
        form_text, empty_keys = build_prefilled_form(template_name, keys, context)
        note = ""
        if empty_keys:
            show = ", ".join(empty_keys[:4])
            more = f" (+{len(empty_keys)-4} trường nữa)" if len(empty_keys) > 4 else ""
            note = f"\n⚠️ Còn <b>{len(empty_keys)} trường cần bổ sung</b>: <i>{show}{more}</i>"
        msg = (
            f"✅ Mẫu: <b>{template_name}</b>{note}\n\n"
            "CHẠM VÀO ĐOẠN CODE ĐỂ COPY, bổ sung phần còn trống rồi gửi lại:\n\n"
            f"<pre>{form_text}</pre>"
        )
        await query.edit_message_text(msg, parse_mode='HTML')
        return

    # ── Quay lại màn hình start ──
    if data == "nav_back_start":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏢 Thành lập mới", callback_data="nav_tlm")],
            [InlineKeyboardButton("📝 Thay đổi / Thủ tục khác", callback_data="nav_thaydoi")],
        ])
        await query.edit_message_text(
            "📋 Chọn nhóm thủ tục:",
            parse_mode='HTML', reply_markup=kb
        )
        return


async def show_procedure_menu(query, context, loai):
    """Hiện menu thủ tục phù hợp với loại hình DN."""
    type_label = DKKD_COMPANY_TYPES.get(loai, {}).get("label", loai)
    keyboard = []
    for proc_code, proc_label in PROCEDURES_THAY_DOI:
        # Chỉ hiện thủ tục có mẫu tương ứng
        if (loai, proc_code) in TEMPLATE_ROUTE:
            keyboard.append([InlineKeyboardButton(proc_label, callback_data=f"proc_{proc_code}")])
    keyboard.append([InlineKeyboardButton("◀️ Quay lại", callback_data="nav_back_start")])

    mst = context.user_data.get('nav_mst', '')
    ten = context.user_data.get('nav_company_name', '')
    header = f"🏢 <b>{ten}</b>\nMST: <code>{mst}</code>\n" if ten else ""
    msg = (
        f"{header}"
        f"Loại hình: <b>{type_label}</b>\n\n"
        "📋 <b>Chọn thủ tục:</b>"
    )
    await query.edit_message_text(msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_dkkd_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý callback khi người dùng chọn/bỏ chọn mục ĐKKD."""


    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("dkkd_type_"):
        type_code = data.replace("dkkd_type_", "")
        type_info = DKKD_COMPANY_TYPES.get(type_code)
        if type_info:
            context.user_data["dkkd_auto_fields"] = {
                "CHUC_DANH_KY": type_info["CHUC_DANH_KY"],
                "CHUC_VU_KY": type_info["CHUC_VU_KY"],
            }
            context.user_data["dkkd_company_type"] = type_info["label"]
            context.user_data["dkkd_selected"] = set()
            msg = (
                f"✅ Loại hình: <b>{type_info['label']}</b>\n\n"
                "📋 <b>Chọn nội dung thay đổi</b> cần có trong hồ sơ:\n"
                "(Bấm để chọn/bỏ chọn, sau đó bấm Xác nhận)"
            )
            await query.edit_message_text(msg, parse_mode='HTML', reply_markup=build_dkkd_keyboard(set()))

    elif data.startswith("dkkd_A"):
        code = data.replace("dkkd_", "")
        selected = context.user_data.get("dkkd_selected", set())
        if code in selected:
            selected.discard(code)
        else:
            selected.add(code)
        context.user_data["dkkd_selected"] = selected
        await query.edit_message_reply_markup(reply_markup=build_dkkd_keyboard(selected))

    elif data == "dkkd_confirm":
        selected = context.user_data.get("dkkd_selected", set())
        if not selected:
            await query.answer("❌ Vui lòng chọn ít nhất 1 mục!", show_alert=True)
            return

        template_name = context.user_data.get("selected_template", "Thay đổi nội dung ĐKKD")
        keys = get_template_keys(template_name)
        if not keys:
            keys = ["TEN_CONG_TY_VN", "MA_SO_THUE", "DDPL_HO_TEN", "CHUC_DANH_KY", "CHUC_VU_KY"]
        form_text, empty_keys = build_prefilled_form(template_name, keys, context)

        selected_names = ", ".join([DKKD_SECTIONS[c] for c in sorted(selected)])
        note = ""
        if empty_keys:
            show = ", ".join(empty_keys[:4])
            more = f" (+{len(empty_keys)-4} trường nữa)" if len(empty_keys) > 4 else ""
            note = f"\n⚠️ Còn <b>{len(empty_keys)} trường cần bổ sung</b>: <i>{show}{more}</i>"

        msg = (
            f"✅ Mẫu: <b>{template_name}</b>\n"
            f"📌 Mục đã chọn: <i>{selected_names}</i>{note}\n\n"
            "CHẠM VÀO ĐOẠN CODE ĐỂ COPY, bổ sung phần còn trống rồi gửi lại:\n\n"
            f"<pre>{form_text}</pre>"
        )
        await query.edit_message_text(msg, parse_mode='HTML')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    templates = get_templates()

    # ── Wizard đang chạy? Chuyển xử lý sang wizard ──
    if get_wizard(context):
        handled = await handle_wizard_message(update, context)
        if handled:
            return

    # ── Nhận MST cho luồng "Thay đổi" ──
    if context.user_data.get("nav_waiting_mst"):
        mst = text.strip().replace(" ", "")
        if mst.isdigit() and len(mst) == 10:
            context.user_data['nav_waiting_mst'] = False
            context.user_data['nav_mst'] = mst

            mst_msg = await update.message.reply_text(f"⏳ Đang tra cứu MST {mst}...")
            mst_success = False
            company_name = ""
            loai = None
            for attempt in range(3):
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0",
                        "Accept": "application/json"
                    }
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        response = await client.get(f"https://api.vietqr.io/v2/business/{mst}", headers=headers)
                        if response.status_code == 200:
                            res_data = response.json()
                            if res_data.get("code") == "00":
                                mst_success = True
                                company_info = res_data.get("data", {})
                                company_name = company_info.get("name", "")
                                c_address = company_info.get("address", "")

                                # Lưu thông tin tra cứu
                                context.user_data['nav_company_name'] = company_name
                                if company_name:
                                    loai = detect_company_type(company_name)

                                # Nạp profile nếu có
                                profiles = load_profiles()
                                if mst in profiles:
                                    context.user_data['loaded_profile'] = profiles[mst]

                                # Auto-fill replacements cơ bản
                                context.user_data.setdefault('_nav_replacements', {})
                                context.user_data['_nav_replacements']['MA_SO_THUE'] = mst
                                if company_name:
                                    context.user_data['_nav_replacements']['TEN_CONG_TY_VN'] = company_name
                                if c_address:
                                    parts = [p.strip() for p in c_address.split(",")]
                                    if len(parts) >= 1:
                                        context.user_data['_nav_replacements']['DIA_CHI_TINH_THANH'] = parts[-1]
                                    if len(parts) >= 2:
                                        context.user_data['_nav_replacements']['DIA_CHI_QUAN_HUYEN'] = parts[-2]
                                    if len(parts) >= 3:
                                        context.user_data['_nav_replacements']['DIA_CHI_XA_PHUONG'] = parts[-3]
                                    if len(parts) >= 4:
                                        context.user_data['_nav_replacements']['DIA_CHI_SO_NHA'] = ", ".join(parts[:-3])
                            break
                        elif response.status_code == 429:
                            await asyncio.sleep(2)
                        else:
                            break
                except Exception:
                    await asyncio.sleep(2)

            if mst_success and loai:
                # Auto-detect thành công → hiện menu thủ tục
                context.user_data['nav_company_type'] = loai
                type_info = DKKD_COMPANY_TYPES.get(loai)
                if type_info:
                    context.user_data["dkkd_auto_fields"] = {
                        "CHUC_DANH_KY": type_info["CHUC_DANH_KY"],
                        "CHUC_VU_KY": type_info["CHUC_VU_KY"],
                    }
                    context.user_data["dkkd_company_type"] = type_info["label"]
                await mst_msg.edit_text(f"✅ {company_name}")

                # Tạo fake query object để dùng show_procedure_menu
                type_label = DKKD_COMPANY_TYPES.get(loai, {}).get("label", loai)
                keyboard = []
                for proc_code, proc_label in PROCEDURES_THAY_DOI:
                    if (loai, proc_code) in TEMPLATE_ROUTE:
                        keyboard.append([InlineKeyboardButton(proc_label, callback_data=f"proc_{proc_code}")])
                keyboard.append([InlineKeyboardButton("◀️ Quay lại", callback_data="nav_back_start")])

                msg = (
                    f"🏢 <b>{company_name}</b>\n"
                    f"MST: <code>{mst}</code>\n"
                    f"Loại hình: <b>{type_label}</b>\n\n"
                    "📋 <b>Chọn thủ tục:</b>"
                )
                await update.message.reply_text(msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            elif mst_success:
                # Tìm được công ty nhưng không nhận diện loại hình → hỏi thủ công
                await mst_msg.edit_text(f"✅ {company_name}")
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏢 TNHH 1 TV", callback_data="nav_type_1tv")],
                    [InlineKeyboardButton("🏢 TNHH 2 TV", callback_data="nav_type_2tv")],
                    [InlineKeyboardButton("🏢 Cổ Phần", callback_data="nav_type_cp")],
                ])
                await update.message.reply_text(
                    f"⚠️ Không tự nhận diện được loại hình của <b>{company_name}</b>.\n"
                    "Vui lòng chọn thủ công:",
                    parse_mode='HTML', reply_markup=kb
                )
            else:
                await mst_msg.edit_text(f"⚠️ Không tìm thấy thông tin MST {mst}")
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏢 TNHH 1 TV", callback_data="nav_type_1tv")],
                    [InlineKeyboardButton("🏢 TNHH 2 TV", callback_data="nav_type_2tv")],
                    [InlineKeyboardButton("🏢 Cổ Phần", callback_data="nav_type_cp")],
                ])
                await update.message.reply_text(
                    "Vui lòng chọn loại hình công ty:",
                    parse_mode='HTML', reply_markup=kb
                )
            return
        else:
            await update.message.reply_text(
                "⚠️ MST phải là 10 chữ số. Vui lòng nhập lại:"
            )
            return

    # ── Xử lý nút bấm cố định ──
    if text == "🏠 Menu chính":
        # Gọi lại start
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏢 Thành lập mới", callback_data="nav_tlm")],
            [InlineKeyboardButton("📝 Thay đổi / Thủ tục khác", callback_data="nav_thaydoi")],
        ])
        await update.message.reply_text(
            "📋 Chọn nhóm thủ tục:",
            parse_mode='HTML', reply_markup=keyboard
        )
        return

    if text == "📂 Profiles":
        await handle_profiles_command(update, context)
        return

    if text == "🔍 Tra mã ngành":
        await update.message.reply_text(
            "🔍 Gõ: /nganh [mô tả hoạt động]\n\n"
            "Ví dụ: /nganh bán quần áo online"
        )
        return

    if text == "🔄 Làm lại":
        keys_to_clear = [
            'selected_template', 'ddpl_info', 'tv2_info',
            'selected_ma_nganh', 'selected_ma_nganh_list', 'nganh_results', 'waiting_nganh_choice',
            'vneid_target', '_build_current_data', 'dkkd_selected',
            'nav_waiting_mst', 'nav_mst', 'nav_company_name', 'nav_company_type',
            'loaded_profile', 'profile_snapshot', 'pending_replacements', 'pending_template_dir',
            'dkkd_auto_fields', 'dkkd_company_type', '_nav_replacements'
        ]
        for k in keys_to_clear:
            context.user_data.pop(k, None)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏢 Thành lập mới", callback_data="nav_tlm")],
            [InlineKeyboardButton("📝 Thay đổi / Thủ tục khác", callback_data="nav_thaydoi")],
        ])
        await update.message.reply_text(
            "🔄 Đã xóa toàn bộ dữ liệu!\n\n📋 Chọn nhóm thủ tục:",
            parse_mode='HTML', reply_markup=keyboard
        )
        return

    # Người dùng bấm nút "Làm lại từ đầu" (legacy)
    if text == "🔄 Làm lại từ đầu":
        keys_to_clear = [
            'selected_template', 'ddpl_info', 'tv2_info',
            'selected_ma_nganh', 'selected_ma_nganh_list', 'nganh_results', 'waiting_nganh_choice',
            'vneid_target', '_build_current_data', 'dkkd_selected'
        ]
        for k in keys_to_clear:
            context.user_data.pop(k, None)
        await update.message.reply_text(
            "🔄 Đã xóa toàn bộ dữ liệu!\n\n"
            "Bây giờ anh có thể bắt đầu lại từ đầu.\n"
            "Gõ /start để chọn lại loại hồ sơ."
        )
        return

    # Đang chọn mã ngành
    if context.user_data.get("waiting_nganh_choice"):
        text_stripped = text.strip()
        all_nganh = load_ma_nganh()
        found = next((n for n in all_nganh if n["ma"] == text_stripped), None)
        if found:
            selected_list = context.user_data.setdefault("selected_ma_nganh_list", [])
            if not any(x["ma"] == found["ma"] for x in selected_list):
                selected_list.append(found)
            
            msg = f"✅ Đã thêm mã ngành: <b>{found['ma']} - {found['ten']}</b>\n\n"
            msg += f"📦 <b>Danh sách đã chọn ({len(selected_list)} mã):</b>\n"
            for x in selected_list:
                msg += f"• {x['ma']}: {x['ten']}\n"
            msg += "\n<i>(Bạn có thể gõ thêm mã khác để chọn nhiều, hoặc gõ /start để tạo hồ sơ)</i>"
            
            await update.message.reply_text(msg, parse_mode='HTML')
            return

    # Người dùng chọn template
    if text in templates:
        context.user_data['selected_template'] = text

        # Special case: ĐKKD - hiện menu chọn mục A1-A7
        if text == "Thay đổi nội dung ĐKKD":
            context.user_data['dkkd_selected'] = set()
            keyboard = [
                [InlineKeyboardButton("🏢 Công ty TNHH 1 TV", callback_data="dkkd_type_1tv")],
                [InlineKeyboardButton("🏢 Công ty TNHH 2 TV", callback_data="dkkd_type_2tv")],
                [InlineKeyboardButton("🏢 Công ty Cổ Phần", callback_data="dkkd_type_cp")],
            ]
            msg = "🏢 <b>Chọn loại hình công ty:</b>"
            await update.message.reply_text(msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            return

        keys = get_template_keys(text)
        if not keys:
            keys = ["TEN_CONG_TY_VN", "MA_SO_THUE", "DDPL_HO_TEN", "DDPL_NGAY_SINH",
                    "DDPL_SO_CCCD", "DDPL_DIA_CHI_SO_NHA", "DDPL_DIA_CHI_XA_PHUONG", "DDPL_DIA_CHI_TINH_THANH"]

        # Điền sẵn từ VNeID đã lưu
        form_text, empty_keys = build_prefilled_form(text, keys, context)

        # Ghi chú VNeID
        ddpl_info = context.user_data.get("ddpl_info", {})
        tv2_info  = context.user_data.get("tv2_info", {})
        vneid_note = ""
        if ddpl_info:
            vneid_note += f" | 📸 ĐDPL: {ddpl_info.get('ho_ten','')} ✓"
        if tv2_info:
            vneid_note += f" | 📸 TV2: {tv2_info.get('ho_ten','')} ✓"

        # Ghi chú trường còn trống
        note = ""
        if empty_keys:
            show = ', '.join(empty_keys[:4])
            more = f" (+{len(empty_keys)-4} trường nữa)" if len(empty_keys) > 4 else ""
            note = f"\n⚠️ Còn <b>{len(empty_keys)} trường cần bổ sung</b>: <i>{show}{more}</i>"

        msg = (
            f"✅ Mẫu: <b>{text}</b>{vneid_note}{note}\n\n"
            "CHẠM VÀO ĐOẠN CODE ĐỂ COPY, bổ sung phần còn trống rồi gửi lại:\n\n"
            f"<pre>{form_text}</pre>"
        )
        await update.message.reply_text(msg, parse_mode='HTML')
        return

    # Người dùng gửi bảng thông tin đã điền
    if ":" in text:
        selected_template = context.user_data.get('selected_template')

        lines = text.strip().split('\n')
        replacements = {}
        for line in lines:
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if key.lower() == "mẫu":
                selected_template = val.strip()
            elif val:
                replacements[key] = val

        # Merge VNeID
        ddpl_info = context.user_data.get("ddpl_info", {})
        if ddpl_info:
            ddpl_map = [
                ("DDPL_HO_TEN",          "ho_ten"),
                ("DDPL_NGAY_SINH",        "ngay_sinh"),
                ("DDPL_SO_CCCD",          "so_cccd"),
                ("DDPL_GIOI_TINH",        "gioi_tinh"),
                ("DDPL_DIA_CHI_SO_NHA",   "dia_chi_so_nha"),
                ("DDPL_DIA_CHI_XA_PHUONG","dia_chi_xa_phuong"),
                ("DDPL_DIA_CHI_QUAN_HUYEN","dia_chi_quan_huyen"),
                ("DDPL_DIA_CHI_TINH_THANH","dia_chi_tinh_thanh"),
                ("DDPL_DIA_CHI_DAY_DU",   "dia_chi"),
            ]
            for k, src in ddpl_map:
                if not replacements.get(k) and ddpl_info.get(src):
                    replacements[k] = ddpl_info[src]

        tv2_info = context.user_data.get("tv2_info", {})
        if tv2_info:
            tv2_map = [
                ("TV2_HO_TEN",           "ho_ten"),
                ("TV2_NGAY_SINH",         "ngay_sinh"),
                ("TV2_SO_CCCD",           "so_cccd"),
                ("TV2_DIA_CHI_SO_NHA",    "dia_chi_so_nha"),
                ("TV2_DIA_CHI_XA_PHUONG", "dia_chi_xa_phuong"),
                ("TV2_DIA_CHI_QUAN_HUYEN","dia_chi_quan_huyen"),
                ("TV2_DIA_CHI_TINH_THANH","dia_chi_tinh_thanh"),
                ("TV2_DIA_CHI_DAY_DU",    "dia_chi"),
            ]
            for k, src in tv2_map:
                if not replacements.get(k) and tv2_info.get(src):
                    replacements[k] = tv2_info[src]

        # Merge mã ngành
        if context.user_data.get("selected_ma_nganh_list"):
            replacements["MA_NGANH_NGHE_LIST"] = context.user_data["selected_ma_nganh_list"]
        elif context.user_data.get("selected_ma_nganh") and not replacements.get("MA_NGANH_NGHE"):
            replacements["MA_NGANH_NGHE"] = context.user_data["selected_ma_nganh"]

        # Tra cứu MST
        if "MA_SO_THUE" in replacements and replacements["MA_SO_THUE"]:
            mst = replacements["MA_SO_THUE"].strip().replace(" ", "")
            mst_msg = await update.message.reply_text(f"⏳ Đang tra cứu Mã số thuế {mst}...")
            mst_success = False
            for attempt in range(3):
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                        "Accept": "application/json"
                    }
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        response = await client.get(f"https://api.vietqr.io/v2/business/{mst}", headers=headers)
                        if response.status_code == 200:
                            res_data = response.json()
                            if res_data.get("code") == "00":
                                mst_success = True
                                company_info = res_data.get("data", {})
                                c_name = company_info.get("name")
                                c_address = company_info.get("address")
                                if c_name and not replacements.get("TEN_CONG_TY_VN"):
                                    replacements["TEN_CONG_TY_VN"] = c_name
                                if c_address:
                                    parts = [p.strip() for p in c_address.split(",")]
                                    if not replacements.get("DIA_CHI_TINH_THANH"):
                                        replacements["DIA_CHI_TINH_THANH"] = parts[-1] if len(parts) >= 1 else ""
                                    if not replacements.get("DIA_CHI_QUAN_HUYEN"):
                                        replacements["DIA_CHI_QUAN_HUYEN"] = parts[-2] if len(parts) >= 2 else ""
                                    if not replacements.get("DIA_CHI_XA_PHUONG"):
                                        replacements["DIA_CHI_XA_PHUONG"] = parts[-3] if len(parts) >= 3 else ""
                                    if not replacements.get("DIA_CHI_SO_NHA"):
                                        replacements["DIA_CHI_SO_NHA"] = ", ".join(parts[:-3]) if len(parts) >= 4 else ""
                                await mst_msg.edit_text(f"✅ Tra cứu MST thành công: {c_name}")
                            break
                        elif response.status_code == 429:
                            await asyncio.sleep(2)
                        else:
                            break
                except Exception as e:
                    print(f"MST lookup error: {e}", flush=True)
                    await asyncio.sleep(2)
            
            if not mst_success:
                await mst_msg.edit_text(f"⚠️ Không thể tự động lấy thông tin từ MST {mst}. Vui lòng tự điền nếu thiếu.")

        if not selected_template:
            await update.message.reply_text("❌ Bạn chưa chọn loại mẫu nào. Vui lòng gõ /start để chọn lại.")
            return

        template_dir = os.path.join(BASE_DIR, f"Mẫu {selected_template}")
        if not os.path.exists(template_dir):
            if selected_template.startswith("Mẫu "):
                template_dir = os.path.join(BASE_DIR, selected_template)
            if not os.path.exists(template_dir):
                await update.message.reply_text(f"❌ Không tìm thấy thư mục mẫu '{selected_template}'.")
                return

        # Lưu replacements để dùng lại khi confirm
        context.user_data['pending_replacements'] = replacements
        context.user_data['pending_template_dir'] = template_dir

        # Hiện màn hình xác nhận (#3)
        mst_val = replacements.get('MA_SO_THUE', '')
        ten_val = replacements.get('TEN_CONG_TY_VN', '')
        ddpl_val = replacements.get('DDPL_HO_TEN', '')
        dkkd_type = context.user_data.get('dkkd_company_type', '')
        dkkd_sel = context.user_data.get('dkkd_selected')
        dkkd_names = ''
        if dkkd_sel:
            dkkd_names = ', '.join([DKKD_SECTIONS.get(c, c) for c in sorted(dkkd_sel)])

        confirm_lines = [f"📋 <b>Xác nhận thông tin hồ sơ</b>\n"]
        confirm_lines.append(f"📁 Loại hồ sơ: <b>{selected_template}</b>")
        if mst_val:  confirm_lines.append(f"🔢 MST: <code>{mst_val}</code>")
        if ten_val:  confirm_lines.append(f"🏢 Công ty: <b>{ten_val}</b>")
        if ddpl_val: confirm_lines.append(f"👤 ĐDPL: {ddpl_val}")
        if dkkd_type: confirm_lines.append(f"🏢 Loại hình: {dkkd_type}")
        if dkkd_names: confirm_lines.append(f"📌 Mục thay đổi: <i>{dkkd_names}</i>")

        # Đếm trường đã điền
        filled = sum(1 for v in replacements.values() if v)
        total_fields = len(replacements)
        confirm_lines.append(f"\n✏️ Đã điền: <b>{filled}/{total_fields}</b> trường")
        confirm_lines.append("\nBấm <b>✅ Tạo hồ sơ</b> để tiếp tục hoặc <b>✏️ Sửa lại</b> để nhập lại.")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Tạo hồ sơ", callback_data="confirm_create"),
             InlineKeyboardButton("✏️ Sửa lại", callback_data="confirm_edit")]
        ])
        await update.message.reply_text('\n'.join(confirm_lines), parse_mode='HTML', reply_markup=keyboard)
        return

    await update.message.reply_text(
        "❓ Tôi không hiểu cú pháp này.\n\n"
        "• /start - Chọn loại hồ sơ\n"
        "• /nganh [mô tả] - Tra mã ngành nghề\n"
        "• /profiles - Xem & nạp profile công ty đã lưu\n"
        "• 📸 Gửi ảnh VNeID để trích xuất thông tin tự động"
    )


def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CommandHandler("nganh", handle_nganh_command))
    application.add_handler(CommandHandler("profiles", handle_profiles_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(handle_wizard_callback_wrapper, pattern="^wiz_"))
    application.add_handler(CallbackQueryHandler(handle_nav_callback,         pattern="^(nav_|tlm_|proc_)"))
    application.add_handler(CallbackQueryHandler(handle_confirm_callback,      pattern="^confirm_"))
    application.add_handler(CallbackQueryHandler(handle_save_profile_callback,  pattern="^save_profile_"))
    application.add_handler(CallbackQueryHandler(handle_profile_action_callback, pattern="^(load|del)_profile_"))
    application.add_handler(CallbackQueryHandler(handle_dkkd_callback,          pattern="^dkkd_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running - VNeID auto-fill + Local Mã ngành search...", flush=True)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
