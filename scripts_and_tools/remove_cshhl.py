import json
import os
from docx import Document

# 1. Remove CSHHL_GIOI_TINH from folder_keys.json
with open('folder_keys.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for template, keys in data.items():
    if "CSHHL_GIOI_TINH" in keys:
        keys.remove("CSHHL_GIOI_TINH")

with open('folder_keys.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Removed from folder_keys.json")

# 2. Revert in template
filepath = 'Mẫu Chuyển nhượng công ty TNHH 1 TV/04. Danh sách chủ sở hữu hưởng lợi.docx'
if os.path.exists(filepath):
    doc = Document(filepath)
    modified = False
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if '[CSHHL_GIOI_TINH]' in p.text:
                        p.text = p.text.replace('[CSHHL_GIOI_TINH]', 'Giới tính')
                        modified = True
    if modified:
        doc.save(filepath)
        print("Reverted template")
