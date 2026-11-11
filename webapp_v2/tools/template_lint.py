"""Công cụ quét bộ mẫu hồ sơ (file Word + _schema.json) và báo lỗi trước khi đưa vào sử dụng.

Chạy từ thư mục webapp_v2:
    python -m tools.template_lint                      # quét mọi bộ mẫu
    python -m tools.template_lint tang-von-cong-ty-tnhh-2-tv "templates/Tạm dừng công ty TNHH 1 TV"
    python -m tools.template_lint --json               # xuất JSON (cho CI / trang quản trị)
    python -m tools.template_lint --strict             # coi cảnh báo là lỗi

Mã kiểm tra:
    E001  Thiếu hoặc hỏng _schema.json
    E002  _schema.json sai đặc tả (schemas/template-schema.json)
    E003  Khối "documents" không khớp các file .docx thật (thiếu, thừa hoặc trùng)
    E004  Lối tắt "shortcut" trỏ tới bộ mẫu không có, hoặc preset sai key/giá trị của bộ đích
    E010  Cú pháp Jinja trong file Word bị lỗi (docxtpl không render được)
    E011  Dấu {{ }} / {% %} không cân trong một đoạn văn (thường do gõ sai hoặc tag bị tách đoạn)
    W020  Còn placeholder kiểu cũ [TEN_BIEN] chưa chuyển sang {{ ten_bien }}
    W021  Biến trong mẫu không có nguồn dữ liệu -> luôn in ra trống
    I022  Biến chỉ được tạo bởi quy tắc riêng trong render_service (tùy dữ liệu đầu vào)
    W030  Dữ liệu cụ thể bị viết cứng trong mẫu (email, số điện thoại, số CCCD, tên công ty)
    W031  Còn file khóa tạm của Word (~$...)
    W032  Bộ mẫu không có file .docx nào
    W033  Còn kiểu person_list cũ (vẫn chạy, tự chuyển thành list); nên đổi sang list trong _schema.json

Mã thoát: 0 nếu không có lỗi (E), 1 nếu có lỗi (hoặc có cảnh báo khi dùng --strict).
"""
import argparse
import json
import re
import sys
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Set

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import docx  # noqa: E402
from docxtpl import DocxTemplate  # noqa: E402

from config import TEMPLATES_DIR  # noqa: E402

SCHEMA_SPEC_PATH = APP_DIR / "schemas" / "template-schema.json"
# Các file gán biến cho mẫu lúc chạy (ngoài dữ liệu nhập): quét để biết biến nào "có nguồn"
RUNTIME_SOURCE_PATHS = [APP_DIR / "services" / "render_service.py", APP_DIR / "services" / "document_rules.py"]

# Biến được tạo động trong vòng lặp của render_service (f-string), không quét được bằng tên cố định
DYNAMIC_VAR_PATTERNS = [
    re.compile(r"^ben_[ab]_\w+$"),        # Hợp đồng chuyển nhượng / Biên bản thanh lý: từng bên A/B
    re.compile(r"^tv\d+_\w+$"),           # tv1_, tv2_...: thành viên theo thứ tự
    re.compile(r"^tv_moi_\d+_\w+$"),      # thành viên mới theo thứ tự
]

OLD_PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z0-9_]{2,}\]")
JINJA_TAG_RE = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.S)
HARDCODED_PATTERNS = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
    ("số điện thoại", re.compile(r"(?<![\d.,])0\d{2,3}[.\s]?\d{3}[.\s]?\d{3,4}(?![\d.,])")),
    ("số CCCD", re.compile(r"(?<!\d)0\d{11}(?!\d)")),
    # Tên công ty cụ thể (dữ liệu khách hàng cũ), vd "CÔNG TY TNHH PHÁT TRIỂN ABC"; loại trừ tên loại hình ở dưới
    ("tên công ty", re.compile(r"(?i:công ty\s+(?:TNHH|cổ phần|CP))(?:\s+[A-ZĐÀ-Ỹ0-9&-]{2,}){2,}")),
]
# Cụm hợp lệ trong mẫu nhà nước, không phải tên công ty cụ thể
HARDCODED_ALLOW = re.compile(r"(MỘT|HAI) THÀNH VIÊN|TRỞ LÊN")


