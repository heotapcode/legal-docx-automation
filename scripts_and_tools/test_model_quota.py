import httpx
import sys
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
            {"text": "Return JSON: {\"status\": \"ok\"}"},
            {"inline_data": {"mime_type": mime_type, "data": image_b64}}
        ]
    }]
}

candidates = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-preview",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash"
]

for m in candidates:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={GEMINI_API_KEY}"
    try:
        r = httpx.post(url, json=payload, timeout=15.0)
        print(f"Model: {m:<30} -> {r.status_code}")
        if r.status_code == 200:
            print("   -> Success text:", r.json()["candidates"][0]["content"]["parts"][0]["text"][:60])
    except Exception as e:
        print(f"Model: {m:<30} -> Error: {e}")
