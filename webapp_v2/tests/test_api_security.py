"""Test API: danh sách mẫu, chống path traversal, chống chèn template, CORS."""
import pytest

from conftest import read_zip


def test_index_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "/static/js/utils.js" in r.text, "utils.js (escapeHtml) phải được nạp trước các trang"


def test_list_templates(client):
    r = client.get("/api/templates")
    assert r.status_code == 200
    templates = r.json()["templates"]
    assert len(templates) >= 20
    assert all(t["has_schema"] for t in templates)
    assert all(t["file_count"] > 0 for t in templates)


def test_schema_endpoint(client):
    name = client.get("/api/templates").json()["templates"][0]["name"]
    r = client.get(f"/api/templates/{name}/schema")
    assert r.status_code == 200
    data = r.json()
    assert data["steps"] and data["doc_files"]


@pytest.mark.parametrize("bad_name", [
    "../config.py",
    "..",
    "/etc",
    "..\\..\\config.py",
    "Thành lập mới công ty TNHH 1 TV/../../",
])
def test_generate_rejects_path_traversal(client, bad_name):
    r = client.post("/api/documents/generate", json={"template_name": bad_name, "data": {}})
    assert r.status_code == 400


def test_generate_unknown_template(client):
    r = client.post("/api/documents/generate", json={"template_name": "khong_ton_tai", "data": {}})
    assert r.status_code == 400


@pytest.mark.parametrize("bad_name", ["..%2F..%2Fconfig.py", "%2e%2e"])
def test_schema_rejects_path_traversal(client, bad_name):
    assert client.get(f"/api/templates/{bad_name}/schema").status_code == 404


def test_user_data_is_not_executed_as_template(client):
    """Dữ liệu người dùng chứa cú pháp Jinja phải được in nguyên văn, không được thực thi."""
    payload = {
        "template_name": "Tạm dừng công ty TNHH 1 TV",
        "data": {"ten_cong_ty_vn": "CÔNG TY A&B <X> {{ 7*7 }} {% if 1 %}LỘ{% endif %}", "ma_so_thue": "0101"},
    }
    r = client.post("/api/documents/generate", json=payload)
    assert r.status_code == 200
    texts = [t for n, t in read_zip(r.content).items() if n.endswith(".docx")]
    joined = "\n".join(texts)
    assert "{{ 7*7 }}" in joined
    assert "A&B <X>" in joined
    assert "CÔNG TY A&B <X> 49" not in joined


def test_cors_rejects_foreign_origin(client):
    r = client.options("/api/documents/generate", headers={
        "Origin": "https://evil.example.com",
        "Access-Control-Request-Method": "POST",
    })
    assert r.headers.get("access-control-allow-origin") != "https://evil.example.com"
    assert r.headers.get("access-control-allow-origin") != "*" or r.headers.get("access-control-allow-credentials") != "true"


def test_cors_allows_local_origin(client):
    from config import PORT
    origin = f"http://localhost:{PORT}"
    r = client.options("/api/documents/generate", headers={
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
    })
    assert r.headers.get("access-control-allow-origin") == origin


def test_cors_origins_parsing():
    from config import _parse_origins
    assert _parse_origins(" https://a.vn/ , https://b.vn ,,") == ["https://a.vn", "https://b.vn"]
    assert _parse_origins("") == []
