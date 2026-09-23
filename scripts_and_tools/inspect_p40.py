import docx
from pathlib import Path

out_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\scripts_and_tools\output_test_tang_von")
doc = docx.Document(out_dir / "02. Biên bản họp.docx")
for i, p in enumerate(doc.paragraphs):
    if "phiếu biểu quyết" in p.text.lower() or "quy ước" in p.text.lower():
        print(f"P{i+1}: {p.text}")
