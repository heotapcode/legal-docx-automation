"""Cài và kiểm tra phần đọc CCCD/VNeID. Chạy trong thư mục webapp_v2:

    python -m tools.setup_ocr            # tải dữ liệu tiếng Việt cho Tesseract (khoảng 12 MB), chạy một lần
    python -m tools.setup_ocr --check    # kiểm tra từng thành phần và đọc thử một ảnh QR + một ảnh chữ
    python -m tools.setup_ocr --check "đường dẫn/ảnh.jpg"   # đọc thử ảnh của bạn (chỉ in các ô đọc được, không in nội dung)
"""
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


def check(image_path: str = "") -> int:
    """In tình trạng từng thành phần và đọc thử. Trả 0 nếu cả đọc QR và đọc chữ đều chạy."""
    import asyncio
    import io

    from services import ocr_service

    st = ocr_service.status()
    rows = [
        ("Thư viện ảnh (pillow)", st["pillow"], ocr_service.INSTALL_HINT),
        ("Đọc mã QR (zxing-cpp)", st["qr"], ocr_service.INSTALL_HINT),
        ("Đọc chữ (tesserocr)", st["tesserocr"], ocr_service.INSTALL_HINT + (
            f" | Lỗi: {st['tesserocr_error']}" if st["tesserocr_error"] else "")),
        (f"Dữ liệu tiếng Việt ({st['tessdata_dir']})", st["tessdata"], ocr_service.DATA_HINT),
    ]
    for label, ok, hint in rows:
        print(f"[{'OK' if ok else 'THIẾU'}] {label}" + ("" if ok else f"\n        -> {hint}"))

    def try_read(label: str, data: bytes, show_keys: bool = False) -> bool:
        try:
            out = asyncio.run(ocr_service.extract_vneid(data))
            extra = f" (nguồn: {out.get('nguon')}; đọc được: {', '.join(k for k, v in out.items() if v and k not in ('nguon', 'can_kiem_tra'))})" \
                if show_keys else f" (nguồn: {out.get('nguon')})"
            print(f"[OK] {label}{extra}")
            return True
        except Exception as e:
            print(f"[LỖI] {label}: {type(e).__name__}: {e}")
            return False

    ok = True
    if st["qr_ready"]:
        import zxingcpp
        from PIL import Image
        qr = Image.fromarray(zxingcpp.create_barcode(
            "001190012345|012345678|Nguyễn Văn Thử|05111990|Nam|Số 1, Phường Thử, Thành phố Hà Nội|01012022",
            zxingcpp.BarcodeFormat.QRCode).to_image(scale=6)).convert("RGB")
        canvas = Image.new("RGB", (qr.width + 80, qr.height + 80), "white")
        canvas.paste(qr, (40, 40))
        buf = io.BytesIO()
        canvas.save(buf, "PNG")
        ok &= try_read("Đọc thử ảnh có mã QR", buf.getvalue())
    else:
        ok = False
    if not st["ocr_ready"]:
        ok = False
        print("[THIẾU] Đọc chữ chưa sẵn sàng: ảnh không có mã QR (ảnh chụp màn hình VNeID) sẽ không đọc được.")
    if image_path:
        with open(image_path, "rb") as f:
            ok &= try_read(f"Đọc ảnh {image_path}", f.read(), show_keys=True)
    print("KẾT LUẬN:", "phần đọc CCCD sẵn sàng." if ok else "phần đọc CCCD CHƯA đầy đủ, xem các dòng THIẾU/LỖI ở trên.")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--check" in sys.argv:
        args = [a for a in sys.argv[1:] if a != "--check"]
        sys.exit(check(args[0] if args else ""))
    sys.exit(main())