@dataclass
class Finding:
    level: str      # "error" | "warning" | "info"
    code: str
    template: str
    file: str
    message: str


# ---------- Tiện ích ----------

def _iter_paragraphs(document) -> Iterator:
    """Mọi đoạn văn: thân, bảng (kể cả bảng lồng), header, footer."""
    def from_container(container):
        for p in container.paragraphs:
            yield p
        for table in getattr(container, "tables", []):
            for row in table.rows:
                for cell in row.cells:
                    yield from from_container(cell)

    yield from from_container(document)
    for section in document.sections:
        for part in (section.header, section.footer):
            yield from from_container(part)


def _runtime_keys() -> Set[str]:
    """Tên biến được gán trực tiếp lúc chạy (raw_data['x'] = ..., sub_ctx["x"] = ..., sub[f"{pfx}x"] = ...)."""
    keys: Set[str] = set()
    for path in RUNTIME_SOURCE_PATHS:
        try:
            src = path.read_text(encoding="utf-8")
        except OSError:
            continue
        keys |= set(re.findall(r"(?:raw_data|sub_ctx|sub|ctx|context)\[['\"]([A-Za-z0-9_]+)['\"]\]\s*=", src))
        # sub[f"{pfx}ho_ten"] trong vòng "for pfx in ("tv2_", "tv_"):" -> tv2_ho_ten, tv_ho_ten
        for block in re.findall(r"for pfx in \(([^)]*)\):(.*?)(?:\n\S|\n    [a-z_]+ = )", src, re.S):
            prefixes = re.findall(r"['\"]([a-z0-9_]+)['\"]", block[0])
            for suffix in re.findall(r"\{pfx\}([a-z0-9_]+)", block[1]):
                keys |= {p + suffix for p in prefixes}
    return keys


