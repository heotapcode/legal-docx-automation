import json
import os
from docx import Document

# 1. Remove from folder_keys.json
with open('folder_keys.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for template, keys in data.items():
    data[template] = [k for k in keys if not k.startswith("NGUOI_DUOC_UY_QUYEN_")]

with open('folder_keys.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Updated folder_keys.json")

# 2. Revert in 1TV templates
base_dir = 'Mẫu Chuyển nhượng công ty TNHH 1 TV'
for f in os.scandir(base_dir):
    if f.name.endswith('.docx') and not f.name.startswith('~'):
        doc = Document(f.path)
        modified = False
        for p in doc.paragraphs:
            if '[NGUOI_DUOC_UY_QUYEN_GIOI_TINH]' in p.text:
                p.text = p.text.replace('[NGUOI_DUOC_UY_QUYEN_GIOI_TINH]', 'Nam')
                modified = True
        if modified:
            doc.save(f.path)
            print(f"Reverted {f.name}")
