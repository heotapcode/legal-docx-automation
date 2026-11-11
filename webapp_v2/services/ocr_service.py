"""Đọc CCCD/VNeID ngay trên máy: ưu tiên mã QR, không có QR thì OCR bằng Tesseract.

Ảnh không được gửi ra ngoài. Dữ liệu tiếng Việt cho Tesseract cài bằng: python -m tools.setup_ocr
"""
import asyncio
import io
from typing import Dict, Optional

try:
    import zxingcpp
except ImportError:
    zxingcpp = None

try:
    from PIL import Image, ImageChops, ImageOps, ImageStat, UnidentifiedImageError
except ImportError:
    Image = None

from config import TESSDATA_DIR
try:
    from services.cccd_parser import combine_ocr, ocr_score, parse_ocr_text, parse_qr
except ImportError:
    combine_ocr = ocr_score = parse_ocr_text = parse_qr = None

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_SIDE = 3500
MIN_OCR_WIDTH = 2800  # phóng lớn giúp Tesseract giữ dấu tiếng Việt ở chữ in hoa
MAX_OCR_SCALE = 4.0
NOISE_CONF = 60
GAP_RATIO = 2.5
DARK_MEAN = 110
FULL_SCORE = 4
MIN_SCORE = 2


INSTALL_HINT = "Trên máy chủ, trong thư mục webapp_v2, chạy: pip install -r requirements.txt"
DATA_HINT = "Trên máy chủ, trong thư mục webapp_v2, chạy: python -m tools.setup_ocr"


class OcrSetupError(ValueError):
    """Máy chủ thiếu thành phần để đọc CCCD. Thông báo viết cho người dùng, nói rõ thiếu gì và cách cài."""


def status() -> Dict[str, object]:
    """Tình trạng các thành phần đọc CCCD (dùng cho /api/ocr/status và python -m tools.setup_ocr --check)."""
    try:
        import tesserocr  # noqa: F401
        tesser, tesser_error = True, ""
    except Exception as e:  # ImportError, hoặc thiếu thư viện hệ thống trên Windows
        tesser, tesser_error = False, f"{type(e).__name__}: {e}"
    data = (TESSDATA_DIR / "vie.traineddata").exists()
    return {
        "pillow": Image is not None,
        "parser": parse_qr is not None,
        "qr": zxingcpp is not None,
        "tesserocr": tesser,
        "tesserocr_error": tesser_error,
        "tessdata": data,
        "tessdata_dir": str(TESSDATA_DIR),
        "qr_ready": Image is not None and parse_qr is not None and zxingcpp is not None,
        "ocr_ready": Image is not None and parse_qr is not None and tesser and data,
    }


def _load_image(image_bytes: bytes) -> "Image.Image":
    if Image is None or parse_qr is None:
        raise OcrSetupError(f"Máy chủ chưa cài thư viện xử lý ảnh (Pillow). {INSTALL_HINT}")
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError("Ảnh quá lớn (tối đa 15 MB)")
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as e:
        raise ValueError("Tệp tải lên không phải ảnh hợp lệ") from e
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    return img


def _scaled(img: "Image.Image", factor: float) -> "Image.Image":
    return img.resize((int(img.width * factor), int(img.height * factor)), Image.LANCZOS)


def _read_qr(img: "Image.Image") -> Optional[Dict]:
    if zxingcpp is None:  # thiếu thư viện đọc QR: vẫn thử đọc chữ
        return None
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


def _prepare_for_ocr(img: "Image.Image") -> "Image.Image":
    # Lấy kênh sáng nhất của mỗi điểm: hoa văn nền nhạt màu của VNeID gần như biến mất, chữ tối vẫn giữ nguyên
    r, g, b = img.split()
    gray = ImageOps.autocontrast(ImageChops.lighter(ImageChops.lighter(r, g), b))
    if ImageStat.Stat(gray).mean[0] < DARK_MEAN:  # ảnh màn hình chế độ tối
        gray = ImageOps.invert(gray)
    if gray.width < MIN_OCR_WIDTH:
        gray = _scaled(gray, min(MAX_OCR_SCALE, MIN_OCR_WIDTH / gray.width))
    return gray


def _read_ocr(img: "Image.Image") -> Dict:
    no_qr = "Không đọc được mã QR trong ảnh" if zxingcpp is not None else \
        "Máy chủ chưa cài thư viện đọc mã QR (zxing-cpp)"
    try:
        import tesserocr
    except Exception as e:
        raise OcrSetupError(f"{no_qr}, và máy chủ chưa cài được thư viện đọc chữ (tesserocr). {INSTALL_HINT} "
                            f"Trong lúc chờ: chụp rõ mã QR trên thẻ hoặc nhập tay.") from e
    if not (TESSDATA_DIR / "vie.traineddata").exists():
        raise OcrSetupError(f"{no_qr}, và máy chủ chưa cài dữ liệu đọc chữ tiếng Việt. {DATA_HINT} "
                            f"Trong lúc chờ: chụp rõ mã QR trên thẻ hoặc nhập tay.")

    gray = _prepare_for_ocr(img)

    with tesserocr.PyTessBaseAPI(path=str(TESSDATA_DIR), lang="vie") as api:
        def read(candidate: "Image.Image", psm: int) -> Dict:
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
