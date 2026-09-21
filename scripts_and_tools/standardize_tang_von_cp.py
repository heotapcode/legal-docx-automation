import re, json, shutil, copy
from pathlib import Path
import docx

BASE_DIR = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word")
TPL_DIR = BASE_DIR / "webapp_v2" / "templates" / "Tăng vốn công ty Cổ Phần"
DST_DIR = BASE_DIR / "Mẫu tăng vốn công ty cổ phần"

def replace_in_doc(doc, replacements):
    for p in doc.paragraphs:
        for old, new in replacements.items():
            if old in p.text:
                p.text = p.text.replace(old, new)
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                for old, new in replacements.items():
                    if old in c.text:
                        c.text = c.text.replace(old, new)

def standardize_file_01():
    p = TPL_DIR / "01. Thông báo thay đổi ĐKKD.docx"
    doc = docx.Document(p)
    replacements = {
        "CÔNG TY CỔ PHẦN THƯƠNG MẠI HÀ PHƯƠNG": "{{ ten_cong_ty_vn }}",
        "0500468371": "{{ ma_so_thue }}",
        "20.000.000.000 VNĐ (Hai mươi tỷ đồng)": "{{ von_cu_so }} đồng ({{ von_cu_chu }})",
        "40.000.000.000 VNĐ (Bốn mươi tỷ đồng)": "{{ von_dieu_le_so }} đồng ({{ von_dieu_le_chu }})",
        "40.000.000.000 VNĐ": "{{ von_dieu_le_so }} đồng",
        "NGUYỄN ĐÌNH LẬP": "{{ ddpl_ho_ten }}"
    }
    replace_in_doc(doc, replacements)
    doc.save(p)
    print("Standardized 01. Thông báo thay đổi ĐKKD.docx")

def standardize_file_02():
    p = TPL_DIR / "02. Thông báo bổ sung cập nhật.docx"
    doc = docx.Document(p)
    replacements = {
        "CÔNG TY CỔ PHẦN THƯƠNG MẠI HÀ PHƯƠNG": "{{ ten_cong_ty_vn }}",
        "0500468371": "{{ ma_so_thue }}",
        "02437893830 / 02437893832": "{{ sdt_cong_ty }}",
        "familywindow@gmail.com": "{{ email_cong_ty }}",
        "NGUYỄN ĐÌNH LẬP": "{{ ddpl_ho_ten }}"
    }
    replace_in_doc(doc, replacements)
    doc.save(p)
    print("Standardized 02. Thông báo bổ sung cập nhật.docx")

def standardize_file_03():
    p = TPL_DIR / "03. Quyết định.docx"
    doc = docx.Document(p)
    replacements = {
        "CÔNG TY CỔ PHẦN THƯƠNG MẠI HÀ PHƯƠNG": "{{ ten_cong_ty_vn }}",
        "20.000.000.000 VNĐ (Hai mươi tỷ đồng)": "{{ von_cu_so }} đồng ({{ von_cu_chu }})",
        "40.000.000.000 VNĐ (Bốn mươi tỷ đồng)": "{{ von_dieu_le_so }} đồng ({{ von_dieu_le_chu }})",
        "40.000.000.000 VNĐ": "{{ von_dieu_le_so }} đồng",
        "ông NGUYỄN ĐÌNH LẬP": "{{ 'ông' if ddpl_gioi_tinh == 'Nam' else 'bà' }} {{ ddpl_ho_ten }}",
        "NGUYỄN ĐÌNH LẬP": "{{ ddpl_ho_ten }}"
    }
    replace_in_doc(doc, replacements)
    doc.save(p)
    print("Standardized 03. Quyết định.docx")

def standardize_file_04():
    p = TPL_DIR / "04. Biên bản họp.docx"
    doc = docx.Document(p)
    replacements = {
        "CÔNG TY CỔ PHẦN THƯƠNG MẠI HÀ PHƯƠNG": "{{ ten_cong_ty_vn }}",
        "0108934485": "{{ ma_so_thue }}",
        "Khối Bạch Đằng, Phường Vạn Phúc, Hà Nội": "{{ dia_chi_so_nha }}, {{ dia_chi_xa_phuong }}, {{ dia_chi_tinh_thanh }}",
        "No 01 - Khối Bạch Đằng, Phường Vạn Phúc, Hà Nội": "{{ dia_chi_so_nha }}, {{ dia_chi_xa_phuong }}, {{ dia_chi_tinh_thanh }}",
        "20.000.000.000 VNĐ (Hai mươi tỷ đồng)": "{{ von_cu_so }} đồng ({{ von_cu_chu }})",
        "20.000.000.000 VNĐ": "{{ von_cu_so }} đồng",
        "40.000.000.000 VNĐ (Bốn mươi tỷ đồng)": "{{ von_dieu_le_so }} đồng ({{ von_dieu_le_chu }})",
        "40.000.000.000 VNĐ": "{{ von_dieu_le_so }} đồng",
        "Chủ toạ: NGUYỄN ĐÌNH LẬP": "Chủ toạ: {{ ddpl_ho_ten }}",
        "NGUYỄN ĐÌNH LẬP": "{{ ddpl_ho_ten }}"
    }
    replace_in_doc(doc, replacements)
    doc.save(p)
    print("Standardized 04. Biên bản họp.docx")

def standardize_file_05():
    p = TPL_DIR / "05. Giấy ủy quyền.docx"
    doc = docx.Document(p)
    replacements = {
        "CÔNG TY CỔ PHẦN THƯƠNG MẠI HÀ PHƯƠNG": "{{ ten_cong_ty_vn }}",
        "0500468371": "{{ ma_so_thue }}",
        "Ông: NGUYỄN ĐÌNH LẬP": "{{ 'Ông' if ddpl_gioi_tinh == 'Nam' else 'Bà' }}: {{ ddpl_ho_ten }}",
        "Ngày sinh: 16/03/1958": "Ngày sinh: {{ ddpl_ngay_sinh }}",
        "Giới tính: Nam": "Giới tính: {{ ddpl_gioi_tinh }}",
        "NGUYỄN ĐÌNH LẬP": "{{ ddpl_ho_ten }}"
    }
    replace_in_doc(doc, replacements)
    doc.save(p)
    print("Standardized 05. Giấy ủy quyền.docx")

def update_schema():
    p = TPL_DIR / "_schema.json"
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)

    # Check if step members already exists
    step_ids = [s.get("id") for s in d.get("steps", [])]
    if "members" not in step_ids:
        d["steps"].append({
            "id": "members",
            "title": "Danh sách cổ đông công ty",
            "fields": [
                {
                    "key": "thanh_vien",
                    "label": "Cổ đông công ty",
                    "type": "person_list",
                    "min": 1,
                    "ocr": True,
                    "extra_fields": [
                        {
                            "key": "von_gop",
                            "label": "Vốn sau tăng (VNĐ)",
                            "type": "money",
                            "required": True
                        },
                        {
                            "key": "ty_le",
                            "label": "Tỷ lệ sở hữu (%)",
                            "type": "number",
                            "required": True
                        }
                    ]
                }
            ]
        })
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print("Updated _schema.json with members step")

def sync_to_root():
    if DST_DIR.exists():
        for f in TPL_DIR.glob("*.docx"):
            shutil.copy2(f, DST_DIR / f.name)
            print(f"Synced {f.name} to {DST_DIR.name}")

if __name__ == "__main__":
    standardize_file_01()
    standardize_file_02()
    standardize_file_03()
    standardize_file_04()
    standardize_file_05()
    update_schema()
    sync_to_root()
    print("All standardization complete for Tăng vốn công ty Cổ Phần!")
