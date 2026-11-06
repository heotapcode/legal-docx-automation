"""Ô chọn tỉnh/thành phố nơi đăng ký (tinh_dang_ky): danh mục, API, và địa danh trong hồ sơ."""
import re
import warnings

import pytest
from docxtpl import DocxTemplate

from conftest import build_payload, list_template_names, load_schema, read_zip
from config import TEMPLATES_DIR
from services.dia_ban import context_values, list_tinh_thanh

LOCALITY_VARS = {"noi_lap", "tinh_thanh_dkkd", "phong_dkkd"}


def template_vars(name):
    from services.render_service import create_jinja_env

    env = create_jinja_env()
    out = set()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for f in (TEMPLATES_DIR / name).glob("*.docx"):
            if not f.name.startswith(("~$", "_")):
                out |= DocxTemplate(str(f)).get_undeclared_template_variables(env)
    return out


LOCALIZED = [n for n in list_template_names() if template_vars(n) & LOCALITY_VARS]


def test_catalog_has_34_units():
    items = list_tinh_thanh()
    assert len(items) == 34
    assert len({i["value"] for i in items}) == 34
    assert sum(i["loai"] == "thành phố" for i in items) == 6
    assert {"Hà Nội", "Hồ Chí Minh", "Bắc Ninh", "Huế"} <= {i["value"] for i in items}
    # Tỉnh cũ đã sáp nhập từ 01/07/2025 không còn trong danh mục
    assert not {"Bắc Giang", "Hà Nam", "Bình Dương"} & {i["value"] for i in items}


@pytest.mark.parametrize("value, phong", [
    ("Hà Nội", "Phòng Đăng ký kinh doanh và tài chính doanh nghiệp thành phố Hà Nội"),
    ("Bắc Ninh", "Phòng Đăng ký kinh doanh tỉnh Bắc Ninh"),
    ("Đà Nẵng", "Phòng Đăng ký kinh doanh thành phố Đà Nẵng"),
])
def test_phong_dkkd(value, phong):
    assert context_values(value)["phong_dkkd"] == phong


@pytest.mark.parametrize("value, noi_lap, dkkd", [
    (None, "Hà Nội", "thành phố Hà Nội"),
    ("", "Hà Nội", "thành phố Hà Nội"),
    ("Bắc Ninh", "Bắc Ninh", "tỉnh Bắc Ninh"),
    ("tỉnh bắc ninh", "Bắc Ninh", "tỉnh Bắc Ninh"),
    ("Hồ Chí Minh", "TP. Hồ Chí Minh", "thành phố Hồ Chí Minh"),
    ("TP. Hồ Chí Minh", "TP. Hồ Chí Minh", "thành phố Hồ Chí Minh"),
    ("Thành phố Huế", "Huế", "thành phố Huế"),
])
def test_context_values(value, noi_lap, dkkd):
    ctx = context_values(value)
    assert (ctx["noi_lap"], ctx["tinh_thanh_dkkd"]) == (noi_lap, dkkd)


def test_unknown_province_is_rejected_not_defaulted():
    with pytest.raises(ValueError, match="Bắc Giang"):
        context_values("Bắc Giang")


def test_api_lists_provinces(client):
    data = client.get("/api/dia-ban/tinh-thanh").json()
    assert data["mac_dinh"] == "Hà Nội"
    assert len(data["tinh_thanh"]) == 34
    hn = next(t for t in data["tinh_thanh"] if t["value"] == "Hà Nội")
    assert hn["label"] == "Thành phố Hà Nội"


def test_generate_rejects_unknown_province(client):
    payload, _, _ = build_payload("Tạm dừng công ty TNHH 1 TV", 1)
    payload["data"]["tinh_dang_ky"] = "Bắc Giang"
    r = client.post("/api/documents/generate", json=payload)
    assert r.status_code == 400
    assert "Bắc Giang" in r.json()["detail"]


def test_localized_templates_found():
    assert len(LOCALIZED) >= 20


@pytest.mark.parametrize("name", LOCALIZED)
def test_schema_offers_province_select(name):
    fields = {f["key"]: f for st in load_schema(name)["steps"] for f in st["fields"]}
    f = fields.get("tinh_dang_ky")
    assert f, "Mẫu dùng {{ noi_lap }}/{{ tinh_thanh_dkkd }} nhưng form không có ô chọn tỉnh/thành phố"
    assert f["type"] == "select" and f["options_source"] == "tinh_thanh" and f["default"] == "Hà Nội"


@pytest.mark.parametrize("name", LOCALIZED)
def test_documents_follow_selected_province(client, name):
    payload, _, _ = build_payload(name, 2)
    payload["data"]["tinh_dang_ky"] = "Bắc Ninh"
    r = client.post("/api/documents/generate", json=payload)
    assert r.status_code == 200, r.text
    text = "\n".join(v for k, v in read_zip(r.content).items() if k.endswith(".docx"))

    used = template_vars(name)
    if "noi_lap" in used:
        assert re.search(r"Bắc Ninh\s*,", text), "Dòng nơi lập văn bản không theo tỉnh đã chọn"
    if "tinh_thanh_dkkd" in used:
        assert "tỉnh Bắc Ninh" in text, "Tên cơ quan đăng ký không theo tỉnh đã chọn"
    if "phong_dkkd" in used:
        assert "Phòng Đăng ký kinh doanh tỉnh Bắc Ninh" in text
        # Cụm "và tài chính doanh nghiệp" chỉ có ở Hà Nội
        assert "tài chính doanh nghiệp tỉnh" not in text
    assert "Sở Kế hoạch và Đầu tư" not in text
    # Không còn địa danh Hà Nội ở dòng ngày hay cơ quan đăng ký
    assert not re.search(r"Hà\s*[Nn]ội\s*,\s*ngày", text)
    assert not re.search(r"(?:[Kk]inh doanh|ĐKKD|tài chính doanh nghiệp|Đầu tư)\s+(?:[Tt]hành phố |TP\.? )?Hà Nội", text)
