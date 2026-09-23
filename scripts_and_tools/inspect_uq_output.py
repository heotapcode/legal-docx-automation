import docx
from pathlib import Path

out_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\scripts_and_tools\output_test_tang_von")
doc = docx.Document(out_dir / "04. Giấy ủy quyền.docx")
for i, p in enumerate(doc.paragraphs[7:15]):
    print(f"P{i+8}: {p.text}")
