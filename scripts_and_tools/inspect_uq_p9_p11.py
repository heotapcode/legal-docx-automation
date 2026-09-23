import docx
from pathlib import Path

f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV\04. Giấy ủy quyền.docx")
doc = docx.Document(f)

print("P9:")
for i, r in enumerate(doc.paragraphs[8].runs):
    print(f"  run {i}: {repr(r.text)}")

print("P11:")
for i, r in enumerate(doc.paragraphs[10].runs):
    print(f"  run {i}: {repr(r.text)}")
