import docx
from pathlib import Path

out_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\scripts_and_tools\output_test_tang_von")

for f in sorted(out_dir.glob("*.docx")):
    if not (f.name.startswith("05") or f.name.startswith("06") or f.name.startswith("07")):
        continue
    print(f"\n=======================================================")
    print(f"FILE: {f.name}")
    print(f"=======================================================")
    doc = docx.Document(f)
    for t_idx, table in enumerate(doc.tables):
        print(f"  --- Table {t_idx+1} ({len(table.rows)} rows x {len(table.columns)} cols) ---")
        for r_idx, row in enumerate(table.rows):
            cells = [c.text.strip().replace('\n', ' ') for c in row.cells]
            print(f"    R{r_idx+1}: {' | '.join(cells)}")
    for p in doc.paragraphs:
        t = p.text.strip()
        if t:
            print(f"  P: {t}")
