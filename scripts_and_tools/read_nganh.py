"""
Script đọc nhanh file mã ngành nghề bằng python-docx (không dùng win32com)
"""
import os
from docx import Document

BASE_DIR = r"c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word"
WORD_FILE = os.path.join(BASE_DIR, "Danh sách mã ngành nghề 2026.docx")

def read_fast():
    doc = Document(WORD_FILE)
    
    lines = []
    # Đọc paragraphs
    for para in doc.paragraphs:
        t = para.text.strip()
        if t:
            lines.append(t)
    
    # Đọc tables
    table_rows = []
    for tbl in doc.tables:
        for row in tbl.rows:
            row_data = [cell.text.strip() for cell in row.cells]
            # Bỏ dòng trống hoàn toàn
            if any(d for d in row_data):
                table_rows.append(row_data)
    
    return lines, table_rows

if __name__ == "__main__":
    print("Đọc file...")
    lines, tables = read_fast()
    
    with open(os.path.join(BASE_DIR, "ma_nganh_preview.txt"), "w", encoding="utf-8") as f:
        f.write("=== PARAGRAPHS (50 đầu) ===\n")
        for i, l in enumerate(lines[:50]):
            f.write(f"{i}: {l}\n")
        
        f.write("\n\n=== TABLE ROWS (100 đầu) ===\n")
        for i, row in enumerate(tables[:100]):
            f.write(f"Row {i}: {' | '.join(row)}\n")
    
    print(f"Paragraphs: {len(lines)}, Table rows: {len(tables)}")
    print("10 hàng đầu trong bảng:")
    for row in tables[:10]:
        print(" | ".join(row))
