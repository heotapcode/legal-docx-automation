import json, shutil
from pathlib import Path
import docx

BASE_DIR = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word")

def update_schema_2tv():
    p = BASE_DIR / "webapp_v2" / "templates" / "Giải thể công ty TNHH 2 TV" / "_schema.json"
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    step_ids = [s.get("id") for s in d.get("steps", [])]
    if "members" not in step_ids:
        d["steps"].append({
            "id": "members",
            "title": "Danh sách thành viên dự họp",
            "fields": [
                {
                    "key": "thanh_vien",
                    "label": "Thành viên công ty",
                    "type": "person_list",
                    "min": 1,
                    "ocr": True,
                    "extra_fields": [
                        {"key": "von_gop", "label": "Vốn góp (VNĐ)", "type": "money"},
                        {"key": "ty_le", "label": "Tỷ lệ (%)", "type": "number"}
                    ]
                }
            ]
        })
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print("Updated _schema.json for Giải thể 2TV")

def update_schema_cp():
    p = BASE_DIR / "webapp_v2" / "templates" / "Giải thể công ty Cổ Phần" / "_schema.json"
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    step_ids = [s.get("id") for s in d.get("steps", [])]
    if "members" not in step_ids:
        d["steps"].append({
            "id": "members",
            "title": "Danh sách cổ đông dự họp",
            "fields": [
                {
                    "key": "thanh_vien",
                    "label": "Cổ đông tham dự",
                    "type": "person_list",
                    "min": 1,
                    "ocr": True,
                    "extra_fields": [
                        {"key": "von_gop", "label": "Vốn góp (VNĐ)", "type": "money"},
                        {"key": "ty_le", "label": "Tỷ lệ (%)", "type": "number"}
                    ]
                }
            ]
        })
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print("Updated _schema.json for Giải thể Cổ Phần")

def sync_all():
    for name in ["Giải thể công ty TNHH 2 TV", "Giải thể công ty Cổ Phần"]:
        src = BASE_DIR / "webapp_v2" / "templates" / name
        dst = BASE_DIR / f"Mẫu {name}"
        if src.exists() and dst.exists():
            for f in src.glob("*.docx"):
                shutil.copy2(f, dst / f.name)
                print(f"Synced {name}/{f.name} -> Mẫu {name}/")

if __name__ == "__main__":
    update_schema_2tv()
    update_schema_cp()
    sync_all()
    print("Done standardizing schemas & syncing Giải thể kits!")
