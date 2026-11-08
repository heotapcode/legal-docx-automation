"""Test công cụ quét mẫu tools/template_lint.py."""
import json

import docx
import pytest

from conftest import list_template_names
from config import TEMPLATES_DIR
from tools import template_lint


def make_template(tmp_path, paragraphs, schema=None):
    d = tmp_path / "Bộ thử nghiệm"
    d.mkdir()
    doc = docx.Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    doc.save(str(d / "01. Thử.docx"))
    schema = schema or {
        "id": "bo-thu-nghiem", "name": "Bộ thử nghiệm", "display_name": "Bộ thử nghiệm",
        "has_nganh": False,
        "steps": [{"id": "company", "title": "Công ty",
                   "fields": [{"key": "ten_cong_ty_vn", "label": "Tên công ty", "type": "text", "required": True}]}],
    }
    (d / "_schema.json").write_text(json.dumps(schema, ensure_ascii=False), encoding="utf-8")
    return d


def codes(findings):
    return {f.code for f in findings}


def test_clean_template_has_no_findings(tmp_path):
    d = make_template(tmp_path, ["Tên doanh nghiệp: {{ ten_cong_ty_vn }}", "Người đại diện: {{ ddpl_ho_ten }}"])
    assert [f for f in template_lint.lint_template(d) if f.level != "info"] == []


@pytest.mark.parametrize("text, code", [
    ("Tên: {{ ten_cong_ty_vn }", "E011"),                 # thiếu dấu đóng
    ("{% if ten_cong_ty_vn %}Có tên", "E010"),           # thiếu endif -> lỗi cú pháp
    ("Tên: [TEN_CONG_TY]", "W020"),                       # placeholder kiểu cũ
    ("Người nhận: {{ bien_khong_ton_tai }}", "W021"),     # biến không có nguồn dữ liệu
    ("Liên hệ: nguyenvana@example.com", "W030"),          # email viết cứng
    ("Điện thoại: 0987.135.358", "W030"),                 # số điện thoại viết cứng
    ("CCCD số: 001089021350", "W030"),                    # số CCCD viết cứng
    ("CÔNG TY TNHH PHÁT TRIỂN CÔNG NGHỆ MẪU", "W030"),    # tên công ty khách hàng viết cứng
    ("Công ty cổ phần THƯƠNG MẠI ĐẠI PHÁT", "W030"),
])
def test_detects_problem(tmp_path, text, code):
    d = make_template(tmp_path, [text])
    assert code in codes(template_lint.lint_template(d))


def test_values_inside_jinja_tags_are_not_flagged(tmp_path):
    d = make_template(tmp_path, ['Email: {{ email or "lienhe@example.com" }}'])
    assert "W030" not in codes(template_lint.lint_template(d))


@pytest.mark.parametrize("text", [
    "DANH SÁCH THÀNH VIÊN CÔNG TY TRÁCH NHIỆM HỮU HẠN HAI THÀNH VIÊN TRỞ LÊN",
    "Đăng ký thay đổi thành viên công ty TNHH hai thành viên trở lên",
    "CÔNG TY TNHH MỘT THÀNH VIÊN",
    "Tên: {{ ten_cong_ty_vn }} (CÔNG TY TNHH)",
])
def test_company_type_titles_are_not_company_names(tmp_path, text):
    d = make_template(tmp_path, [text])
    assert "W030" not in codes(template_lint.lint_template(d))


def test_money_is_not_mistaken_for_phone(tmp_path):
    d = make_template(tmp_path, ["Vốn điều lệ: 1.000.000.000 đồng, mệnh giá 10.000 đồng"])
    assert "W030" not in codes(template_lint.lint_template(d))


def test_runtime_variables_are_info_not_warning(tmp_path):
    d = make_template(tmp_path, ["Bên A: {{ ben_a_ho_ten }}, thành viên 2: {{ tv2_ho_ten }}"])
    found = template_lint.lint_template(d)
    assert "W021" not in codes(found)
    assert "I022" in codes(found)


def test_missing_and_broken_schema(tmp_path):
    d = make_template(tmp_path, ["{{ ten_cong_ty_vn }}"])
    (d / "_schema.json").write_text("{không phải json", encoding="utf-8")
    assert "E001" in codes(template_lint.lint_template(d))
    (d / "_schema.json").unlink()
    assert "E001" in codes(template_lint.lint_template(d))


def test_schema_spec_violation(tmp_path):
    bad = {"id": "Bo Sai", "name": "x", "display_name": "x",
           "steps": [{"id": "a", "title": "A", "fields": [{"key": "k", "label": "K", "type": "khong_ho_tro"}]}]}
    d = make_template(tmp_path, ["{{ k }}"], schema=bad)
    msgs = [f.message for f in template_lint.lint_template(d) if f.code == "E002"]
    assert msgs, "Phải báo id sai định dạng và kiểu trường không hỗ trợ"


def test_cli_exit_codes(tmp_path, capsys):
    good = make_template(tmp_path, ["{{ ten_cong_ty_vn }}"])
    assert template_lint.main([str(good)]) == 0
    bad_root = tmp_path / "bad"
    bad_root.mkdir()
    bad = make_template(bad_root, ["{{ ten_cong_ty_vn }"])
    assert template_lint.main([str(bad)]) == 1
    warn_root = tmp_path / "warn"
    warn_root.mkdir()
    warn = make_template(warn_root, ["Email: a@b.vn {{ ten_cong_ty_vn }}"])
    assert template_lint.main([str(warn)]) == 0
    assert template_lint.main(["--strict", str(warn)]) == 1
    template_lint.main(["--json", str(warn)])
    out = capsys.readouterr().out
    assert '"W030"' in out


@pytest.mark.parametrize("name", list_template_names())
def test_real_templates_have_no_errors(name):
    """Mọi bộ mẫu thật không được có lỗi (E). Cảnh báo (W) được phép nhưng nên giảm dần."""
    errors = [f for f in template_lint.lint_template(TEMPLATES_DIR / name) if f.level == "error"]
    assert not errors, "\n".join(f"{f.code} [{f.file}] {f.message}" for f in errors)


# CCCD được phép xuất hiện trong mẫu: người nhận ủy quyền trong Giấy ủy quyền (giữ nguyên theo yêu cầu)
ALLOWED_HARDCODED_CCCD = {"001089021350"}


def test_no_unexpected_personal_id_in_templates():
    """Không được để số CCCD của người thật (ngoài danh sách cho phép) trong file mẫu."""
    leaked = []
    for name in list_template_names():
        for f in template_lint.lint_template(TEMPLATES_DIR / name):
            if f.code == "W030" and f.message.startswith("Số cccd"):
                value = f.message.rsplit(": ", 1)[-1]
                if value not in ALLOWED_HARDCODED_CCCD:
                    leaked.append(f"{name} / {f.file}: {value}")
    assert not leaked, "\n".join(leaked)



def test_documents_block_mismatch_is_error(tmp_path):
    schema = {
        "id": "bo-thu-nghiem", "name": "Bộ thử nghiệm", "display_name": "Bộ thử nghiệm",
        "steps": [{"id": "c", "title": "C", "fields": [{"key": "ten_cong_ty_vn", "label": "Tên", "type": "text"}]}],
        "documents": [{"file": "02. Không tồn tại.docx"}],
    }
    d = make_template(tmp_path, ["{{ ten_cong_ty_vn }}"], schema=schema)
    msgs = [f.file for f in template_lint.lint_template(d) if f.code == "E003"]
    assert "01. Thử.docx" in msgs and "02. Không tồn tại.docx" in msgs
