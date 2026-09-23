import httpx
import json
import re
import sys

sys.path.insert(0, r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")
from config import GEMINI_API_KEY

prompt = """Đây là ảnh chụp màn hình VNeID (ứng dụng căn cước công dân điện tử của Việt Nam) hoặc ảnh chụp thẻ CCCD.
Hãy trích xuất chính xác các thông tin sau và trả về JSON thuần túy (không có markdown, không có ```json):
{
  "ho_ten": "họ và tên đầy đủ viết hoa",
  "ngay_sinh": "ngày sinh định dạng DD/MM/YYYY",
  "gioi_tinh": "Nam hoặc Nữ",
  "so_cccd": "số căn cước công dân (12 chữ số)",
  "dia_chi": "địa chỉ thường trú đầy đủ (nguyên văn)",
  "dia_chi_so_nha": "phần địa chỉ cụ thể: số nhà, ngõ, thôn, xóm, tổ dân phố (KHÔNG bao gồm xã/phường và tỉnh/thành)",
  "dia_chi_xa_phuong": "tên xã hoặc phường hoặc thị trấn (ví dụ: Xã Đông Anh, Phường Cầu Giấy)",
  "dia_chi_quan_huyen": "tên quận hoặc huyện hoặc thị xã nếu có (ví dụ: Huyện Đông Anh, Quận Cầu Giấy), để trống nếu không có",
  "dia_chi_tinh_thanh": "tên tỉnh hoặc thành phố (ví dụ: Thành Phố Hà Nội, Tỉnh Bắc Ninh)"
}
Ví dụ text trên CCCD:
Số / No.: 001085001234
Họ và tên / Full name: NGUYỄN VĂN AN
Ngày sinh / Date of birth: 15/05/1985
Giới tính / Sex: Nam
Quê quán / Place of origin: Hà Nội
Nơi thường trú / Place of residence: Số 10 ngõ 5 phố Vọng, Phường Đồng Tâm, Quận Hai Bà Trưng, Hà Nội
"""

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
payload = {"contents": [{"parts": [{"text": prompt}]}]}

r = httpx.post(url, json=payload, timeout=20.0)
print("Status:", r.status_code)
if r.status_code == 200:
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    print("Raw text:", repr(text))
    # Test json parsing
    content = text.strip()
    if content.startswith("```"):
        content = re.sub(r"^```[a-zA-Z]*\n?", "", content)
        content = re.sub(r"\n?```$", "", content).strip()
    data = json.loads(content)
    print("Parsed JSON:", json.dumps(data, indent=2, ensure_ascii=False))
