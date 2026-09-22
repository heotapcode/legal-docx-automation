import json
import base64
import re
import httpx
from config import GEMINI_API_KEY

def detect_image_mime(b: bytes) -> str:
    if b.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if b.startswith(b"RIFF") and b[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"

async def extract_vneid(image_bytes: bytes, target: str = "ddpl") -> dict:
    if not GEMINI_API_KEY:
        raise Exception("Chưa cấu hình GEMINI_API_KEY trong file .env")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    mime_type = detect_image_mime(image_bytes)

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
Ví dụ địa chỉ 'Tiên Hội, Xã Đông Anh, Thành Phố Hà Nội' thì:
- dia_chi_so_nha = 'Tiên Hội'
- dia_chi_xa_phuong = 'Xã Đông Anh'
- dia_chi_quan_huyen = ''
- dia_chi_tinh_thanh = 'Thành Phố Hà Nội'
Nếu không tìm thấy thông tin nào, để trống chuỗi "". Chỉ trả về JSON, không thêm bất kỳ văn bản nào khác."""

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": image_b64}}
            ]
        }]
    }

    # Danh sách model OCR: ưu tiên các model flash-lite có quota ổn định
    candidate_models = [
        "gemini-flash-lite-latest",
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
    ]
    last_error = ""

    for model in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                        # Tìm khối JSON hợp lệ trong chuỗi trả về
                        json_match = re.search(r"\{.*\}", content, re.DOTALL)
                        if json_match:
                            content = json_match.group(0)
                        elif content.startswith("```"):
                            content = re.sub(r"^```[a-zA-Z]*\n?", "", content)
                            content = re.sub(r"\n?```$", "", content).strip()
                        return json.loads(content)
                else:
                    last_error = f"{resp.status_code} - {resp.text}"
        except Exception as e:
            last_error = str(e)
            continue

    raise Exception(f"Lỗi gọi Gemini OCR: {last_error}")
