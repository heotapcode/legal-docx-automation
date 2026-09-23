import httpx

client = httpx.Client(base_url="http://localhost:8002", timeout=10)
r = client.get("/api/templates")
assert r.status_code == 200
templates = r.json()["templates"]
print(f"Tổng số biểu mẫu thủ tục: {len(templates)}")

ok_count = 0
for t in templates:
    name = t["name"]
    res = client.get(f"/api/templates/{name}/schema")
    if res.status_code == 200:
        data = res.json()
        doc_count = len(data.get("doc_files", []))
        ok_count += 1
    else:
        print(f"Lỗi: {name} status={res.status_code}")

print(f"Đã kiểm tra thành công {ok_count}/{len(templates)} biểu mẫu.")
