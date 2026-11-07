"""Kiểm tra cấu trúc mọi _schema.json: frontend (wizard.js) chỉ hiểu định dạng "steps".

Schema dạng phẳng ("fields": [...]) hay kiểu trường lạ sẽ khiến wizard không hiện ô nhập nào.
"""
import json
import re
from pathlib import Path

import pytest

from conftest import list_template_names, load_schema
from config import TEMPLATES_DIR

SPEC_PATH = Path(__file__).resolve().parent.parent / "schemas" / "template-schema.json"

# Các kiểu trường mà renderField() trong static/js/pages/wizard.js HIỆN hỗ trợ.
# Đặc tả (schemas/template-schema.json) còn định nghĩa thêm kiểu [v2] cho bộ máy wizard mới;
# chừng nào wizard chưa vẽ được thì bộ mẫu thật chưa được dùng các kiểu đó.
SUPPORTED_TYPES = {"text", "mst_lookup", "money", "phone", "email", "number", "select",
                   "person", "person_list", "transfer_list", "checkbox_group",
                   "date", "cccd", "percent", "address", "list"}  # dòng cuối: bộ vẽ form chung (Mục 9 bước 4)

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


@pytest.fixture(scope="module")
def spec_validator():
    jsonschema = pytest.importorskip("jsonschema")
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(spec)
    return jsonschema.Draft202012Validator(spec)


@pytest.mark.parametrize("name", TEMPLATES)
def test_schema_matches_spec(name, spec_validator):
    errors = [f"{'/'.join(map(str, e.absolute_path)) or '(gốc)'}: {e.message}"
              for e in spec_validator.iter_errors(load_schema(name))]
    assert not errors, "\n".join(errors)


def test_template_ids_unique_and_resolvable():
    from services.render_service import template_id_index

    ids = [load_schema(n)["id"] for n in TEMPLATES]
    assert len(ids) == len(set(ids)), "Trùng id bộ mẫu"
    index = template_id_index()
    for name in TEMPLATES:
        assert index[load_schema(name)["id"]].name == name


@pytest.mark.parametrize("name", TEMPLATES)
def test_documents_block_matches_files(name):
    """Khối documents liệt kê đủ và đúng các file .docx; tên quy tắc phải có trong document_rules."""
    from services.document_rules import HOOKS, REPEATERS

    docs = load_schema(name).get("documents")
    assert docs, "Thiếu khối documents"
    listed = [d["file"] for d in docs]
    actual = sorted(f.name for f in (TEMPLATES_DIR / name).glob("*.docx") if not f.name.startswith(("~$", "_")))
    assert len(listed) == len(set(listed)), "Một file được khai báo nhiều lần"
    assert sorted(listed) == actual, f"Thiếu: {sorted(set(actual) - set(listed))}; thừa: {sorted(set(listed) - set(actual))}"
    for d in docs:
        if "repeat_with" in d:
            assert d["repeat_with"] in REPEATERS
        for hook in d.get("post", []):
            assert hook in HOOKS


def test_spec_rule_names_match_code():
    from services.document_rules import HOOKS, PREPARERS, REPEATERS

    full = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    spec = full["$defs"]["document"]["properties"]
    assert sorted(spec["repeat_with"]["enum"]) == sorted(REPEATERS)
    assert sorted(spec["post"]["items"]["enum"]) == sorted(HOOKS)
    assert sorted(full["properties"]["prepare"]["enum"]) == sorted(PREPARERS)
