import docx
from pathlib import Path

f1 = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV\04. Giấy ủy quyền.docx")
f2 = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\Mẫu tăng vốn công ty TNHH 2TV\04. Giấy ủy quyền.docx")

d1 = docx.Document(f1)
d2 = docx.Document(f2)

p1 = [p.text for p in d1.paragraphs]
p2 = [p.text for p in d2.paragraphs]

print(f"File 1 len paragraphs: {len(p1)}, File 2 len paragraphs: {len(p2)}")
if p1 == p2:
    print("Paragraphs are identical!")
else:
    for i, (a, b) in enumerate(zip(p1, p2)):
        if a != b:
            print(f"Diff P{i+1}:\n  F1: {repr(a)}\n  F2: {repr(b)}")
