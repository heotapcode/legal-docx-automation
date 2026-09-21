import os
import sys
import re
import docx
from pathlib import Path

BASE_DIR = Path(r'C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2')
TPL_DIR = BASE_DIR / 'templates' / 'Chuyển đổi loại hình 1TV sang 2 TV'

print(f"=== AUDITING TEMPLATES IN: {TPL_DIR} ===")

files = sorted([f for f in os.listdir(TPL_DIR) if f.endswith('.docx') and not f.startswith('~')])

audit_report = {}

for fname in files:
    fpath = TPL_DIR / fname
    doc = docx.Document(str(fpath))
    
    paras_tags = []
    tables_tags = []
    
    # Check paragraphs
    for p_idx, p in enumerate(doc.paragraphs):
        text = p.text
        j_tags = re.findall(r'\{\{([^}]+)\}\}', text)
        b_tags = re.findall(r'\[([A-Z0-9_]+)\]', text)
        if j_tags or b_tags or any(k in text for k in ['ddpl_', 'tv2_', 'csh_', 'tv1_']):
            paras_tags.append({
                'loc': f"P{p_idx + 1}",
                'text': text.strip(),
                'jinja': [j.strip() for j in j_tags],
                'bracket': b_tags
            })
            
    # Check tables
    for t_idx, t in enumerate(doc.tables):
        for r_idx, r in enumerate(t.rows):
            for c_idx, c in enumerate(r.cells):
                text = c.text.strip()
                j_tags = re.findall(r'\{\{([^}]+)\}\}', text)
                b_tags = re.findall(r'\[([A-Z0-9_]+)\]', text)
                if j_tags or b_tags or any(k in text for k in ['ddpl_', 'tv2_', 'csh_', 'tv1_']):
                    tables_tags.append({
                        'loc': f"T{t_idx+1}R{r_idx+1}C{c_idx+1}",
                        'text': text.replace('\n', ' '),
                        'jinja': [j.strip() for j in j_tags],
                        'bracket': b_tags
                    })
                    
    audit_report[fname] = {
        'paras': paras_tags,
        'tables': tables_tags
    }

print(f"Audited {len(files)} files.")
for fname, rep in audit_report.items():
    print(f"\n=======================================================")
    print(f"FILE: {fname}")
    print(f"=======================================================")
    print(f"--- Paragraphs with tags ({len(rep['paras'])}):")
    for item in rep['paras'][:10]:
        print(f"  [{item['loc']}] {item['text'][:100]}")
    if len(rep['paras']) > 10:
        print(f"  ... and {len(rep['paras']) - 10} more paragraphs")
        
    print(f"--- Table cells with tags ({len(rep['tables'])}):")
    for item in rep['tables'][:10]:
        print(f"  [{item['loc']}] {item['text'][:100]}")
    if len(rep['tables']) > 10:
        print(f"  ... and {len(rep['tables']) - 10} more table cells")
