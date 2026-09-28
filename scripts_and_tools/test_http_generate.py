import httpx, zipfile, io, docx

url = "http://127.0.0.1:8002/api/documents/generate"
payload = {
    "template_name": "Giải thể công ty TNHH 1 TV",
    "data": {
        "ten_cong_ty_vn": "CÔNG TY TNHH MỘT THÀNH VIÊN VÍ DỤ",
        "ma_so_thue": "0101234567",
        "dia_chi_so_nha": "Số 1 Cầu Giấy",
        "dia_chi_xa_phuong": "Phường Quan Hoa",
        "dia_chi_tinh_thanh": "Thành phố Hà Nội",
        "von_dieu_le_so": "10000000000",
        "ddpl": {
            "ho_ten": "LÊ THỊ MAI",
            "so_cccd": "001190005678",
            "ngay_sinh": "20/05/1990",
            "gioi_tinh": "Nữ",
            "dia_chi_day_du": "Số 1 Cầu Giấy, Quan Hoa, Hà Nội"
        }
    }
}

resp = httpx.post(url, json=payload, timeout=30.0)
print("Status:", resp.status_code)
assert resp.status_code == 200, f"Error {resp.status_code}: {resp.text}"

z = zipfile.ZipFile(io.BytesIO(resp.content))
print("Files in response zip:", z.namelist())
bctl = docx.Document(io.BytesIO(z.read("03. Báo cáo thanh lý tài sản.docx")))

for p in bctl.paragraphs:
    if "chi phí giải thể công ty" in p.text or "hoàn trả" in p.text:
        print("  ->", p.text)
print("HTTP GENERATE TEST PASSED!")
