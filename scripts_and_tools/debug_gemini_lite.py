import asyncio
import sys
import httpx
import base64

sys.path.insert(0, r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")
from config import GEMINI_API_KEY
from services.ocr_service import detect_image_mime

dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

image_b64 = base64.b64encode(dummy_png).decode("utf-8")
mime_type = detect_image_mime(dummy_png)

payload = {
    "contents": [{
        "parts": [
            {"text": "Extract json"},
            {"inline_data": {"mime_type": mime_type, "data": image_b64}}
        ]
    }]
}

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
r = httpx.post(url, json=payload, timeout=20.0)
print("gemini-2.5-flash-lite with image status:", r.status_code)
print("Response text:", r.text[:300])
