import docx
from pathlib import Path

f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\Mẫu tăng vốn công ty TNHH 2TV\04. Giấy ủy quyền.docx")
doc = docx.Document(f)
for i, p in enumerate(doc.paragraphs):
    if any(k in p.text.lower() for k in ["sinh", "cccd", "ngày", "bên a"]):
        print(f"P{i+1}: {repr(p.text)}")
        for r_i, r in enumerate(p.runs):
            print(f"   r{r_i}: {repr(r.text)}")