def _load_spec() -> Optional[dict]:
    try:
        return json.loads(SCHEMA_SPEC_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _sample_context_keys(schema: dict, jinja_env) -> Set[str]:
    from services.render_service import normalize_context
    from services.sample_data import build_sample_payload

    payload, _, _ = build_sample_payload(schema, 3)
    data = dict(payload["data"])
    data.update({k: v for k, v in (payload.get("special_payload") or {}).items() if v})
    return set(normalize_context(data, payload["ma_nganh"])) | set(jinja_env.globals)


# ---------- Kiểm tra ----------

def lint_schema(tpl_dir: Path, spec: Optional[dict]) -> (Optional[dict], List[Finding]):
    name = tpl_dir.name
    path = tpl_dir / "_schema.json"
    if not path.exists():
        return None, [Finding("error", "E001", name, "_schema.json", "Thiếu file _schema.json")]
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        return None, [Finding("error", "E001", name, "_schema.json", f"JSON không hợp lệ: {e}")]

    findings: List[Finding] = []
    if spec is not None:
        try:
            import jsonschema
        except ImportError:
            jsonschema = None
        if jsonschema is not None:
            validator = jsonschema.Draft202012Validator(spec)
            for err in sorted(validator.iter_errors(schema), key=lambda e: list(e.absolute_path)):
                loc = "/".join(str(p) for p in err.absolute_path) or "(gốc)"
                findings.append(Finding("error", "E002", name, "_schema.json", f"{loc}: {err.message}"))
    for step in (schema.get("steps") or []) if isinstance(schema, dict) else []:
        for f in step.get("fields") or []:
            if isinstance(f, dict) and f.get("type") == "person_list":
                findings.append(Finding("warning", "W033", name, "_schema.json",
                                        f"Trường '{f.get('key')}' dùng kiểu person_list cũ; nên đổi sang list "
                                        "(xem docs/schema-v2.md)"))
    return schema, findings


def lint_docx(tpl_dir: Path, docx_path: Path, known: Set[str], runtime: Set[str], jinja_env) -> List[Finding]:
    name, fname = tpl_dir.name, docx_path.name
    findings: List[Finding] = []

    # E011, W020, W030: duyệt từng đoạn văn
    seen_hardcoded = set()
    for p in _iter_paragraphs(docx.Document(str(docx_path))):
        text = p.text
        if not text:
            continue
        for open_, close in (("{{", "}}"), ("{%", "%}")):
            if text.count(open_) != text.count(close):
                findings.append(Finding("error", "E011", name, fname,
                                        f"Dấu {open_} {close} không cân: «{text.strip()[:120]}»"))
        for m in OLD_PLACEHOLDER_RE.finditer(text):
            findings.append(Finding("warning", "W020", name, fname, f"Placeholder kiểu cũ {m.group(0)}"))
        static_text = JINJA_TAG_RE.sub(" ", text)
        for label, rx in HARDCODED_PATTERNS:
            for m in rx.finditer(static_text):
                if label == "tên công ty" and HARDCODED_ALLOW.search(m.group(0)):
                    continue
                if (label, m.group(0)) in seen_hardcoded:
                    continue
                seen_hardcoded.add((label, m.group(0)))
                findings.append(Finding("warning", "W030", name, fname,
                                        f"{label.capitalize()} viết cứng: {m.group(0)}"))

    # E010, W021, I022: biến Jinja
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            variables = DocxTemplate(str(docx_path)).get_undeclared_template_variables(jinja_env)
    except Exception as e:  # TemplateSyntaxError và lỗi XML
        findings.append(Finding("error", "E010", name, fname, f"Cú pháp Jinja lỗi: {e}"))
        return findings

    for var in sorted(variables):
        if var in known:
            continue
        if var in runtime or any(rx.match(var) for rx in DYNAMIC_VAR_PATTERNS):
            findings.append(Finding("info", "I022", name, fname,
                                    f"Biến '{var}' chỉ có khi quy tắc riêng trong render_service được kích hoạt"))
        else:
            findings.append(Finding("warning", "W021", name, fname,
                                    f"Biến '{var}' không có nguồn dữ liệu, sẽ luôn in ra trống"))
    return findings


def lint_template(tpl_dir: Path, spec: Optional[dict] = None, runtime: Optional[Set[str]] = None) -> List[Finding]:
    from services.render_service import create_jinja_env

    spec = _load_spec() if spec is None else spec
    runtime = _runtime_keys() if runtime is None else runtime
    jinja_env = create_jinja_env()

    schema, findings = lint_schema(tpl_dir, spec)
    docx_files = sorted(f for f in tpl_dir.glob("*.docx") if not f.name.startswith(("~$", "_")))
    for lock in sorted(tpl_dir.glob("~$*")):
        findings.append(Finding("warning", "W031", tpl_dir.name, lock.name, "File khóa tạm của Word, nên xóa"))
    if not docx_files:
        findings.append(Finding("warning", "W032", tpl_dir.name, "", "Không có file .docx nào"))
        return findings

    if schema is not None and schema.get("documents"):
        listed = [d.get("file") for d in schema["documents"]]
        actual = {f.name for f in docx_files}
        for f in sorted(actual - set(listed)):
            findings.append(Finding("error", "E003", tpl_dir.name, f, "File .docx chưa khai báo trong documents (sẽ không được sinh)"))
        for f in sorted(set(listed) - actual):
            findings.append(Finding("error", "E003", tpl_dir.name, str(f), "documents khai báo file không tồn tại"))
        for f in sorted({x for x in listed if listed.count(x) > 1}):
            findings.append(Finding("error", "E003", tpl_dir.name, str(f), "File được khai báo nhiều lần trong documents"))

    known: Set[str] = set(jinja_env.globals)
    if schema is not None and schema.get("steps"):
        try:
            known = _sample_context_keys(schema, jinja_env)
        except Exception as e:
            findings.append(Finding("error", "E001", tpl_dir.name, "_schema.json",
                                    f"Không dựng được dữ liệu mẫu từ schema: {e}"))
    if schema is not None and isinstance(schema.get("shortcut"), dict):
        findings.extend(lint_shortcut(tpl_dir, schema["shortcut"]))
    for f in docx_files:
        findings.extend(lint_docx(tpl_dir, f, known, runtime, jinja_env))
    return findings


def lint_shortcut(tpl_dir: Path, shortcut: dict) -> List[Finding]:
    """E004: lối tắt sang thủ tục gộp phải trỏ tới bộ mẫu có thật, preset đúng key và giá trị của bộ đích."""
    name = tpl_dir.name
    target = str(shortcut.get("template") or "")
    bad = lambda msg: Finding("error", "E004", name, "_schema.json", f"shortcut: {msg}")  # noqa: E731
    candidates = [tpl_dir.parent / target, TEMPLATES_DIR / target]
    target_schema_path = next((p / "_schema.json" for p in candidates
                               if target and Path(target).name == target and (p / "_schema.json").is_file()), None)
    if target_schema_path is None:
        return [bad(f"không tìm thấy bộ mẫu đích '{target}'")]
    try:
        target_schema = json.loads(target_schema_path.read_text(encoding="utf-8"))
    except ValueError:
        return [bad(f"_schema.json của bộ mẫu đích '{target}' hỏng")]
    fields = {f.get("key"): f for st in target_schema.get("steps") or [] for f in st.get("fields") or []}
    findings = []
    for key, value in (shortcut.get("preset") or {}).items():
        field = fields.get(key)
        if field is None:
            findings.append(bad(f"bộ mẫu đích không có trường '{key}'"))
            continue
        allowed = {o.get("value") for o in field.get("options") or []}
        if field.get("type") == "checkbox_group":
            values = value if isinstance(value, list) else [value]
        elif field.get("type") == "select":
            values = [value]
        else:
            continue
        for v in values:
            if allowed and v not in allowed:
                findings.append(bad(f"giá trị '{v}' không có trong lựa chọn của '{key}'"))
    persons = [k for k, f in fields.items() if f.get("type") == "person"]
    for src, dst in (shortcut.get("map") or {}).items():
        if dst not in fields and not any(dst.startswith(p + "_") for p in persons):
            findings.append(bad(f"map '{src}' -> '{dst}': bộ mẫu đích không có trường '{dst}'"))
    return findings


# ---------- Dòng lệnh ----------

def resolve_targets(targets: Iterable[str]) -> List[Path]:
    from services.render_service import template_id_index

    targets = list(targets)
    if not targets:
        return sorted(d for d in TEMPLATES_DIR.iterdir() if d.is_dir())
    index = template_id_index()
    out = []
    for t in targets:
        p = Path(t)
        if p.is_dir():
            out.append(p)
        elif t in index:
            out.append(index[t])
        elif (TEMPLATES_DIR / t).is_dir():
            out.append(TEMPLATES_DIR / t)
        else:
            raise SystemExit(f"Không tìm thấy bộ mẫu: {t}")
    return out


def summarize(findings: List[Finding]) -> Dict[str, int]:
    return {lvl: sum(1 for f in findings if f.level == lvl) for lvl in ("error", "warning", "info")}


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Quét bộ mẫu hồ sơ (docx + _schema.json)")
    ap.add_argument("targets", nargs="*", help="id bộ mẫu, tên thư mục trong templates/, hoặc đường dẫn thư mục")
    ap.add_argument("--json", action="store_true", help="xuất kết quả dạng JSON")
    ap.add_argument("--strict", action="store_true", help="coi cảnh báo (W) là lỗi")
    ap.add_argument("--info", action="store_true", help="hiện cả mục thông tin (I)")
    args = ap.parse_args(argv)

    spec, runtime = _load_spec(), _runtime_keys()
    findings: List[Finding] = []
    dirs = resolve_targets(args.targets)
    for d in dirs:
        findings.extend(lint_template(d, spec, runtime))
    counts = summarize(findings)

    if args.json:
        print(json.dumps({"summary": counts, "findings": [asdict(f) for f in findings]}, ensure_ascii=False, indent=2))
    else:
        icon = {"error": "✖", "warning": "⚠", "info": "ℹ"}
        current = None
        for f in findings:
            if f.level == "info" and not args.info:
                continue
            if f.template != current:
                current = f.template
                print(f"\n{current}")
            loc = f" [{f.file}]" if f.file else ""
            print(f"  {icon[f.level]} {f.code}{loc} {f.message}")
        print(f"\nĐã quét {len(dirs)} bộ mẫu: {counts['error']} lỗi, {counts['warning']} cảnh báo, {counts['info']} thông tin")

    failed = counts["error"] > 0 or (args.strict and counts["warning"] > 0)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
