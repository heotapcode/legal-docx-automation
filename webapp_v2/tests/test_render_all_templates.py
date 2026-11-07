"""Sinh hồ sơ end-to-end cho TẤT CẢ bộ mẫu qua API và kiểm tra nội dung file Word."""
import re

import pytest

from config import TEMPLATES_DIR
from conftest import build_payload, list_template_names, read_zip

TEMPLATES = list_template_names()

# Những dấu hiệu cho thấy dữ liệu bị điền sai / sót placeholder
BAD_PATTERNS = [
    (re.compile(r"\{\{|\}\}|\{%|%\}"), "placeholder Jinja chưa được thay"),
    (re.compile(r"\bNone\b"), "chữ None"),
    (re.compile(r"\bundefined\b"), "chữ undefined"),
    (re.compile(r"\bnan\b"), "chữ nan"),
    (re.compile(r"\[object Object\]"), "[object Object]"),
    (re.compile(r"\{'|\['"), "repr dict/list của Python"),
]


# Số file kỳ vọng cho các bộ có quy tắc tách/bỏ file đặc biệt (xem render_documents):
# Chuyển nhượng 2 TV: file 09 được tách thành 1 file/thành viên mới và file 10 bị bỏ.
EXPECTED_FILE_COUNT = {
    "Chuyển nhượng Công ty TNHH 2 TV": lambda n_tpl, n_mem: n_tpl - 2 + n_mem,
}


def test_found_templates():
    assert len(TEMPLATES) >= 20, f"Chỉ tìm thấy {len(TEMPLATES)} bộ mẫu"


@pytest.mark.parametrize("n_members", [1, 3], ids=lambda n: f"{n}tv")
@pytest.mark.parametrize("name", TEMPLATES)
def test_render_template(client, name, n_members):
    payload, markers, members = build_payload(name, n_members)
    r = client.post("/api/documents/generate", json=payload)
    assert r.status_code == 200, r.text[:500]
    assert r.headers["content-type"] == "application/zip"

    files = read_zip(r.content)
    assert "_CANH_BAO_LOI_HO_SO.txt" not in files, files.get("_CANH_BAO_LOI_HO_SO.txt")

    docx_files = {k: v for k, v in files.items() if k.endswith(".docx")}
    # Không được mất file mẫu nào (có thể nhiều hơn khi tách theo thành viên/giao dịch)
    n_templates = len([f for f in (TEMPLATES_DIR / name).glob("*.docx") if not f.name.startswith(("~$", "_"))])
    if name in EXPECTED_FILE_COUNT:
        expected = EXPECTED_FILE_COUNT[name](n_templates, len(members))
        assert len(docx_files) == expected, f"Sinh {len(docx_files)} file, kỳ vọng {expected}: {sorted(docx_files)}"
    else:
        assert len(docx_files) >= n_templates, f"Chỉ sinh {len(docx_files)}/{n_templates} file"

    problems = []
    for fname, text in docx_files.items():
        for pat, label in BAD_PATTERNS:
            m = pat.search(text)
            if m:
                ctx = text[max(0, m.start() - 40): m.end() + 40].replace("\n", " ")
                problems.append(f"{fname}: {label} …{ctx}…")
    assert not problems, "\n".join(problems)

    all_text = "\n".join(docx_files.values())
    missing_fields = [k for k, v in markers.items() if v not in all_text]
    assert not missing_fields, f"Các trường nhập không xuất hiện trong hồ sơ: {missing_fields}"
    missing_members = [m["ho_ten"] for m in members if m["ho_ten"] not in all_text]
    assert not missing_members, f"Thành viên không xuất hiện trong hồ sơ: {missing_members}"


def test_chuyen_nhuong_splits_contract_per_transfer(client):
    name = "Chuyển nhượng Công ty TNHH 2 TV"
    payload, _, _ = build_payload(name, 3)
    second = dict(payload["data"]["chuyen_nhuong"][0])
    second["ben_a"] = dict(second["ben_a"], ho_ten="TRẦN THỊ BÊN A2")
    payload["data"]["chuyen_nhuong"].append(second)
    payload["special_payload"]["chuyen_nhuong"] = payload["data"]["chuyen_nhuong"]

    r = client.post("/api/documents/generate", json=payload)
    assert r.status_code == 200
    contracts = [n for n in read_zip(r.content) if "Hợp đồng chuyển nhượng" in n]
    assert len(contracts) == 2, contracts


@pytest.mark.parametrize("ly_do, expected", [
    ("Công ty đã tìm được nhà đầu tư mới", "Công ty đã tìm được nhà đầu tư mới"),
    ("", "Doanh nghiệp tiếp tục duy trì hoạt động kinh doanh"),
])
def test_huy_bo_giai_the_uses_ly_do(client, ly_do, expected):
    name = "Hủy bỏ quyết định giải thể"
    payload, _, _ = build_payload(name, 1)
    payload["data"]["ly_do_huy"] = ly_do
    r = client.post("/api/documents/generate", json=payload)
    assert r.status_code == 200
    qd = next(v for k, v in read_zip(r.content).items() if k.startswith("02."))
    assert f"Lý do hủy bỏ Quyết định giải thể: {expected}" in qd
