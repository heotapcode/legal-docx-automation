import docx
from pathlib import Path

f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV\02. Biên bản họp.docx")
doc = docx.Document(f)
for i, p in enumerate(doc.paragraphs):
    if any(k in p.text for k in ["{{", "ddpl", "tv2", "vốn", "Chủ tọa", "Thư ký"]):
        print(f"P{i+1}: {p.text}")
