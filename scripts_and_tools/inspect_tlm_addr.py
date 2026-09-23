import docx
from pathlib import Path

f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Thành lập mới công ty TNHH 2 TV\01. Giấy đề nghị ĐKDN.docx")
doc = docx.Document(f)
for i, p in enumerate(doc.paragraphs):
    if "Địa chỉ" in p.text or "trụ sở" in p.text.lower():
        print(f"P{i+1}: {p.text}")
