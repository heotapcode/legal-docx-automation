import docx
from pathlib import Path

out_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\scripts_and_tools\output_test_tang_von")

f6 = out_dir / "06. Danh sách thành viên.docx"
print("=== 06. Danh sách thành viên.docx ===")
doc6 = docx.Document(f6)
t1 = doc6.tables[0]
for r_idx in range(len(t1.rows)):
    cells = [c.text.strip().replace('\n', ' ') for c in t1.rows[r_idx].cells]
    print(f"R{r_idx+1}: {cells}")

print("\n=== 07. Giấy chứng nhận góp vốn_a ===")
f7a = out_dir / "07. Giấy chứng nhận góp vốn_a (NGUYỄN VĂN AN).docx"
doc7a = docx.Document(f7a)
for p in doc7a.paragraphs:
    if p.text.strip():
        print(f"P: {p.text.strip()}")
for t in doc7a.tables:
    for r in t.rows:
        print(f"Table: {[c.text.strip().replace(chr(10), ' ') for c in r.cells]}")

print("\n=== 07. Giấy chứng nhận góp vốn_b ===")
f7b = out_dir / "07. Giấy chứng nhận góp vốn_b (TRẦN THỊ BÌNH).docx"
doc7b = docx.Document(f7b)
for p in doc7b.paragraphs:
    if p.text.strip():
        print(f"P: {p.text.strip()}")
for t in doc7b.tables:
    for r in t.rows:
        print(f"Table: {[c.text.strip().replace(chr(10), ' ') for c in r.cells]}")
