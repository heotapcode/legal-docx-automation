import httpx
import os
import sys

sys.path.insert(0, r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")
from config import GEMINI_API_KEY

models = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
]

payload = {
    "contents": [{"parts": [{"text": "ping"}]}]
}

for m in models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={GEMINI_API_KEY}"
    try:
        r = httpx.post(url, json=payload, timeout=10.0)
        print(f"Model: {m:<25} -> Status: {r.status_code}")
        if r.status_code != 200:
            print(f"   Response: {r.text[:120]}")
    except Exception as e:
        print(f"Model: {m:<25} -> Error: {e}")
