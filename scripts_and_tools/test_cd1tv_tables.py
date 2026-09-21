import docx
import copy
from pathlib import Path

def test_cd1tv_tables():
    template_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Chuyển đổi loại hình 1TV sang 2 TV")
    
    # Test 04. Danh sách thành viên.docx
    doc4 = docx.Document(str(template_dir / "04. Danh sách thành viên.docx"))
    t4 = doc4.tables[0]
    print(f"04. Danh sách thành viên: {len(t4.rows)} rows in table 0")
    for r in t4.rows:
        print(" ", [c.text.strip().replace('\n', ' ') for c in r.cells[:4]])
        
    # Test 05. Danh sách chủ sở hữu hưởng lợi.docx
    doc5 = docx.Document(str(template_dir / "05. Danh sách chủ sở hữu hưởng lợi.docx"))
    t5 = doc5.tables[0]
    print(f"\n05. Danh sách CSHHL: {len(t5.rows)} rows in table 0")
    for r in t5.rows:
        print(" ", [c.text.strip().replace('\n', ' ') for c in r.cells[:4]])

if __name__ == "__main__":
    test_cd1tv_tables()
