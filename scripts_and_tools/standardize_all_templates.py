import docx
from pathlib import Path
import sys
sys.path.append(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2")

from services.docx_standardizer import standardize_document

template_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates")
count = 0
for docx_path in template_dir.glob("*/*.docx"):
    if docx_path.name.startswith(('~$', '_')):
        continue
    try:
        doc = docx.Document(str(docx_path))
        standardize_document(doc)
        doc.save(str(docx_path))
        count += 1
        print(f"Standardized: {docx_path.parent.name} / {docx_path.name}")
    except Exception as e:
        print(f"ERROR standardizing {docx_path}: {e}")

print(f"\nDone! Standardized {count} template files.")
