import httpx, zipfile, io, docx

url = "http://127.0.0.1:8002/api/documents/generate"
payload = {
    "template_name": "Giải thể công ty TNHH 1 TV",
    "data": {
        "ten_cong_ty_vn": "CÔNG TY ABC & SONS <VIỆT NAM>",
        "ma_so_thue": "0109123456",
        "dia_chi_so_nha": "Số 10 & 12 Phố Tràng Tiền",
        "dia_chi_xa_phuong": "Phường Tràng Tiền",
        "dia_chi_tinh_thanh": "Thành phố Hà Nội",
        "von_dieu_le_so": "1005000",
        "ddpl": {
            "ho_ten": "NGUYỄN VĂN A & B",
            "so_cccd": "001090001234",
            "ngay_sinh": "01/01/1985",
            "gioi_tinh": "Nam",
            "dia_chi_day_du": "Số 10 Phố Tràng Tiền, Hà Nội"
        }
    }
}

resp = httpx.post(url, json=payload, timeout=30.0)
print("HTTP status:", resp.status_code)
assert resp.status_code == 200

z = zipfile.ZipFile(io.BytesIO(resp.content))
print("Files:", z.namelist())

# Check 01. Thông báo giải thể.docx
doc = docx.Document(io.BytesIO(z.read("01. Thông báo giải thể.docx")))
txt = "\n".join(p.text for p in doc.paragraphs)
print("Check '&':", "CÔNG TY ABC & SONS <VIỆT NAM>" in txt)
assert "CÔNG TY ABC & SONS <VIỆT NAM>" in txt, "Company name with & and < > failed!"

# Check Báo cáo thanh lý: check so_thanh_chu for 1005000
bctl = docx.Document(io.BytesIO(z.read("03. Báo cáo thanh lý tài sản.docx")))
bctl_txt = "\n".join(p.text for p in bctl.paragraphs)
print("Check so_thanh_chu:", "Một triệu không trăm lẻ năm nghìn đồng" in bctl_txt)
assert "Một triệu không trăm lẻ năm nghìn đồng" in bctl_txt, "so_thanh_chu failed!"

print("ALL SPECIAL CHARS AND SO_THANH_CHU TESTS PASSED!")
