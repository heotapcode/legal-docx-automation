import docx
from pathlib import Path

f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV\03. Quyết định.docx")
doc = docx.Document(f)
for p in doc.paragraphs:
    if "địa chỉ" in p.text.lower() or "trụ sở" in p.text.lower():
        print(p.text)
