import docx
from pathlib import Path

f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV\02. Biên bản họp.docx")
doc = docx.Document(f)
p9 = doc.paragraphs[8]
print("P9 text:", repr(p9.text))
for i, r in enumerate(p9.runs):
    print(f"Run {i}: {repr(r.text)}")
