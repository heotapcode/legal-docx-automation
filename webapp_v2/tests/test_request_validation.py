"""API /api/documents/generate kiểm tra dữ liệu theo _schema.json (services/schema_engine.py)."""
import pytest

from conftest import build_payload, list_template_names

CHECKED = list_template_names()  # mọi bộ mẫu đều được kiểm tra (không còn wizard riêng nào bỏ qua)


def post(client, name, data):
    return client.post("/api/documents/generate", json={"template_name": name, "data": data})


@pytest.mark.parametrize("name", CHECKED)
def test_empty_form_is_rejected_with_details(client, name):
    r = post(client, name, {})
    assert r.status_code == 422
    body = r.json()
    assert body["detail"].startswith("Dữ liệu chưa hợp lệ:")
    assert body["errors"] and all({"key", "code", "message"} <= set(e) for e in body["errors"])


def test_too_few_members_is_rejected(client):
    payload, _, _ = build_payload("Thành lập mới công ty Cổ Phần", 3)
    payload["data"]["thanh_vien"] = payload["data"]["thanh_vien"][:2]
    r = post(client, payload["template_name"], payload["data"])
    assert r.status_code == 422
    assert any(e["code"] == "min_items" and e["key"] == "thanh_vien" for e in r.json()["errors"])


def test_member_without_name_is_rejected(client):
    payload, _, _ = build_payload("Thành lập mới công ty TNHH 2 TV", 2)
    payload["data"]["thanh_vien"][1]["ho_ten"] = "  "
    r = post(client, payload["template_name"], payload["data"])
    assert r.status_code == 422
    assert {"key": "ho_ten", "code": "required", "index": 1}.items() <= next(
        e for e in r.json()["errors"] if e["key"] == "ho_ten").items()


def test_province_default_satisfies_required(client):
    """Ô tỉnh/thành phố bắt buộc nhưng có mặc định: bỏ trống vẫn hợp lệ (dùng Hà Nội)."""
    payload, _, _ = build_payload("Tạm dừng công ty TNHH 1 TV", 1)
    payload["data"].pop("tinh_dang_ky", None)
    assert post(client, payload["template_name"], payload["data"]).status_code == 200
