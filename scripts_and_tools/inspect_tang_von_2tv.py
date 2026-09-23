import docx
import re
import os
from pathlib import Path

template_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV")

print(f"=== Inspecting Docx files in: {template_dir} ===")

placeholder_regex = re.compile(r"\{\{([^}]+)\}\}|<<([^>]+)>>|\[\[([^\]]+)\]\]|«([^»]+)»")

for f in sorted(template_dir.glob("*.docx")):
    if f.name.startswith("~$"):
        continue
    doc = docx.Document(f)
    print(f"\n--- FILE: {f.name} ---")
    
    # Check paragraphs
    all_placeholders = set()
    for p in doc.paragraphs:
        for m in placeholder_regex.finditer(p.text):
            all_placeholders.add(m.group(0))
            
    # Check tables
    table_placeholders = set()
    row_counts = []
    for t_idx, table in enumerate(doc.tables):
        row_counts.append(f"T{t_idx+1}({len(table.rows)}x{len(table.columns)})")
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for m in placeholder_regex.finditer(p.text):
                        table_placeholders.add(m.group(0))
                        
    print(f"Tables: {', '.join(row_counts) if row_counts else 'None'}")
    print(f"Paragraph Placeholders ({len(all_placeholders)}): {sorted(list(all_placeholders))}")
    print(f"Table Placeholders ({len(table_placeholders)}): {sorted(list(table_placeholders))}")
