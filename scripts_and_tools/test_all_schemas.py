import httpx
import json

templates_to_test = [
    "Thành lập mới công ty TNHH 1 TV",
    "Thành lập mới công ty TNHH 2 TV",
    "Thành lập mới công ty Cổ Phần",
    "Tăng vốn công ty TNHH 2 TV",
    "Tăng vốn công ty Cổ Phần",
    "Giải thể công ty TNHH 1 TV",
    "Tạm dừng công ty TNHH 2 TV",
    "Thay đổi nội dung ĐKKD",
    "Chuyển nhượng Công ty TNHH 2 TV",
    "Chuyển đổi loại hình 1TV sang 2 TV"
]

client = httpx.Client(base_url="http://localhost:8002")

print(f"{'MẪU THỦ TỤC':<40} | {'FILES':<6} | {'STATUS'}")
print("-" * 65)

for name in templates_to_test:
    r = client.get(f"/api/templates/{name}/schema")
    if r.status_code == 200:
        data = r.json()
        f_count = data.get("file_count", len(data.get("doc_files", [])))
        files = data.get("doc_files", [])
        print(f"{name:<40} | {f_count:<6} | OK ({len(files)} docs: {files[:2]})")
    else:
        print(f"{name:<40} | FAIL ({r.status_code})")
