"""Sinh khối "documents" cho mọi _schema.json từ các điều kiện viết cứng cũ trong render_documents.

Chạy một lần, từ thư mục gốc repo:  python scripts_and_tools/migrate_document_rules.py
Mỗi điều kiện dưới đây chép nguyên từ render_service.render_documents (trước Mục 9 bước 3) và được
đánh giá trên từng file thật, nên khối "documents" sinh ra cho đúng hành vi cũ. Ảnh chụp chuẩn
(tests/golden) xác nhận nội dung hồ sơ không đổi.
"""
import json
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "webapp_v2" / "templates"


def rules_for(clean_name: str, fname: str) -> dict:
    entry = {"file": fname}
    cn = "Chuyển nhượng" in clean_name
    # 1) Bỏ qua theo điều kiện
    if cn and ("02." in fname or "08." in fname):
        entry["when"] = {"field": "ddpl_changed", "equals": True}
    if cn and "10. Xác nhận góp vốn 2" in fname:
        entry["when"] = {"field": "tv_moi", "not_empty": False}
    # 2) Sinh lặp (thứ tự giống chuỗi if ... continue cũ)
    if cn and "09. Xác nhận góp vốn 1" in fname:
        entry.update(repeat_for="tv_moi", repeat_with="xac_nhan_gop_von")
        return entry
    if cn and ("Hợp đồng chuyển nhượng" in fname or "Biên bản thanh lý" in fname):
        entry.update(repeat_for="chuyen_nhuong", repeat_with="giao_dich_chuyen_nhuong")
        return entry
    if "Chuyển đổi" in clean_name and "Hợp đồng chuyển nhượng" in fname:
        entry.update(repeat_for="chuyen_nhuong", repeat_with="giao_dich_chuyen_doi")
        return entry
    if ("Chuyển đổi" in clean_name or "Tăng vốn" in clean_name) and "Giấy chứng nhận góp vốn" in fname:
        entry.update(repeat_for="tv_moi", repeat_with="giay_chung_nhan_gop_von")
        return entry
    # 3) Xử lý sau khi điền (theo đúng thứ tự cũ)
    post = []
    if "Danh sách thành viên" in fname:
        post.append("fill_member_table_tang_von" if "Tăng vốn" in clean_name else "fill_member_table")
    if "Danh sách cổ đông sáng lập" in fname:
        post.append("fill_founders_table")
    if "Danh sách chủ sở hữu hưởng lợi" in fname:
        post.append("fill_cshhl_table")
    if "01. Quyết định" in fname and "Chuyển đổi" in clean_name:
        post.append("fill_qd_chuyen_doi")
    if "02. Điều lệ" in fname:
        if "Chuyển đổi" in clean_name:
            post.append("fill_dieu_le_chuyen_doi")
        elif "Thành lập mới công ty TNHH 2 TV" in clean_name:
            post.append("fill_dieu_le_tlm_2tv")
        elif "Thành lập mới công ty Cổ Phần" in clean_name:
            post.append("fill_dieu_le_tlm_cp")
    if "04. Biên bản họp" in fname and "Tăng vốn" in clean_name and "Cổ Phần" in clean_name:
        post.append("fill_bbh_tang_von_cp")
    if "04. Biên bản họp" in fname and "Giảm vốn" in clean_name and "Cổ Phần" in clean_name:
        post.append("fill_bbh_giam_von_cp")
    if "02. Biên bản họp" in fname and "Tăng vốn" in clean_name and "2 TV" in clean_name:
        post.append("fill_bbh_tang_von_2tv")
    if "01. Biên bản họp" in fname and "Giải thể" in clean_name and "Cổ Phần" in clean_name:
        post.append("fill_bbh_giai_the_cp")
    if post:
        entry["post"] = post
    return entry


def main():
    for schema_path in sorted(TEMPLATES.glob("*/_schema.json")):
        folder = schema_path.parent
        raw = schema_path.read_text(encoding="utf-8")
        schema = json.loads(raw)
        files = sorted(f.name for f in folder.glob("*.docx") if not f.name.startswith(("~$", "_")))
        schema["documents"] = [rules_for(folder.name, f) for f in files]
        indent = 2 if raw.startswith('{\n  "') else 4 if raw.startswith('{\n    "') else 2
        schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=indent) + ("\n" if raw.endswith("\n") else ""),
                               encoding="utf-8")
        special = [d for d in schema["documents"] if len(d) > 1]
        print(f"{folder.name}: {len(files)} file, {len(special)} có quy tắc riêng")


if __name__ == "__main__":
    main()
