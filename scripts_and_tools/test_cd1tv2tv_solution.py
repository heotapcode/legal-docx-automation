import os
import sys
import copy
import re
import docx
from pathlib import Path

BASE_DIR = Path(r'C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2')
sys.path.insert(0, str(BASE_DIR))

from services.render_service import (
    fmt_money, so_thanh_chu, danh_xung, parse_address_str,
    merge_cd1tv2tv_data, normalize_context
)

mock_csh = {
    'HO_TEN': 'NGUYỄN VĂN A',
    'CCCD': '001090123456',
    'NGAY_SINH': '01/01/1980',
    'GIOI_TINH': 'Nam',
    'DIA_CHI': '123 Đường Cũ, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh'
}

mock_old_comp = {
    'name': 'CÔNG TY TNHH MỘT THÀNH VIÊN ABC',
    'mst': '0312345678',
    'address': '123 Đường Cũ, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh',
    'von': '1.000.000.000'
}

mock_new_comp = {
    'nameVn': 'CÔNG TY TNHH HAI THÀNH VIÊN ABC',
    'nameEn': 'ABC TWO MEMBERS COMPANY LIMITED',
    'nameShort': 'ABC CO., LTD',
    'phone': '0901234567',
    'email': 'contact@abc.vn'
}

print('Imports and mocks initialized OK!')
