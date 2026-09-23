import docx
from pathlib import Path

templates_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates")

for f in sorted(templates_dir.glob("*/*ủy quyền*.docx")):
    try:
        doc = docx.Document(f)
        for p in doc.paragraphs:
            if "Bên A" in p.text or "sinh:" in p.text.lower():
                print(f"[{f.parent.name} / {f.name}] P: {repr(p.text)}")
    except Exception as e:
        pass
