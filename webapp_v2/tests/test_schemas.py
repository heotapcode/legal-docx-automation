"""Kiểm tra cấu trúc mọi _schema.json: frontend (wizard.js) chỉ hiểu định dạng "steps".

Schema dạng phẳng ("fields": [...]) hay kiểu trường lạ sẽ khiến wizard không hiện ô nhập nào.
"""
import re

import pytest

from conftest import list_template_names, load_schema
from config import TEMPLATES_DIR

# Các kiểu trường mà renderField() trong static/js/pages/wizard.js hỗ trợ
SUPPORTED_TYPES = {"text", "mst_lookup", "money", "phone", "email", "number",
                   "person", "person_list", "transfer_list", "checkbox_group"}

TEMPLATES = list_template_names()


@pytest.mark.parametrize("name", TEMPLATES)
def test_schema_structure(name):
    s = load_schema(name)
    assert s.get("name") == name, "Trường 'name' phải trùng tên thư mục"
    assert s.get("display_name")
    assert isinstance(s.get("has_nganh", False), bool)
    assert "fields" not in s, "Dùng định dạng 'steps', không dùng 'fields' phẳng (xem scripts_and_tools/migrate_flat_schemas.py)"
    steps = s.get("steps")
    assert steps, "Schema phải có ít nhất một bước trong 'steps'"

    keys = []
    for step in steps:
        assert step.get("title"), f"Bước {step.get('id')} thiếu 'title'"
        assert step.get("fields"), f"Bước {step.get('id')} không có trường nào"
        for f in step["fields"]:
            assert f.get("key") and f.get("label"), f
            assert f["type"] in SUPPORTED_TYPES, f"Kiểu trường không hỗ trợ: {f}"
            keys.append(f["key"])
            for ef in f.get("extra_fields", []):
                assert ef["type"] in SUPPORTED_TYPES, f"Kiểu trường không hỗ trợ: {ef}"
    dup = {k for k in keys if keys.count(k) > 1}
    assert not dup, f"Trùng key: {dup}"


@pytest.mark.parametrize("name", TEMPLATES)
def test_has_nganh_matches_templates(name):
    """Bộ mẫu có bảng 'Mã ngành / Tên ngành' thì schema nên bật has_nganh để người dùng chọn ngành."""
    import docx

    has_table = False
    for f in (TEMPLATES_DIR / name).glob("*.docx"):
        if f.name.startswith(("~$", "_")):
            continue
        for t in docx.Document(str(f)).tables:
            if t.rows:
                head = " ".join(c.text.upper() for c in t.rows[0].cells)
                if "MÃ NGÀNH" in head and "TÊN NGÀNH" in head:
                    has_table = True
    if has_table:
        assert load_schema(name).get("has_nganh"), "Có bảng mã ngành nhưng has_nganh=false"
