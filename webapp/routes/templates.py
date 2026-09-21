import os
import json
from fastapi import APIRouter
from config import TEMPLATES_DIR, FOLDER_KEYS_JSON

router = APIRouter(prefix="/api/templates", tags=["Templates"])

FIELD_LABELS = {
    'TEN_CONG_TY_VN': 'Tên công ty (tiếng Việt)',
    'TEN_CONG_TY_EN': 'Tên công ty (tiếng Anh)',
    'TEN_CONG_TY_VIET_TAT': 'Tên viết tắt',
    'MA_SO_THUE': 'Mã số thuế',
    'DIA_CHI_SO_NHA': 'Số nhà, đường',
    'DIA_CHI_XA_PHUONG': 'Xã/Phường',
    'DIA_CHI_QUAN_HUYEN': 'Quận/Huyện',
    'DIA_CHI_TINH_THANH': 'Tỉnh/Thành phố',
    'SDT_CONG_TY': 'Số điện thoại',
    'EMAIL_CONG_TY': 'Email',
    'VON_DIEU_LE_SO': 'Vốn điều lệ (số)',
    'VON_DIEU_LE_CHU': 'Vốn điều lệ (chữ)',
    'DDPL_HO_TEN': 'Họ tên ĐDPL',
    'DDPL_NGAY_SINH': 'Ngày sinh ĐDPL',
    'DDPL_SO_CCCD': 'Số CCCD ĐDPL',
    'DDPL_GIOI_TINH': 'Giới tính ĐDPL',
    'DDPL_DIA_CHI_SO_NHA': 'Địa chỉ ĐDPL (số nhà)',
    'DDPL_DIA_CHI_XA_PHUONG': 'Địa chỉ ĐDPL (xã/phường)',
    'DDPL_DIA_CHI_QUAN_HUYEN': 'Địa chỉ ĐDPL (quận/huyện)',
    'DDPL_DIA_CHI_TINH_THANH': 'Địa chỉ ĐDPL (tỉnh/thành)',
    'DDPL_DIA_CHI_DAY_DU': 'Địa chỉ ĐDPL (đầy đủ)',
    'DDPL_CU_GIOI_TINH': 'Giới tính ĐDPL Cũ',
    'DDPL_CU_HO_TEN': 'Họ tên ĐDPL Cũ',
    'DDPL_CU_NGAY_SINH': 'Ngày sinh ĐDPL Cũ',
    'DDPL_CU_SO_CCCD': 'Số CCCD ĐDPL Cũ',
    'DDPL_CU_DIA_CHI_DAY_DU': 'Địa chỉ ĐDPL Cũ',
    'TV1_HO_TEN': 'Họ tên Thành viên 1',
    'TV1_NGAY_SINH': 'Ngày sinh TV1',
    'TV1_SO_CCCD': 'Số CCCD TV1',
    'TV1_DIA_CHI_DAY_DU': 'Địa chỉ TV1',
    'TV1_VON_SO': 'Vốn góp TV1 (số)',
    'TV1_TY_LE': 'Tỷ lệ vốn TV1 (%)',
    'TV2_HO_TEN': 'Họ tên Thành viên 2',
    'TV2_NGAY_SINH': 'Ngày sinh TV2',
    'TV2_SO_CCCD': 'Số CCCD TV2',
    'TV2_GIOI_TINH': 'Giới tính TV2',
    'TV2_DIA_CHI_SO_NHA': 'Địa chỉ TV2 (số nhà)',
    'TV2_DIA_CHI_XA_PHUONG': 'Địa chỉ TV2 (xã/phường)',
    'TV2_DIA_CHI_TINH_THANH': 'Địa chỉ TV2 (tỉnh/thành)',
    'TV2_DIA_CHI_DAY_DU': 'Địa chỉ TV2',
    'TV2_VON_SO': 'Vốn góp TV2 (số)',
    'TV2_VON_CU_SO': 'Vốn cũ TV2 (số)',
    'TV2_VON_CU_CHU': 'Vốn cũ TV2 (chữ)',
    'TV2_VON_MOI_SO': 'Vốn mới TV2 (số)',
    'TV2_VON_MOI_CHU': 'Vốn mới TV2 (chữ)',
    'TV2_TY_LE': 'Tỷ lệ vốn TV2 (%)',
    'CSHHL_GIOI_TINH': 'Giới tính CSHHL',
    'NGUOI_DUOC_UY_QUYEN_GIOI_TINH': 'Giới tính người được ủy quyền',
    'CHUC_DANH_KY': 'Chức danh người ký',
    'CHUC_VU_KY': 'Chức vụ người ký'
}

@router.get("")
def get_templates():
    templates = []
    if os.path.exists(TEMPLATES_DIR):
        for f in os.listdir(TEMPLATES_DIR):
            if os.path.isdir(os.path.join(TEMPLATES_DIR, f)) and f.startswith("Mẫu "):
                name = f.replace("Mẫu ", "")
                templates.append({"name": name, "display_name": name, "file_count": len(os.listdir(os.path.join(TEMPLATES_DIR, f))), "category": "Thành lập mới" if "Thành lập mới" in name else "Thay đổi"})
    return {"templates": templates}

@router.get("/{template_name}/fields")
def get_template_fields(template_name: str):
    fields = []
    if os.path.exists(FOLDER_KEYS_JSON):
        with open(FOLDER_KEYS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            keys = data.get(template_name, [])
            for key in keys:
                label = FIELD_LABELS.get(key, key)
                
                if key.startswith("DDPL_CU"):
                    group = "Đại diện pháp luật CŨ"
                elif key.startswith("DDPL") or key.startswith("NGUOI_DUOC_UY_QUYEN"):
                    group = "Đại diện pháp luật MỚI"
                elif key.startswith("TV1"):
                    group = "Thành viên 1"
                elif key.startswith("TV2"):
                    group = "Thành viên 2"
                elif key.startswith("CHUC_DANH") or key.startswith("CHUC_VU"):
                    group = "Người ký (Tự động điền)"
                else:
                    group = "Thông tin Công ty"
                    
                fields.append({"key": key, "label": label, "group": group, "type": "text", "required": True})
    return {"fields": fields}
