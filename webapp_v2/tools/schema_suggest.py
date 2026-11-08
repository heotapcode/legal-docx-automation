"""Gợi ý trường cho _schema.json từ tên biến trong mẫu Word (Mục 10.3).

Biến "chưa có nguồn" là biến có trong file .docx mà dữ liệu nhập (theo schema) và quy tắc lúc chạy đều không
cung cấp — đúng tập công cụ quét báo W021. Mỗi biến được đoán kiểu theo tên:

    <x>_ho_ten, <x>_so_cccd, <x>_ngay_sinh, <x>_gioi_tinh, <x>_dia_chi_*  -> một trường kiểu person "<x>"
    ...so_cccd / cccd                                                     -> cccd
    ngay_... / ..._ngay / ..._ngay_sinh ...                              -> date
    ma_so_thue / mst                                                      -> mst_lookup
    sdt / dien_thoai                                                      -> phone
    email                                                                 -> email
    ty_le                                                                 -> percent
    (von|tien|gia_tri|gia|phi|luong)..._so                                -> money
    còn lại                                                               -> text

Đây chỉ là gợi ý: người quản trị chọn và sửa nhãn trên trang quản trị trước khi xuất bản.

Dòng lệnh (trong thư mục webapp_v2):
    python -m tools.schema_suggest "templates/Tạm dừng công ty TNHH 1 TV"
"""
import json
import re
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Set

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from docxtpl import DocxTemplate  # noqa: E402

from tools import template_lint as lint  # noqa: E402

PERSON_SUFFIXES = ("ho_ten", "so_cccd", "ngay_sinh", "gioi_tinh", "dia_chi_day_du", "dia_chi_so_nha",
                   "dia_chi_xa_phuong", "dia_chi_tinh_thanh", "ngay_cap", "noi_cap", "dan_toc", "quoc_tich")
SUGGEST_STEP_ID = "bo_sung"
SUGGEST_STEP_TITLE = "Thông tin bổ sung"
KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")

WORDS = {
    "ho_ten": "họ và tên", "so_cccd": "số CCCD", "ngay_sinh": "ngày sinh", "gioi_tinh": "giới tính",
    "dia_chi": "địa chỉ", "ma_so_thue": "mã số thuế", "ty_le": "tỷ lệ", "sdt": "số điện thoại",
    "dien_thoai": "điện thoại", "email": "email", "cong_ty": "công ty", "von": "vốn", "dieu_le": "điều lệ",
    "ngay": "ngày", "ten": "tên", "so": "số", "chu": "bằng chữ", "tien": "tiền", "gia_tri": "giá trị",
    "hop_dong": "hợp đồng", "quyet_dinh": "quyết định", "thong_bao": "thông báo", "nguoi": "người",
    "dai_dien": "đại diện", "lien_he": "liên hệ", "phi": "phí", "dich_vu": "dịch vụ", "ky": "ký",
    "tinh": "tỉnh", "thanh_pho": "thành phố", "xa_phuong": "xã/phường", "so_nha": "số nhà",
    "chuc_danh": "chức danh", "ly_do": "lý do", "noi_dung": "nội dung", "moi": "mới", "cu": "cũ",
    "nganh": "ngành", "ma": "mã", "luong": "lương", "gia": "giá", "hieu_luc": "hiệu lực",
    "gop": "góp", "quan_huyen": "quận/huyện", "cshhl": "chủ sở hữu hưởng lợi", "ddpl": "người đại diện theo pháp luật",
    "csh": "chủ sở hữu", "tv": "thành viên",
}


def humanize(key: str) -> str:
    """'ngay_ky_hop_dong' -> 'Ngày ký hợp đồng' (ghép cụm dài nhất trước)."""
    parts, out, i = key.split("_"), [], 0
    while i < len(parts):
        for n in (3, 2, 1):
            chunk = "_".join(parts[i:i + n])
            if len(parts[i:i + n]) == n and chunk in WORDS:
                out.append(WORDS[chunk])
                i += n
                break
        else:
            out.append(parts[i])
            i += 1
    text = " ".join(out).strip()
    return text[:1].upper() + text[1:] if text else key


