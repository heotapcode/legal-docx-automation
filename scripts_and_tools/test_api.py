import sys
import os
import json
import zipfile
from io import BytesIO

sys.path.insert(0, r"c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word\webapp_v2")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
logs = []

# 1. Test GET /
res_root = client.get("/")
logs.append(f"1. GET / status: {res_root.status_code}")

# 2. Test GET /api/templates
res_templates = client.get("/api/templates")
logs.append(f"2. GET /api/templates status: {res_templates.status_code}")

# 3. Test GET /api/templates/{name}/schema
res_schema = client.get("/api/templates/T%E1%BA%A1m%20d%E1%BB%ABng%20c%C3%B4ng%20ty%20TNHH%201%20TV/schema")
logs.append(f"3. GET /api/templates/.../schema status: {res_schema.status_code}")

# 4. Test GET /api/templates/{name}/fields
res_fields = client.get("/api/templates/T%E1%BA%A1m%20d%E1%BB%ABng%20c%C3%B4ng%20ty%20TNHH%201%20TV/fields")
logs.append(f"4. GET /api/templates/.../fields status: {res_fields.status_code}")

# 5. Test POST /api/documents/generate
payload = {
    "template_name": "Tạm dừng công ty TNHH 1 TV",
    "context": {
        "ten_cong_ty_vn": "CÔNG TY TNHH FASTAPI INTEGRATION TEST",
        "ma_so_thue": "0101234567",
        "ddpl": {
            "ho_ten": "NGUYỄN VĂN FASTAPI",
            "ngay_sinh": "01/01/1990",
            "so_cccd": "001090123456",
            "gioi_tinh": "Nam",
            "dia_chi_so_nha": "Số 12 phố Huế",
            "dia_chi_xa_phuong": "Phường Hàng Bài",
            "dia_chi_tinh_thanh": "Hà Nội"
        }
    }
}
res_gen = client.post("/api/documents/generate", json=payload)
logs.append(f"5. POST /api/documents/generate status: {res_gen.status_code}")
logs.append(f"   Response headers: {dict(res_gen.headers)}")

if res_gen.status_code == 200 and "application/zip" in res_gen.headers.get("content-type", ""):
    try:
        with zipfile.ZipFile(BytesIO(res_gen.content), "r") as zf:
            logs.append(f"   Files in generated zip: {zf.namelist()}")
            logs.append("   -> ZIP generation: SUCCESS!")
    except Exception as ze:
        logs.append(f"   -> ZIP error: {ze}")
else:
    logs.append(f"   Response text error: {res_gen.text}")

# 6. Test GET /api/nganh/search
res_nganh = client.get("/api/nganh/search?q=ph%E1%BA%A7n%20m%E1%BB%81m")
logs.append(f"6. GET /api/nganh/search status: {res_nganh.status_code}, count: {len(res_nganh.json().get('results', []))}")

with open(r"c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word\test_api_log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(logs))

print("TEST COMPLETED")
