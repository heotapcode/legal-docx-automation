import docx
from pathlib import Path

out_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\scripts_and_tools\output_test_tang_von")

for f in sorted(out_dir.glob("*.docx")):
    if f.name.startswith("01") or f.name.startswith("02"):
        continue
    print(f"\n=======================================================")
    print(f"FILE: {f.name}")
    print(f"=======================================================")
    doc = docx.Document(f)
    
    print("\n--- Paragraphs ---")
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if t:
            print(f"  P{i+1}: {t}")
            
    print("\n--- Tables Content ---")
    for t_idx, table in enumerate(doc.tables):
        print(f"  Table {t_idx+1} ({len(table.rows)} rows x {len(table.columns)} cols):")
        for r_idx, row in enumerate(table.rows):
            row_vals = [c.text.strip().replace('\n', ' ') for c in row.cells]
            if any(row_vals):
                print(f"    R{r_idx+1}: {' | '.join(row_vals[:6])}")