def guess_type(key: str) -> str:
    if re.search(r"(^|_)(so_)?cccd($|_)", key):
        return "cccd"
    if re.search(r"(^|_)(ma_so_thue|mst)($|_)", key):
        return "mst_lookup"
    if re.search(r"(^|_)(sdt|dien_thoai)($|_)", key):
        return "phone"
    if re.search(r"(^|_)email($|_)", key):
        return "email"
    if re.search(r"(^|_)ty_le($|_)", key):
        return "percent"
    if re.search(r"(^|_)ngay($|_)", key):
        return "date"
    if re.search(r"(^|_)(von|tien|gia_tri|gia|phi|luong)($|_).*_so$", key) or key.endswith("_so_tien"):
        return "money"
    return "text"


def template_variables(tpl_dir: Path, jinja_env) -> Dict[str, List[str]]:
    """{biến: [các file .docx có biến đó]}; file lỗi cú pháp bị bỏ qua (công cụ quét báo E010)."""
    out: Dict[str, List[str]] = {}
    for f in sorted(tpl_dir.glob("*.docx")):
        if f.name.startswith(("~$", "_")):
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                names = DocxTemplate(str(f)).get_undeclared_template_variables(jinja_env)
        except Exception:  # noqa: BLE001
            continue
        for v in names:
            out.setdefault(v, []).append(f.name)
    return out


def unsourced_variables(tpl_dir: Path) -> Dict[str, List[str]]:
    from services.render_service import create_jinja_env

    jinja_env = create_jinja_env()
    schema_path = tpl_dir / "_schema.json"
    known: Set[str] = set(jinja_env.globals)
    if schema_path.exists():
        try:
            known = lint._sample_context_keys(json.loads(schema_path.read_text(encoding="utf-8")), jinja_env)
        except Exception:  # noqa: BLE001 - schema hỏng: công cụ quét báo E001/E002
            pass
    runtime = lint._runtime_keys()
    return {v: files for v, files in template_variables(tpl_dir, jinja_env).items()
            if v not in known and v not in runtime and not any(rx.match(v) for rx in lint.DYNAMIC_VAR_PATTERNS)}


def suggest(tpl_dir: Path) -> List[dict]:
    """Danh sách gợi ý [{key, type, label, variables, files}], sắp theo tên."""
    missing = unsourced_variables(tpl_dir)
    suggestions: Dict[str, dict] = {}
    # Gom người theo tiền tố: cần ít nhất 2 thuộc tính, hoặc có họ tên
    by_prefix: Dict[str, List[str]] = {}
    for v in missing:
        for suf in PERSON_SUFFIXES:
            if v.endswith("_" + suf) and len(v) > len(suf) + 1:
                by_prefix.setdefault(v[:-len(suf) - 1], []).append(v)
                break
    used: Set[str] = set()
    for prefix, vars_ in by_prefix.items():
        if KEY_RE.match(prefix) and (len(vars_) >= 2 or f"{prefix}_ho_ten" in vars_):
            files = sorted({f for v in vars_ for f in missing[v]})
            suggestions[prefix] = {"key": prefix, "type": "person", "label": humanize(prefix),
                                   "variables": sorted(vars_), "files": files}
            used |= set(vars_)
    for v, files in missing.items():
        if v in used or not KEY_RE.match(v):
            continue
        suggestions[v] = {"key": v, "type": guess_type(v), "label": humanize(v), "variables": [v], "files": files}
    return [suggestions[k] for k in sorted(suggestions)]


def to_field(s: dict) -> dict:
    field = {"key": s["key"], "label": s["label"], "type": s["type"]}
    if s["type"] == "person":
        field["ocr"] = True
    return field


def apply_to_schema(schema: dict, suggestions: List[dict]) -> dict:
    """Thêm các gợi ý vào bước "Thông tin bổ sung" (tạo nếu chưa có); bỏ qua khóa đã có trong schema."""
    schema = json.loads(json.dumps(schema))
    existing = {f["key"] for st in schema.get("steps", []) for f in st.get("fields", [])}
    new_fields = [to_field(s) for s in suggestions if s["key"] not in existing]
    if not new_fields:
        return schema
    step = next((st for st in schema.setdefault("steps", []) if st.get("id") == SUGGEST_STEP_ID), None)
    if step is None:
        step = {"id": SUGGEST_STEP_ID, "title": SUGGEST_STEP_TITLE, "fields": []}
        schema["steps"].append(step)
    step["fields"].extend(new_fields)
    return schema


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print(__doc__)
        return 2
    for s in suggest(Path(args[0])):
        print(f"{s['key']}\t{s['type']}\t{s['label']}\t{', '.join(s['variables'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
