import docx
import re
from pathlib import Path

base_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Chuyển đổi loại hình 1TV sang 2 TV")

print(f"Analyzing templates in {base_dir}...\n")

for f in sorted(base_dir.glob("*.docx")):
    doc = docx.Document(str(f))
    print(f"==================================================")
    print(f"FILE: {f.name}")
    print(f"==================================================")
    
    # 1. Existing placeholders
    all_text = []
    for p in doc.paragraphs:
        all_text.append(p.text)
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs:
                    all_text.append(p.text)
    full = "\n".join(all_text)
    
    placeholders = sorted(list(set(re.findall(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", full))))
    print(f"Existing Jinja placeholders ({len(placeholders)}):")
    print(" ", ", ".join(placeholders))
    
    # 2. Find suspicious blank spots or dots (...) or underscores (___)
    suspicious = []
    for idx, p in enumerate(doc.paragraphs):
        txt = p.text.strip()
        if re.search(r"\.{3,}|_{3,}|…|\[[a-zA-Z0-9_]+\]", txt):
            suspicious.append((f"P#{idx}", txt))
            
    for t_idx, t in enumerate(doc.tables):
        for r_idx, r in enumerate(t.rows):
            for c_idx, c in enumerate(r.cells):
                txt = c.text.strip()
                if re.search(r"\.{3,}|_{3,}|…|\[[a-zA-Z0-9_]+\]", txt):
                    suspicious.append((f"T#{t_idx} R#{r_idx} C#{c_idx}", txt.replace('\n', ' ')))
                    
    print(f"\nSuspicious blank spots / dots ({len(suspicious)} found):")
    for loc, txt in suspicious[:15]:
        print(f"  [{loc}] {txt[:120]}")
    if len(suspicious) > 15:
        print(f"  ... and {len(suspicious) - 15} more.")
    print()
