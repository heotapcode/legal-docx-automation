import docx
from pathlib import Path

f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Thành lập mới công ty TNHH 2 TV\04. Giấy ủy quyền.docx")
doc = docx.Document(f)
for p in doc.paragraphs:
    if "sinh" in p.text.lower() or "bên a" in p.text.lower():
        print(repr(p.text))
