import docx
from pathlib import Path

f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV\01. Thông báo thay đổi ĐKKD.docx")
doc = docx.Document(f)
for i, p in enumerate(doc.paragraphs):
    if "Địa chỉ" in p.text or "trụ sở" in p.text.lower():
        print(f"P{i+1}: {p.text}")
