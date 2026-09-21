"""
Script chuyển đổi file Word mã ngành nghề sang JSON để bot có thể tìm kiếm nhanh.
"""
import os
import json
from docx import Document

BASE_DIR = r"c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word"
WORD_FILE = os.path.join(BASE_DIR, "Danh sách mã ngành nghề 2026.docx")
OUTPUT_JSON = os.path.join(BASE_DIR, "ma_nganh_nghe.json")

def build_json():
    doc = Document(WORD_FILE)
    
    entries = []
    for tbl in doc.tables:
        for i, row in enumerate(tbl.rows):
            cells = [cell.text.strip() for cell in row.cells]
            if i == 0:
                continue  # bỏ header
            cap1, cap2, cap3, cap4, cap5, ten_nganh = (cells + [""] * 6)[:6]
            
            # Lấy mã ngành chi tiết nhất có giá trị
            ma_nganh = cap5 or cap4 or cap3 or cap2 or cap1
            
            if ma_nganh and ten_nganh and ma_nganh not in ["Cấp 1","Cấp 2","Cấp 3","Cấp 4","Cấp 5"]:
                entries.append({
                    "ma": ma_nganh,
                    "ten": ten_nganh,
                    "cap1": cap1,
                    "cap2": cap2,
                    "cap3": cap3,
                    "cap4": cap4,
                    "cap5": cap5,
                })
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    
    print(f"Đã tạo {len(entries)} mục mã ngành vào {OUTPUT_JSON}")
    # Hiển thị mẫu
    for e in entries[:5]:
        print(e)

if __name__ == "__main__":
    build_json()
