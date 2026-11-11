"""Đọc CCCD không cần API ngoài. Toàn bộ dữ liệu trong test là giả."""
import io

import pytest
import zxingcpp
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from config import TESSDATA_DIR
from main import app
from services.cccd_parser import cccd_conflicts, combine_ocr, parse_ocr_text, parse_qr, split_address
from services.ocr_service import tsv_to_text

QR_TEXT = "001190012345|012345678|Nguyễn Thị Hường|05111990|Nữ|Số 12 ngõ 34, Phường Nghĩa Đô, Thành phố Hà Nội|01012022"
client = TestClient(app)


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def qr_image(text: str) -> Image.Image:
    barcode = zxingcpp.create_barcode(text, zxingcpp.BarcodeFormat.QRCode)
    img = Image.fromarray(barcode.to_image(scale=6)).convert("RGB")
    canvas = Image.new("RGB", (img.width + 80, img.height + 80), "white")
    canvas.paste(img, (40, 40))
    return canvas


def test_parse_qr_fields():
    d = parse_qr(QR_TEXT)
    assert d["ho_ten"] == "NGUYỄN THỊ HƯỜNG"
    assert (d["ngay_sinh"], d["gioi_tinh"], d["so_cccd"]) == ("05/11/1990", "Nữ", "001190012345")
    assert d["dia_chi_so_nha"] == "Số 12 ngõ 34"
    assert d["dia_chi_xa_phuong"] == "Phường Nghĩa Đô"
    assert d["dia_chi_tinh_thanh"] == "Thành Phố Hà Nội"
    assert (d["nguon"], d["can_kiem_tra"]) == ("qr", [])


@pytest.mark.parametrize("text", ["https://example.com", "123|a|b|c|d|e", "001190012345||Tên|99999999|Nữ|Hà Nội"])
def test_parse_qr_rejects_other_codes(text):
    assert parse_qr(text) is None


def test_cccd_cross_check():
    assert cccd_conflicts("001190012345", "05/11/1990", "Nữ") == []
    assert "ngay_sinh" in cccd_conflicts("001190012345", "05/11/1991", "Nữ")
    assert "gioi_tinh" in cccd_conflicts("001190012345", "05/11/1990", "Nam")
    assert cccd_conflicts("001205012345", "01/01/2005", "Nam") == []  # chữ số 4 = 2: nam, sinh thế kỷ 21
    assert cccd_conflicts("001305012345", "01/01/2005", "Nam") == ["so_cccd", "gioi_tinh"]


def test_split_address_with_district():
    parts, review = split_address("Thôn A, Xã Yên Thường, Huyện Gia Lâm, Hà Nội")
    assert parts == {
        "dia_chi_so_nha": "Thôn A", "dia_chi_xa_phuong": "Xã Yên Thường",
        "dia_chi_quan_huyen": "Huyện Gia Lâm", "dia_chi_tinh_thanh": "Thành Phố Hà Nội",
    }
    assert review == []


def test_split_address_without_markers_is_flagged():
    parts, review = split_address("Tổ 3, Nghĩa Đô, Cầu Giấy, Hà Nội")
    assert (parts["dia_chi_so_nha"], parts["dia_chi_xa_phuong"], parts["dia_chi_quan_huyen"]) == ("Tổ 3", "Nghĩa Đô", "Cầu Giấy")
    assert "dia_chi_xa_phuong" in review


def test_split_address_flags_province_outside_catalog():
    parts, review = split_address("Xã A, Tỉnh Không Có Thật")
    assert parts["dia_chi_tinh_thanh"] == "Tỉnh Không Có Thật"
    assert "dia_chi_tinh_thanh" in review


def test_parse_ocr_vneid_layout():
    d = parse_ocr_text(
        "Họ và tên\nNGUYỄN THỊ HƯỜNG\nNgày sinh\n05/11/1990\nGiới tính\nNữ\nSố định danh cá nhân\n001190012345\n"
        "Nơi thường trú\nSố 12 ngõ 34, Phường Nghĩa Đô,\nThành phố Hà Nội\nQuê quán\nXã Yên Thường, Hà Nội\n"
    )
    assert d["ho_ten"] == "NGUYỄN THỊ HƯỜNG"
    assert d["dia_chi"] == "Số 12 ngõ 34, Phường Nghĩa Đô, Thành phố Hà Nội"
    assert "so_cccd" not in d["can_kiem_tra"] and "ho_ten" in d["can_kiem_tra"]


