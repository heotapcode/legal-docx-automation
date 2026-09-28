import sys, zipfile, io, docx
from pathlib import Path

base = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word")
sys.path.insert(0, str(base / "webapp_v2"))
from services.render_service import render_documents

payload = {
    "ten_cong_ty_vn": "CÔNG TY TNHH MỘT THÀNH VIÊN DỊCH VỤ AN BÌNH",
    "ma_so_thue": "0109887766",
    "dia_chi_so_nha": "Số 88 Phố Bà Triệu",
    "dia_chi_xa_phuong": "Phường Hàng Bài",
    "dia_chi_tinh_thanh": "Thành phố Hà Nội",
    "von_dieu_le_so": "2000000000",
    "ddpl": {
        "ho_ten": "NGUYỄN VĂN AN",
        "so_cccd": "001088009988",
        "ngay_sinh": "10/10/1988",
        "gioi_tinh": "Nam",
        "dia_chi_day_du": "Số 88 Phố Bà Triệu, Phường Hàng Bài, Hà Nội"
    }
}

zip_bytes = render_documents("Giải thể công ty TNHH 1 TV", payload)
z = zipfile.ZipFile(io.BytesIO(zip_bytes))
print("ZIP file names:", z.namelist())

assert "03. Báo cáo thanh lý tài sản.docx" in z.namelist()
doc_bytes = z.read("03. Báo cáo thanh lý tài sản.docx")
doc = docx.Document(io.BytesIO(doc_bytes))

found_p15 = False
found_p16 = False
for i, p in enumerate(doc.paragraphs):
    if "Sau khi trừ đi chi phí giải thể công ty, tiền mặt còn lại là:" in p.text:
        print(f"Output P{i}: {p.text}")
        assert "2,000,000,000 đồng (Hai tỷ đồng)" in p.text
        found_p15 = True
    if "Chủ sở hữu đã được hoàn trả số tiền là:" in p.text:
        print(f"Output P{i}: {p.text}")
        assert "2,000,000,000 đồng (Hai tỷ đồng)" in p.text
        found_p16 = True

assert found_p15 and found_p16, "Failed to find both paragraphs in output document!"
print("TEST SUCCESS: 03. Báo cáo thanh lý tài sản rendered perfectly with full format!")
