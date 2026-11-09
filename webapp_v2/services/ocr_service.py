"""Đọc CCCD/VNeID ngay trên máy: ưu tiên mã QR, không có QR thì OCR bằng Tesseract.

Ảnh không được gửi ra ngoài. Dữ liệu tiếng Việt cho Tesseract cài bằng: python -m tools.setup_ocr
"""
import asyncio
import io
from typing import Dict, Optional

import zxingcpp
from PIL import Image, ImageChops, ImageOps, ImageStat, UnidentifiedImageError

from config import TESSDATA_DIR
from services.cccd_parser import combine_ocr, ocr_score, parse_ocr_text, parse_qr

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_SIDE = 3500
MIN_OCR_WIDTH = 2800  # phóng lớn giúp Tesseract giữ dấu tiếng Việt ở chữ in hoa
MAX_OCR_SCALE = 4.0
NOISE_CONF = 60
GAP_RATIO = 2.5
DARK_MEAN = 110
FULL_SCORE = 4
MIN_SCORE = 2


def _load_image(image_bytes: bytes) -> Image.Image:
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError("Ảnh quá lớn (tối đa 15 MB)")
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as e:
        raise ValueError("Tệp tải lên không phải ảnh hợp lệ") from e
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    return img


def _scaled(img: Image.Image, factor: float) -> Image.Image:
    return img.resize((int(img.width * factor), int(img.height * factor)), Image.LANCZOS)


def _read_qr(img: Image.Image) -> Optional[Dict]:
    gray = ImageOps.autocontrast(img.convert("L"))
    for candidate in (img, gray, _scaled(gray, 2), _scaled(gray, 0.5)):
        for barcode in zxingcpp.read_barcodes(candidate, formats=zxingcpp.BarcodeFormat.QRCode):
            parsed = parse_qr(barcode.text)
            if parsed:
                return parsed
    return None


def tsv_to_text(tsv: str) -> str:
    """Dựng lại văn bản từ TSV của Tesseract: khoảng trống lớn thành tab, bỏ chữ ngắn cuối dòng độ tin cậy thấp."""
    rows: Dict[tuple, list] = {}
    for row in tsv.splitlines():
        f = row.split("\t")
        if len(f) == 12 and f[0] == "5" and f[11].strip():
            rows.setdefault((f[2], f[3], f[4]), []).append(
                (int(f[6]), int(f[6]) + int(f[8]), int(f[9]), float(f[10]), f[11].strip())
            )

    lines = []
    for words in rows.values():
        last = words[-1]
        if len(words) > 1 and len(last[4]) <= 2 and last[4].isalpha() and last[3] < NOISE_CONF:
            words = words[:-1]
        height = max(w[2] for w in words)
        text = words[0][4]
        for prev, word in zip(words, words[1:]):
            text += ("\t" if word[0] - prev[1] > GAP_RATIO * height else " ") + word[4]
        lines.append(text)
    return "\n".join(lines)


def _prepare_for_ocr(img: Image.Image) -> Image.Image:
    # Lấy kênh sáng nhất của mỗi điểm: hoa văn nền nhạt màu của VNeID gần như biến mất, chữ tối vẫn giữ nguyên
    r, g, b = img.split()
    gray = ImageOps.autocontrast(ImageChops.lighter(ImageChops.lighter(r, g), b))
    if ImageStat.Stat(gray).mean[0] < DARK_MEAN:  # ảnh màn hình chế độ tối
        gray = ImageOps.invert(gray)
    if gray.width < MIN_OCR_WIDTH:
        gray = _scaled(gray, min(MAX_OCR_SCALE, MIN_OCR_WIDTH / gray.width))
    return gray


def _read_ocr(img: Image.Image) -> Dict:
    import tesserocr

    if not (TESSDATA_DIR / "vie.traineddata").exists():
        raise ValueError("Không đọc được mã QR và chưa cài dữ liệu OCR tiếng Việt. Chạy: python -m tools.setup_ocr")

    gray = _prepare_for_ocr(img)

    with tesserocr.PyTessBaseAPI(path=str(TESSDATA_DIR), lang="vie") as api:
        def read(candidate: Image.Image, psm: int) -> Dict:
            api.SetPageSegMode(psm)
            api.SetImage(candidate)
            return parse_ocr_text(tsv_to_text(api.GetTSVText(0)))

        best = combine_ocr([read(gray, psm) for psm in (6, 4, 11)])
        if ocr_score(best) < FULL_SCORE:  # ảnh có thể bị xoay
            for angle in (90, 270, 180):
                rotated = combine_ocr([read(gray.rotate(angle, expand=True), psm) for psm in (6, 11)])
                if ocr_score(rotated) > ocr_score(best):
                    best = rotated
                if ocr_score(best) == FULL_SCORE:
                    break

    if ocr_score(best) < MIN_SCORE:
        raise ValueError("Không nhận diện được thông tin trong ảnh. Vui lòng chụp lại rõ nét, đủ khung hình.")
    return best


def _extract(image_bytes: bytes) -> Dict:
    img = _load_image(image_bytes)
    return _read_qr(img) or _read_ocr(img)


async def extract_vneid(image_bytes: bytes, target: str = "ddpl") -> Dict:
    return await asyncio.to_thread(_extract, image_bytes)
