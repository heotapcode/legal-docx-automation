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
                    "von": "1000000000",
                    "ty_le": "50",
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
        doc = docx.Document(io.BytesIO(zf.read(name)))
        
        # Check font sizes in paragraphs where values are filled
        filled_runs_sizes = set()
        all_paras = list(doc.paragraphs)
        for t in doc.tables:
            for r in t.rows:
                for c in r.cells:
                    for p in c.paragraphs:
                        all_paras.append(p)
                        
        sample_checks = []
        for p in all_paras:
            txt = p.text
            if any(val in txt for val in ["AN KHANG", "NGUYỄN VĂN THÀNH", "TRẦN THỊ HƯƠNG", "0106842704"]):
                runs_info = []
                for r in p.runs:
                    sz = r._r.xpath('./w:rPr/w:sz/@w:val')
                    sz_pt = int(sz[0]) / 2 if sz else 'Inherit'
                    runs_info.append(f"{r.text[:15]} ({sz_pt}pt)")
                sample_checks.append(f"   P: {' | '.join(runs_info[:4])}")
                
        print(f"* {name}:")
        for s in sample_checks[:3]:
            print(s)
        print()
