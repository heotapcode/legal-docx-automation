import asyncio
import sys

sys.path.insert(0, r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")
from services.ocr_service import extract_vneid

# 1x1 transparent PNG
dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

async def main():
    try:
        res = await extract_vneid(dummy_png)
        print("Success:", res)
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
