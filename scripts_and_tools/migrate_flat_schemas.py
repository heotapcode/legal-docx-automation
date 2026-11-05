"""Chuyển các _schema.json dạng phẳng ("fields": [...]) sang dạng chuẩn ("steps": [...]).

Frontend (wizard.js) chỉ hiểu dạng "steps"; schema dạng phẳng làm wizard không hiện ô nhập nào.
Chạy một lần từ thư mục gốc repo:
    python scripts_and_tools/migrate_flat_schemas.py
"""
import json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "webapp_v2" / "templates"

# (tiền tố tên trường, id bước, tiêu đề bước) — xét theo thứ tự, tiền tố rỗng = mặc định
GROUPS = [
    ("ddpl_", "ddpl", "Người đại diện theo pháp luật"),
    ("csh_", "csh", "Chủ sở hữu / Chủ tịch Hội đồng thành viên"),
    ("tv2_", "tv2", "Thành viên thứ hai"),
    ("ktt_", "ktt", "Kế toán trưởng"),
    ("thu_ky_", "thu_ky", "Thư ký cuộc họp"),
    ("", "company", "Thông tin doanh nghiệp & hồ sơ"),
]
TYPE_MAP = {"string": "text", "currency": "money"}
EXTRA = {
    # Bộ có bảng "Mã ngành / Tên ngành" trong file 01 -> cần bước chọn ngành nghề
    "Thay đổi ngành nghề kinh doanh TNHH 1 TV": {"has_nganh": True, "category": "Thay đổi"},
}
DEFAULT_CATEGORY = {
    "Tăng vốn": "Tăng vốn", "Giải thể": "Giải thể", "Hủy bỏ": "Giải thể",
    "Tạm dừng": "Tạm dừng & Hoạt động lại", "Thay đổi": "Thay đổi",
}


def convert_field(f: dict) -> dict:
    key = f["name"]
    typ = TYPE_MAP.get(f.get("type", "string"), "text")
    if key == "ma_so_thue":
        typ = "mst_lookup"
    out = {"key": key, "label": f.get("label", key), "type": typ}
    if f.get("required"):
        out["required"] = True
    if "gioi_tinh" in key:
        out["placeholder"] = "Nam hoặc Nữ"
    elif f.get("default"):
        # Giá trị mặc định cũ là dữ liệu mẫu -> chỉ dùng làm gợi ý, không điền sẵn vào hồ sơ thật
        out["placeholder"] = f"VD: {f['default']}"
    return out


def migrate(schema: dict) -> dict:
    steps = {gid: {"id": gid, "title": title, "fields": []} for _, gid, title in GROUPS}
    for f in schema["fields"]:
        if f.get("computed") or f["name"].endswith("danh_xung"):  # backend tự tính (von_*_chu, danh xưng từ giới tính)
            continue
        gid = next(g for prefix, g, _ in GROUPS if f["name"].startswith(prefix))
        steps[gid]["fields"].append(convert_field(f))
    order = ["company"] + [g for _, g, _ in GROUPS if g != "company"]
    name = schema["name"]
    out = {
        "name": name,
        "display_name": schema.get("display_name", name),
        "category": schema.get("category") or next((v for k, v in DEFAULT_CATEGORY.items() if name.startswith(k)), "Khác"),
        "description": schema.get("description", ""),
        "has_nganh": schema.get("has_nganh", False),
        "steps": [steps[g] for g in order if steps[g]["fields"]],
    }
    out.update(EXTRA.get(name, {}))
    return out


def main():
    for path in sorted(TEMPLATES_DIR.glob("*/_schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        if "steps" in schema or "fields" not in schema:
            continue
        new = migrate(schema)
        path.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        n = sum(len(s["fields"]) for s in new["steps"])
        print(f"Đã chuyển: {path.parent.name} ({n} trường, {len(new['steps'])} bước)")


if __name__ == "__main__":
    main()
