from pathlib import Path
import json

templates_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates")

dirs = sorted([d for d in templates_dir.iterdir() if d.is_dir()])
print(f"Total template folders: {len(dirs)}")

for i, d in enumerate(dirs, 1):
    schema_file = d / "_schema.json"
    cat = "Unknown"
    desc = ""
    if schema_file.exists():
        try:
            s = json.loads(schema_file.read_text(encoding="utf-8"))
            cat = s.get("category", "")
            desc = s.get("description", "")
        except:
            pass
    docx_files = [f.name for f in d.glob("*.docx") if not f.name.startswith("~$")]
    print(f"{i:2d}. [{cat}] {d.name} ({len(docx_files)} docx files)")
