import json
import base64
import re
import httpx
from config import GEMINI_API_KEY

async def extract_vneid(image_bytes: bytes, target: str = "ddpl") -> dict:
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    prompt = """Đây là ảnh chụp màn hình VNeID (ứng dụng căn cước công dân điện tử của Việt Nam).
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
Ví dụ địa chỉ 'Tiên Hội, Xã Đông Anh, Thành Phố Hà Nội' thì:
- dia_chi_so_nha = 'Tiên Hội'
- dia_chi_xa_phuong = 'Xã Đông Anh'
- dia_chi_quan_huyen = ''
- dia_chi_tinh_thanh = 'Thành Phố Hà Nội'
Nếu không tìm thấy thông tin nào, để trống chuỗi "". Chỉ trả về JSON, không thêm bất kỳ văn bản nào khác."""

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
            raise Exception(f"Gemini API error: {resp.status_code} - {resp.text}")
        data = resp.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise Exception("Không nhận diện được nội dung từ Gemini")

    content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```[a-zA-Z]*\n?", "", content)
        content = re.sub(r"\n?```$", "", content).strip()

    parsed = json.loads(content)
    return parsed
