import sys, zipfile, io, docx
from pathlib import Path

base = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word")
sys.path.insert(0, str(base / "webapp_v2"))
from services.render_service import render_documents

payload = {
    "ten_cong_ty_vn": "CÔNG TY CỔ PHẦN CÔNG NGHỆ ALPHA",
    "ma_so_thue": "0108889999",
    "dia_chi_so_nha": "Số 123 Phố Huế",
    "dia_chi_xa_phuong": "Phường Hàng Bài",
    "dia_chi_tinh_thanh": "Thành phố Hà Nội",
    "ddkd_dia_chi_so_nha": "Số nhà 61C, Ngõ 77 Phố Lua",
    "ddkd_dia_chi_xa_phuong": "Phường Hà Đông",
    "ddkd_dia_chi_tinh_thanh": "TP Hà Nội",
    "ddpl": {
        "ho_ten": "NGUYỄN VĂN THÀNH",
        "so_cccd": "001090001122",
        "ngay_sinh": "12/12/1990",
        "gioi_tinh": "Nam",
        "dia_chi_day_du": "Số 50 Quang Trung, Hà Đông, Hà Nội",
        "dia_chi_so_nha": "Số 50 Quang Trung",
        "dia_chi_xa_phuong": "Phường Quang Trung",
        "dia_chi_tinh_thanh": "Thành phố Hà Nội"
    }
}

zip_bytes = render_documents("Thành lập mới địa điểm kinh doanh", payload)
z = zipfile.ZipFile(io.BytesIO(zip_bytes))
print("ZIP contents:", z.namelist())

# Check 01. Thông Báo lập địa điểm.docx
tb_bytes = z.read("01. Thông Báo lập địa điểm.docx")
tb_doc = docx.Document(io.BytesIO(tb_bytes))

print("\n--- 01. Thông Báo lập địa điểm.docx check ---")
for i in [10, 11, 12, 13]:
    p = tb_doc.paragraphs[i]
    print(f"P{i}: {p.text}")

assert "Số nhà 61C, Ngõ 77 Phố Lua" in tb_doc.paragraphs[11].text, "P11 failed"
assert "Phường Hà Đông" in tb_doc.paragraphs[12].text, "P12 failed"
assert "TP Hà Nội" in tb_doc.paragraphs[13].text, "P13 failed"
assert "Số 123 Phố Huế" not in tb_doc.paragraphs[11].text, "Mother address leaked into location address!"

# Check 02. Giấy ủy quyền.docx
uq_bytes = z.read("02. Giấy ủy quyền.docx")
uq_doc = docx.Document(io.BytesIO(uq_bytes))

print("\n--- 02. Giấy ủy quyền.docx check ---")
for p in uq_doc.paragraphs:
    if "Địa chỉ trụ sở:" in p.text:
        print("Trụ sở:", p.text)
        assert "Số 123 Phố Huế, Phường Hàng Bài, Thành phố Hà Nội" in p.text

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
