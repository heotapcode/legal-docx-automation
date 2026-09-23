import docx
from pathlib import Path

templates_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates")

for f in templates_dir.glob("*/*.docx"):
    if f.name.startswith("~$"): continue
    try:
        doc = docx.Document(f)
        for p in doc.paragraphs:
            if "ĐỖ QUANG HIẾU" in p.text or "0987.135.358" in p.text:
                print(f"{f.parent.name} / {f.name}: {p.text[:80]}")
                break
    except:
        pass
