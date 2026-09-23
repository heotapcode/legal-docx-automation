import docx
from pathlib import Path

f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV\04. Giấy ủy quyền.docx")
doc = docx.Document(f)
p11 = doc.paragraphs[10] # P11
print("P11 text:", repr(p11.text))
print("P11 XML:\n", p11._p.xml)
