import docx
from pathlib import Path

f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV\06. Danh sách thành viên.docx")
doc = docx.Document(f)
t = doc.tables[0]
for r_idx in range(len(t.rows)):
    row_text = [c.text.strip().replace('\n', ' ') for c in t.rows[r_idx].cells]
    print(f"R{r_idx+1}: {row_text}")
