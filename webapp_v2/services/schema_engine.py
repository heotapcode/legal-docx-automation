"""Lõi đọc _schema.json v2 phía backend: điều kiện hiển thị và kiểm tra dữ liệu.

Hành vi PHẢI giống hệt static/js/engine/schema_engine.js (frontend). Cả hai bản chạy cùng bộ ca
kiểm thử tests/engine_cases.json (tests/test_schema_engine.py), nên sửa một bên thì sửa cả bên kia.

Đặc tả: docs/schema-v2.md (mục 3.2 validate, 3.3 rules, 4 điều kiện).
"""
import re
from datetime import date
from typing import Any, Dict, Iterable, List, Optional

LIST_TYPES = {"list", "person_list", "transfer_list"}


# ---------- Giá trị ----------

def is_blank(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, (list, tuple, dict)):
        return len(v) == 0
    return str(v).strip() == ""


def to_number(v: Any) -> Optional[float]:
    """'1,000,000' / '1.000.000' / '33.33' / 5 -> số; không đọc được -> None.

    Dấu '.' hoặc ',' theo sau đúng 3 chữ số được coi là phân cách hàng nghìn; còn lại là dấu thập phân.
    """
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(" ", "")
    if not s:
        return None
    neg = s.startswith("-")
    s = s.lstrip("+-")
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", s):
        s = re.sub(r"[.,]", "", s)
    else:
        s = s.replace(",", ".")
    # Cùng cú pháp với bản JS (không nhận "1_000", "inf", "nan"...)
    if not re.fullmatch(r"(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?", s):
        return None
    n = float(s)
    return -n if neg else n


