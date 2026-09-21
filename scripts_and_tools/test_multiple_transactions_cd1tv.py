import sys
sys.path.append(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")

import zipfile
import io
import docx
from services.render_service import render_documents

test_payload = {
    "template_name": "Chuyển đổi loại hình 1TV sang 2 TV",
    "data": {
        "TEN_CONG_TY_VN_CU": "CÔNG TY TNHH MỘT THÀNH VIÊN ĐẦU TƯ AN KHANG",
        "MA_SO_THUE": "0106842704",
        "DIA_CHI_CTY_CU": "Số 88 Phố Huế, Phường Hàng Bài, Thành phố Hà Nội",
        "VON_CU": "2000000000",
        "TEN_CONG_TY_VN": "CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ AN KHANG",
        "TEN_CONG_TY_EN": "AN KHANG TRADING SERVICE COMPANY LIMITED",
        "TEN_CONG_TY_VIET_TAT": "AN KHANG TRADING",
        "SDT_CONG_TY": "0988123456",
        "EMAIL_CONG_TY": "info@ankhang.com.vn",
    },
    "special_payload": {
        "cd1tv2tv_data": {
            "oldCompany": {
                "mst": "0106842704",
                "name": "CÔNG TY TNHH MỘT THÀNH VIÊN ĐẦU TƯ AN KHANG",
                "address": "Số 88 Phố Huế, Phường Hàng Bài, Thành phố Hà Nội",
                "von": "2000000000"
            },
            "newCompany": {
                "nameVn": "CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ AN KHANG",
                "nameEn": "AN KHANG TRADING SERVICE COMPANY LIMITED",
                "nameShort": "AN KHANG TRADING",
                "phone": "0988123456",
                "email": "info@ankhang.com.vn"
            },
            "csh": {
                "HO_TEN": "NGUYỄN VĂN THÀNH",
                "CCCD": "001080001234",
                "NGAY_SINH": "10/02/1980",
                "GIOI_TINH": "Nam",
                "DIA_CHI": "Số 12 Tràng Thi, Phường Hàng Trống, Quận Hoàn Kiếm, Thành phố Hà Nội"
            },
            "members": [
                {
                    "id": 1,
                    "ho_ten": "NGUYỄN VĂN THÀNH",
                    "cccd": "001080001234",
                    "ngay_sinh": "10/02/1980",
                    "gioi_tinh": "Nam",
                    "dia_chi": "Số 12 Tràng Thi, Phường Hàng Trống, Thành phố Hà Nội",
                    "von": "500000000",
                    "ty_le": "25",
                    "nhan_cn": ""
                },
                {
                    "id": 2,
                    "ho_ten": "TRẦN THỊ HƯƠNG",
                    "cccd": "001090005678",
                    "ngay_sinh": "15/05/1990",
                    "gioi_tinh": "Nữ",
                    "dia_chi": "Số 45 Cầu Giấy, Phường Dịch Vọng, Thành phố Hà Nội",
                    "von": "1000000000",
                    "ty_le": "50",
                    "nhan_cn": "1000000000"
                },
                {
                    "id": 3,
                    "ho_ten": "LÊ VĂN LONG",
                    "cccd": "001085009999",
                    "ngay_sinh": "20/11/1985",
                    "gioi_tinh": "Nam",
                    "dia_chi": "Số 99 Kim Mã, Phường Kim Mã, Thành phố Hà Nội",
                    "von": "500000000",
                    "ty_le": "25",
                    "nhan_cn": "500000000"
                }
            ],
            "chuyen_nhuong": [
                {
                    "ben_a": {
                        "ho_ten": "NGUYỄN VĂN THÀNH",
                        "so_cccd": "001080001234",
                        "ngay_sinh": "10/02/1980",
                        "gioi_tinh": "Nam",
                        "dia_chi_day_du": "Số 12 Tràng Thi, Phường Hàng Trống, Quận Hoàn Kiếm, Thành phố Hà Nội"
                    },
                    "ben_b": {
                        "ho_ten": "TRẦN THỊ HƯƠNG",
                        "so_cccd": "001090005678",
                        "ngay_sinh": "15/05/1990",
                        "gioi_tinh": "Nữ",
                        "dia_chi_day_du": "Số 45 Cầu Giấy, Phường Dịch Vọng, Thành phố Hà Nội"
                    },
                    "von_cn_so": "1000000000",
                    "gia_tri_cn_so": "1000000000",
                    "ty_le_cn": "50"
                },
                {
                    "ben_a": {
                        "ho_ten": "NGUYỄN VĂN THÀNH",
                        "so_cccd": "001080001234",
                        "ngay_sinh": "10/02/1980",
                        "gioi_tinh": "Nam",
                        "dia_chi_day_du": "Số 12 Tràng Thi, Phường Hàng Trống, Quận Hoàn Kiếm, Thành phố Hà Nội"
                    },
                    "ben_b": {
                        "ho_ten": "LÊ VĂN LONG",
                        "so_cccd": "001085009999",
                        "ngay_sinh": "20/11/1985",
                        "gioi_tinh": "Nam",
                        "dia_chi_day_du": "Số 99 Kim Mã, Phường Kim Mã, Thành phố Hà Nội"
                    },
                    "von_cn_so": "500000000",
                    "gia_tri_cn_so": "500000000",
                    "ty_le_cn": "25"
                }
            ]
        }
    },
    "ma_nganh": [
        {"ma": "6201", "ten": "Lập trình máy vi tính", "is_main": True}
    ]
}

zip_bytes = render_documents(
    template_name="Chuyển đổi loại hình 1TV sang 2 TV",
    raw_data=test_payload["data"],
    ma_nganh_list=test_payload["ma_nganh"],
    special_payload=test_payload["special_payload"]
)

with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
    names = zf.namelist()
    print(f"Total files in ZIP: {len(names)}\n")
    for name in sorted(names):
        print(f"- {name}")
        doc = docx.Document(io.BytesIO(zf.read(name)))
        full_text = " ".join([p.text for p in doc.paragraphs] + [c.text for t in doc.tables for r in t.rows for c in r.cells])
        has_unrendered = "{{" in full_text
        if has_unrendered:
            print("  WARNING: Has unrendered tags!")
