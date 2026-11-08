"""Tải dữ liệu tiếng Việt cho Tesseract (khoảng 12 MB). Chạy một lần: python -m tools.setup_ocr"""
import hashlib
import sys

import httpx

from config import TESSDATA_DIR

URL = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/vie.traineddata"
SHA256 = "b6b49293d95d0b6dbd8780174627e82c75be957b6f4ed9862155540d6b00bb45"


def main() -> int:
    target = TESSDATA_DIR / "vie.traineddata"
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == SHA256:
        print(f"Đã có dữ liệu OCR: {target}")
        return 0

    resp = httpx.get(URL, follow_redirects=True, timeout=180)
    resp.raise_for_status()
    if hashlib.sha256(resp.content).hexdigest() != SHA256:
        print("Tệp tải về không khớp mã kiểm tra, đã hủy.", file=sys.stderr)
        return 1

    TESSDATA_DIR.mkdir(parents=True, exist_ok=True)
    target.write_bytes(resp.content)
    print(f"Đã cài dữ liệu OCR: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