def parse_date(v: Any) -> Optional[date]:
    """'DD/MM/YYYY' hoặc 'YYYY-MM-DD' (năm đủ 4 chữ số); ngày không hợp lệ -> None."""
    s = str(v if v is not None else "").strip()
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        d, mo, y = map(int, m.groups())
    else:
        m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
        if not m:
            return None
        y, mo, d = map(int, m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None


# ---------- Điều kiện ----------

def eval_condition(cond: Optional[dict], data: Dict[str, Any]) -> bool:
    """Điều kiện rỗng/None -> True. Xem docs/schema-v2.md mục 4."""
    if not cond:
        return True
    if "all" in cond:
        return all(eval_condition(c, data) for c in cond["all"])
    if "any" in cond:
        return any(eval_condition(c, data) for c in cond["any"])
    value = data.get(cond.get("field"))
    if "equals" in cond and value != cond["equals"]:
        return False
    if "not_equals" in cond and value == cond["not_equals"]:
        return False
    if "contains" in cond:
        if not isinstance(value, (list, tuple)) or cond["contains"] not in value:
            return False
    if "in" in cond and value not in cond["in"]:
        return False
    if "not_empty" in cond and (not is_blank(value)) != bool(cond["not_empty"]):
        return False
    return True


def visible_steps(schema: dict, data: Dict[str, Any]) -> List[dict]:
    return [s for s in schema.get("steps", []) if eval_condition(s.get("show_if"), data)]


def visible_fields(schema: dict, data: Dict[str, Any]) -> Iterable[dict]:
    for step in visible_steps(schema, data):
        for f in step.get("fields", []):
            if eval_condition(f.get("show_if"), data):
                yield f


# ---------- Kiểm tra dữ liệu ----------

def _err(errors, key, label, code, message, index=None):
    e = {"key": key, "label": label, "code": code, "message": message}
    if index is not None:
        e["index"] = index
    errors.append(e)


def _check_value(field: dict, value: Any, scope: Dict[str, Any], errors: list, today: date, index=None, prefix=""):
    key, label = field["key"], prefix + field.get("label", field["key"])
    if is_blank(value) and "default" in field:
        value = field["default"]  # bỏ trống -> dùng giá trị mặc định (vd tỉnh/thành phố = Hà Nội)
    if is_blank(value):
        if field.get("required") and field.get("type") != "checkbox_group":
            _err(errors, key, label, "required", f"{label}: bắt buộc nhập", index)
        elif field.get("required"):
            _err(errors, key, label, "required", f"{label}: chọn ít nhất 1 mục", index)
        return
    rules = field.get("validate") or {}
    msg = rules.get("message")
    if field.get("type") == "cccd" and "pattern" not in rules and not re.fullmatch(r"\d{12}", str(value).strip()):
        _err(errors, key, label, "pattern", msg or f"{label}: số CCCD phải gồm 12 chữ số", index)
    if "pattern" in rules and not re.fullmatch(rules["pattern"], str(value).strip()):
        _err(errors, key, label, "pattern", msg or f"{label}: không đúng định dạng", index)
    num = to_number(value)
    if "min" in rules and (num is None or num < rules["min"]):
        _err(errors, key, label, "min", msg or f"{label}: tối thiểu {rules['min']:g}", index)
    if "max" in rules and (num is None or num > rules["max"]):
        _err(errors, key, label, "max", msg or f"{label}: tối đa {rules['max']:g}", index)
    for code, op in (("greater_than", lambda a, b: a > b), ("less_than", lambda a, b: a < b)):
        if code in rules:
            other = to_number(scope.get(rules[code]))
            if num is not None and other is not None and not op(num, other):
                word = "lớn hơn" if code == "greater_than" else "nhỏ hơn"
                _err(errors, key, label, code, msg or f"{label}: phải {word} {rules[code]}", index)
    if "min_age" in rules:
        d = parse_date(value)
        age = None if d is None else today.year - d.year - ((today.month, today.day) < (d.month, d.day))
        if age is None or age < rules["min_age"]:
            _err(errors, key, label, "min_age", msg or f"{label}: chưa đủ {rules['min_age']} tuổi", index)


def _check_list(field: dict, items: Any, root: Dict[str, Any], errors: list, today: date):
    key, label = field["key"], field.get("label", field["key"])
    items = items if isinstance(items, list) else []
    lo = field.get("min", 1 if field.get("required") else 0)
    subs = field.get("item", []) + field.get("extra_fields", [])
    if field.get("type") == "person_list" and not any(sub["key"] == "ho_ten" for sub in subs):
        subs = [{"key": "ho_ten", "label": "Họ và tên", "type": "text", "required": True}] + subs
    if len(items) < lo:
        _err(errors, key, label, "min_items", f"{label}: cần ít nhất {lo} (hiện có {len(items)})")
    if "max" in field and len(items) > field["max"]:
        _err(errors, key, label, "max_items", f"{label}: tối đa {field['max']} (hiện có {len(items)})")
    for i, item in enumerate(items):
        item = item if isinstance(item, dict) else {}
        if field.get("type") == "transfer_list":
            # Kiểu cũ: mỗi giao dịch {ben_a: {...}, ben_b: {...}, gia_tri_so}
            for path, sub_label in (("ben_a.ho_ten", "Họ tên bên chuyển nhượng"), ("ben_b.ho_ten", "Họ tên bên nhận"),
                                    ("gia_tri_so", "Giá trị chuyển nhượng")):
                head, _, tail = path.partition(".")
                v = item.get(head)
                if tail:
                    v = v.get(tail) if isinstance(v, dict) else None
                _check_value({"key": path, "label": sub_label, "required": True}, v, item, errors, today,
                             index=i, prefix=f"Giao dịch #{i + 1}: ")
        for sub in subs:
            if eval_condition(sub.get("show_if"), item):
                _check_value(sub, item.get(sub["key"]), item, errors, today, index=i, prefix=f"{label} #{i + 1}: ")
    for rule in field.get("rules", []):
        if "sum" in rule:
            total = sum(to_number(it.get(rule["sum"])) or 0 for it in items if isinstance(it, dict))
            target = rule["equals"]
            # equals là số, hoặc tên một trường ở cấp gốc (vd "von_dieu_le_so")
            target_n = to_number(root.get(target)) if isinstance(target, str) and target in root else to_number(target)
            if target_n is not None and abs(total - target_n) > 1e-6:
                _err(errors, key, label, "sum",
                     rule.get("message") or f"{label}: tổng {rule['sum']} phải bằng {target_n:g} (hiện {total:g})")
        if "unique" in rule:
            seen = {}
            for i, it in enumerate(items):
                v = (it or {}).get(rule["unique"]) if isinstance(it, dict) else None
                if is_blank(v):
                    continue
                v = str(v).strip()
                if v in seen:
                    _err(errors, key, label, "unique",
                         rule.get("message") or f"{label}: {rule['unique']} bị trùng (#{seen[v] + 1} và #{i + 1})", index=i)
                else:
                    seen[v] = i


def validate(schema: dict, data: Dict[str, Any], today: Optional[date] = None) -> List[dict]:
    """Danh sách lỗi [{key, label, code, message, index?}] cho các trường đang hiển thị."""
    today = today or date.today()
    errors: List[dict] = []
    for f in visible_fields(schema, data):
        if f.get("type") in LIST_TYPES:
            _check_list(f, data.get(f["key"]), data, errors, today)
        elif f.get("type") == "person":
            # Kiểu cũ: dữ liệu phẳng <key>_ho_ten, <key>_so_cccd...
            if f.get("required"):
                for suffix, sub_label in (("_ho_ten", "Họ và tên"), ("_so_cccd", "Số CCCD")):
                    _check_value({"key": f["key"] + suffix, "label": f"{f.get('label', f['key'])}: {sub_label}",
                                  "required": True}, data.get(f["key"] + suffix), data, errors, today)
        else:
            _check_value(f, data.get(f["key"]), data, errors, today)
    return errors