def test_parse_ocr_card_layout_nationality_is_not_gender():
    d = parse_ocr_text(
        "Số / No.: 001190012345\nHọ và tên / Full name:\nNGUYỄN THỊ HƯỜNG\nNgày sinh / Date of birth: 05/11/1990\n"
        "Giới tính / Sex: Nữ  Quốc tịch / Nationality: Việt Nam\nQuê quán / Place of origin: Gia Lâm, Hà Nội\n"
        "Nơi thường trú / Place of residence: Tổ 1, Phường Nghĩa Đô, Hà Nội\nCó giá trị đến: 05/11/2030\n"
    )
    assert (d["so_cccd"], d["ngay_sinh"], d["gioi_tinh"]) == ("001190012345", "05/11/1990", "Nữ")
    assert d["dia_chi"] == "Tổ 1, Phường Nghĩa Đô, Hà Nội"


def test_parse_ocr_stops_at_temporary_residence_and_fixes_uppercase_words():
    d = parse_ocr_text(
        "Họ và tên\nTRÂN THỊ MAI\tHI\nSố định danh cá nhân\n001182012345\nNgày sinh\n02/03/1982\n"
        "Nơi thường trú\nTÔ DÂN PHÔ SÔ 2 NGỌC HÀ, Phường Tây Hồ, Thành phố Hà Nội Nơi tạm trú\nKhông có\n"
    )
    assert d["ho_ten"] == "TRẦN THỊ MAI"
    assert d["dia_chi_so_nha"] == "TỔ DÂN PHỐ SỐ 2 NGỌC HÀ"
    assert d["dia_chi_tinh_thanh"] == "Thành Phố Hà Nội"


def test_noise_is_not_a_name_and_votes_pick_majority():
    assert parse_ocr_text("Họ và tên\nẦM G\nNgày sinh\n")["ho_ten"] == ""
    read = lambda name: parse_ocr_text(f"Họ và tên\n{name}\nSố định danh cá nhân\n001182012345\n")
    assert combine_ocr([read("LÊ THỊ HOA"), read("LÊ THI HOA"), read("LÊ THỊ HOA")])["ho_ten"] == "LÊ THỊ HOA"


def test_name_ignores_background_noise_after_it():
    d = parse_ocr_text("Họ, chữ đệm và tên / Full name:\t$ _ . SSỆ\nPHẠM VĂN HÙNG. “...7\nNgày, tháng, năm sinh / Date of birth:\n")
    assert d["ho_ten"] == "PHẠM VĂN HÙNG"
    assert parse_ocr_text("Họ, chữ đệm và tên / Full name:\n$\nG\nPHAM VĂN HÙNG\n")["ho_ten"] == "PHẠM VĂN HÙNG"


def test_tsv_drops_trailing_noise_and_marks_gaps():
    head = "5\t1\t1\t1\t1\t{}\t{}\t10\t{}\t30\t{}\t{}"
    tsv = "\n".join(head.format(i, x, w, c, t) for i, (x, w, c, t) in enumerate(
        [(10, 80, 95, "TRẦN"), (100, 60, 92, "MAI"), (170, 20, 30, "HI"), (500, 40, 90, "AB")], 1))
    assert tsv_to_text(tsv) == "TRẦN MAI HI\tAB"
    assert tsv_to_text("\n".join(tsv.splitlines()[:3])) == "TRẦN MAI"


def test_parse_ocr_missing_gender_uses_cccd_digit():
    d = parse_ocr_text("Họ và tên: TRẦN VĂN AN\nSố định danh cá nhân: 001090012345\n")
    assert d["gioi_tinh"] == "Nam"
    assert "ngay_sinh" in d["can_kiem_tra"]


def test_api_reads_qr():
    res = client.post("/api/ocr/vneid", files={"image": ("a.png", png_bytes(qr_image(QR_TEXT)), "image/png")}).json()
    assert res["success"] and res["data"]["nguon"] == "qr"
    assert res["data"]["so_cccd"] == "001190012345"


def test_api_rejects_non_image():
    res = client.post("/api/ocr/vneid", files={"image": ("a.png", b"not an image", "image/png")}).json()
    assert res == {"success": False, "message": "Tệp tải lên không phải ảnh hợp lệ"}


