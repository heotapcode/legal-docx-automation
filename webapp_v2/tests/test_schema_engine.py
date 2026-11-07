"""Lõi schema v2: bản Python (services/schema_engine.py) và bản JS (static/js/engine/schema_engine.js)
phải cho cùng kết quả trên cùng bộ ca kiểm thử tests/engine_cases.json."""
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

from services import schema_engine as py

HERE = Path(__file__).resolve().parent
CASES = json.loads((HERE / "engine_cases.json").read_text(encoding="utf-8"))
JS_ENGINE = HERE.parent / "static" / "js" / "engine" / "schema_engine.js"

# Chạy toàn bộ ca kiểm thử bằng bản JS trong Node.js, in kết quả dạng JSON
NODE_RUNNER = r"""
const E = require(process.argv[1]);
const cases = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const pd = v => { const d = E.parseDate(v); return d ? `${d.y}-${String(d.m).padStart(2,'0')}-${String(d.d).padStart(2,'0')}` : null; };
process.stdout.write(JSON.stringify({
  to_number: cases.to_number.map(([v]) => E.toNumber(v)),
  parse_date: cases.parse_date.map(([v]) => pd(v)),
  conditions: cases.conditions.map(([c, d]) => E.evalCondition(c, d)),
  validate: cases.validate.map(c => E.validate(c.schema, c.data, c.today).map(e => [e.key, e.code, e.index === undefined ? -1 : e.index])),
  lists: cases.validate.map(c => E.validate(c.schema, c.data, c.today).map(e => e.list || null)),
}));
"""


def norm_errors(errors):
    return [[e["key"], e["code"], e.get("index", -1)] for e in errors]


@pytest.fixture(scope="module")
def js_results():
    node = shutil.which("node")
    if not node:
        pytest.skip("Không có Node.js để chạy bản JS")
    out = subprocess.run([node, "-e", NODE_RUNNER, str(JS_ENGINE), str(HERE / "engine_cases.json")],
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


@pytest.mark.parametrize("i", range(len(CASES["to_number"])))
def test_to_number(i, js_results):
    value, expected = CASES["to_number"][i]
    assert py.to_number(value) == expected
    assert js_results["to_number"][i] == expected


@pytest.mark.parametrize("i", range(len(CASES["parse_date"])))
def test_parse_date(i, js_results):
    value, expected = CASES["parse_date"][i]
    d = py.parse_date(value)
    assert (d.isoformat() if d else None) == expected
    assert js_results["parse_date"][i] == expected


@pytest.mark.parametrize("i", range(len(CASES["conditions"])))
def test_conditions(i, js_results):
    cond, data, expected = CASES["conditions"][i]
    assert py.eval_condition(cond, data) is expected
    assert js_results["conditions"][i] is expected


@pytest.mark.parametrize("i", range(len(CASES["validate"])), ids=[c["name"] for c in CASES["validate"]])
def test_validate(i, js_results):
    case = CASES["validate"][i]
    today = date.fromisoformat(case["today"])
    assert norm_errors(py.validate(case["schema"], case["data"], today)) == case["errors"]
    assert js_results["validate"][i] == case["errors"]


def test_error_messages_are_vietnamese():
    errors = py.validate(CASES["validate"][1]["schema"], CASES["validate"][1]["data"], date(2026, 11, 6))
    assert any("bắt buộc nhập" in e["message"] for e in errors)
    assert any("ít nhất 2" in e["message"] for e in errors)


@pytest.mark.parametrize("name", __import__("conftest").list_template_names())
def test_real_schemas_accept_sample_data(name):
    """Dữ liệu mẫu hợp lệ của mọi bộ mẫu thật không bị lõi mới báo lỗi kiểu/định dạng."""
    from conftest import build_payload, load_schema

    payload, _, _ = build_payload(name, 3)
    data = dict(payload["data"], dkkd_selected=payload["data"].get("dkkd_selected", []))
    assert py.validate(load_schema(name), data) == []


@pytest.mark.parametrize("name", __import__("conftest").list_template_names())
def test_real_schemas_reject_empty_form(name):
    """Form trống phải bị báo thiếu, đúng như wizard hiện tại đang chặn."""
    from conftest import load_schema

    assert py.validate(load_schema(name), {}), "Bộ mẫu không có trường bắt buộc nào?"


def test_resolve_refs_replaces_index_with_item_copy():
    schema = CASES["validate"][-1]["schema"]
    tv_cu = [{"ho_ten": "A"}, {"ho_ten": "B"}]
    data = {"tv_cu": tv_cu, "thanh_vien": [{"ho_ten": "C"}],
            "chuyen_nhuong": [{"ben_a": "1", "ben_b": 0, "gia_tri_so": "5"}, {"ben_a": "9", "ben_b": "x"}]}
    out = py.resolve_refs(schema, data)
    assert out["chuyen_nhuong"] == [{"ben_a": {"ho_ten": "B"}, "ben_b": {"ho_ten": "C"}, "gia_tri_so": "5"},
                                    {"ben_a": {}, "ben_b": {}}]
    out["chuyen_nhuong"][0]["ben_a"]["ho_ten"] = "Z"
    assert tv_cu[1]["ho_ten"] == "B" and data["chuyen_nhuong"][0]["ben_a"] == "1", "Không được sửa dữ liệu gốc"


@pytest.mark.parametrize("i", range(len(CASES["validate"])), ids=[c["name"] for c in CASES["validate"]])
def test_errors_name_their_list(i, js_results):
    """Lỗi của phần tử danh sách ghi kèm khóa danh sách (để trỏ đúng ô khi hai danh sách có cùng tên ô)."""
    case = CASES["validate"][i]
    errors = py.validate(case["schema"], case["data"], date.fromisoformat(case["today"]))
    lists = [e.get("list") for e in errors]
    assert js_results["lists"][i] == lists
    assert all((lst is not None) == ("index" in e) for e, lst in zip(errors, lists))
