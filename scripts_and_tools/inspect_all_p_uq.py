import docx
from pathlib import Path

f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV\04. Giấy ủy quyền.docx")
doc = docx.Document(f)
for i, p in enumerate(doc.paragraphs):
    print(f"P{i+1}: {repr(p.text)}")
