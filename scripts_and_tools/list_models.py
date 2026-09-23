import httpx
import sys

sys.path.insert(0, r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")
from config import GEMINI_API_KEY

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
r = httpx.get(url, timeout=10.0)
print("Status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    for m in data.get("models", []):
        name = m.get("name", "")
        methods = m.get("supportedGenerationMethods", [])
        if "generateContent" in methods:
            print(f"{name} -> {m.get('displayName', '')}")
else:
    print(r.text)
