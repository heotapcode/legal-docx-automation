import docx, re, shutil
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word")
TPL_DIR = BASE_DIR / "webapp_v2" / "templates" / "Tăng vốn công ty TNHH 2 TV"
DST_DIR = BASE_DIR / "Mẫu tăng vốn công ty TNHH 2TV"

def fix_file_06():
    p = TPL_DIR / "06. Danh sách thành viên.docx"
    doc = docx.Document(p)
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                if "2.{{ von_cu_so }}" in c.text:
                    c.text = c.text.replace("2.{{ von_cu_so }}", "{{ tv2_von_cu_so }}")
    doc.save(p)
    print("Fixed 06. Danh sách thành viên.docx")

def fix_file_07():
    p = TPL_DIR / "07. Giấy chứng nhận góp vốn.docx"
    doc = docx.Document(p)
    for p_item in doc.paragraphs:
        if "tv2_" in p_item.text:
            p_item.text = p_item.text.replace("tv2_", "tv_")
        if "2.{{ von_cu_so }}" in p_item.text:
            p_item.text = re.sub(r'2\.\{\{\s*von_cu_so\s*\}\}\s*VNĐ\s*\(Hai tỷ\s*\{\{\s*von_cu_chu\s*\}\}\)', '{{ tv_von_so }} đồng ({{ tv_von_chu }})', p_item.text)
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                if "tv2_" in c.text:
                    c.text = c.text.replace("tv2_", "tv_")
                if "2.{{ von_cu_so }}" in c.text:
                    c.text = re.sub(r'2\.\{\{\s*von_cu_so\s*\}\}\s*VNĐ\s*\(Hai tỷ\s*\{\{\s*von_cu_chu\s*\}\}\)', '{{ tv_von_so }} đồng ({{ tv_von_chu }})', c.text)
    doc.save(p)
    print("Standardized 07. Giấy chứng nhận góp vốn.docx")

def sync_to_root():
    if DST_DIR.exists():
        for f in TPL_DIR.glob("*.docx"):
            shutil.copy2(f, DST_DIR / f.name)
            print(f"Synced {f.name} to {DST_DIR.name}")

if __name__ == "__main__":
    fix_file_06()
    fix_file_07()
    sync_to_root()
    print("Done standardizing Tăng vốn công ty TNHH 2 TV templates!")
