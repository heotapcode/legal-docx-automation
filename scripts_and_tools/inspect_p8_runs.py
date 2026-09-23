import docx
from pathlib import Path

f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV\01. Thông báo thay đổi ĐKKD.docx")
doc = docx.Document(f)
p8 = doc.paragraphs[7]
print("P8 text:", repr(p8.text))
for i, r in enumerate(p8.runs):
    print(f"Run {i}: {repr(r.text)}")
