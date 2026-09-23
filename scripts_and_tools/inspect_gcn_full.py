import docx
from pathlib import Path

out_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\scripts_and_tools\output_test_tang_von")
f7a = out_dir / "07. Giấy chứng nhận góp vốn_a (NGUYỄN VĂN AN).docx"
doc = docx.Document(f7a)
for i, p in enumerate(doc.paragraphs):
    if p.text.strip():
        print(f"P{i+1}: {p.text.strip()}")
