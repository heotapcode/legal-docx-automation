import docx
from pathlib import Path

f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV\06. Danh sách thành viên.docx")
doc = docx.Document(f)
for p in doc.paragraphs:
    if p.text.strip():
        print(f"P: {p.text.strip()}")
for t_idx, t in enumerate(doc.tables):
    if t_idx > 0:
        print(f"Table {t_idx+1}:")
        for r in t.rows:
            print(f"  {[c.text.strip().replace(chr(10), ' ') for c in r.cells]}")