@pytest.mark.skipif(not (TESSDATA_DIR / "vie.traineddata").exists(), reason="Chưa chạy python -m tools.setup_ocr")
def test_api_ocr_screenshot_without_qr():
    pytest.importorskip("tesserocr")
    candidates = ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    path = next((p for p in candidates if __import__("os").path.exists(p)), None)
    if not path:
        pytest.skip("Không có phông chữ tiếng Việt")
    font = ImageFont.truetype(path, 34)
    img = Image.new("RGB", (950, 760), "white")
    draw = ImageDraw.Draw(img)
    rows = ["Họ và tên", "NGUYỄN THỊ HƯỜNG", "Ngày sinh", "05/11/1990", "Giới tính", "Nữ",
            "Số định danh cá nhân", "001190012345", "Nơi thường trú", "Số 12 ngõ 34, Phường Nghĩa Đô, Hà Nội"]
    for i, row in enumerate(rows):
        draw.text((40, 30 + i * 70), row, fill="black", font=font)

    res = client.post("/api/ocr/vneid", files={"image": ("a.png", png_bytes(img), "image/png")}).json()
    assert res["success"], res
    data = res["data"]
    assert data["nguon"] == "ocr"
    assert (data["so_cccd"], data["ngay_sinh"], data["gioi_tinh"]) == ("001190012345", "05/11/1990", "Nữ")
    assert data["dia_chi_xa_phuong"] == "Phường Nghĩa Đô"


def test_api_hides_internal_errors(monkeypatch):
    """Lỗi hệ thống không lộ chi tiết kỹ thuật (đường dẫn, tên thư viện...) ra trình duyệt."""
    from routes import ocr

    async def boom(*_a, **_k):
        raise RuntimeError("C:/secret/path/tesseract.dll failed")

    monkeypatch.setattr(ocr, "extract_vneid", boom)
    res = client.post("/api/ocr/vneid", files={"image": ("a.png", png_bytes(qr_image(QR_TEXT)), "image/png")}).json()
    assert res["success"] is False and "secret" not in res["message"] and "lỗi hệ thống" in res["message"]


def test_api_requires_upload():
    assert client.post("/api/ocr/vneid", data={"target": "ddpl"}).status_code == 400


# ---------- Máy chủ thiếu thành phần: báo rõ thiếu gì, không báo "lỗi hệ thống" chung chung ----------

def _text_image_bytes():
    img = Image.new("RGB", (600, 200), "white")
    ImageDraw.Draw(img).text((20, 80), "khong co ma QR", fill="black")
    return png_bytes(img)


def test_missing_tessdata_message_names_the_fix(monkeypatch, tmp_path):
    pytest.importorskip("tesserocr")
    from services import ocr_service

    monkeypatch.setattr(ocr_service, "TESSDATA_DIR", tmp_path)
    res = client.post("/api/ocr/vneid", files={"image": ("a.png", _text_image_bytes(), "image/png")}).json()
    assert res["success"] is False
    assert "chưa cài dữ liệu đọc chữ" in res["message"] and "python -m tools.setup_ocr" in res["message"]
    assert client.get("/api/ocr/status").json()["ocr_ready"] is False


def test_missing_tesserocr_message_names_the_fix(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "tesserocr":
            raise ImportError("DLL load failed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    res = client.post("/api/ocr/vneid", files={"image": ("a.png", _text_image_bytes(), "image/png")}).json()
    assert res["success"] is False and "tesserocr" in res["message"] and "pip install" in res["message"]
    assert "DLL" not in res["message"]  # chi tiết kỹ thuật chỉ ghi log
    st = client.get("/api/ocr/status").json()
    assert st["tesserocr"] is False and st["qr_ready"] is True and "tessdata_dir" not in st


def test_qr_still_works_without_tesserocr(monkeypatch):
    import builtins

    real_import = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", lambda name, *a, **k: (_ for _ in ()).throw(ImportError(name))
                        if name == "tesserocr" else real_import(name, *a, **k))
    res = client.post("/api/ocr/vneid", files={"image": ("a.png", png_bytes(qr_image(QR_TEXT)), "image/png")}).json()
    assert res["success"] and res["data"]["nguon"] == "qr"


def test_missing_qr_library_falls_back_to_text(monkeypatch):
    from services import ocr_service

    monkeypatch.setattr(ocr_service, "zxingcpp", None)
    monkeypatch.setattr(ocr_service, "_read_ocr", lambda img: {"nguon": "ocr", "ho_ten": "A"})
    res = client.post("/api/ocr/vneid", files={"image": ("a.png", png_bytes(qr_image(QR_TEXT)), "image/png")}).json()
    assert res["success"] and res["data"]["nguon"] == "ocr"


def test_setup_ocr_check_command(capsys):
    from tools import setup_ocr
    from services import ocr_service

    code = setup_ocr.check()
    out = capsys.readouterr().out
    assert "Đọc thử ảnh có mã QR" in out and "KẾT LUẬN" in out
    assert code == (0 if ocr_service.status()["ocr_ready"] else 1)
