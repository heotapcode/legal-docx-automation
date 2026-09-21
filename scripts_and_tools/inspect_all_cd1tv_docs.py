import docx
from pathlib import Path

base_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Chuyển đổi loại hình 1TV sang 2 TV")

for f in sorted(base_dir.glob("*.docx")):
    doc = docx.Document(str(f))
    out_file = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\scripts_and_tools") / f"text_{f.stem}.txt"
    with open(out_file, "w", encoding="utf-8") as out:
        out.write(f"=== DOCUMENT: {f.name} ===\n\n")
        out.write("--- PARAGRAPHS ---\n")
        for i, p in enumerate(doc.paragraphs):
            t = p.text.strip()
            if t:
                out.write(f"P#{i}: {t}\n")
                
        out.write("\n--- TABLES ---\n")
        for t_idx, t in enumerate(doc.tables):
            out.write(f"\n[Table {t_idx} - {len(t.rows)} rows x {len(t.columns)} cols]\n")
            for r_idx, r in enumerate(t.rows):
                row_txt = [c.text.strip().replace('\n', ' ') for c in r.cells]
                out.write(f"  R#{r_idx}: {row_txt}\n")
    print(f"Dumped text for {f.name} -> {out_file.name}")
