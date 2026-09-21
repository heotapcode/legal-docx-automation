import docx, re, json
from pathlib import Path

base_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word")
tpl_v2 = base_dir / "webapp_v2" / "templates"

def run_audit():
    # Toàn bộ các bộ hồ sơ có tính chất nhiều thành viên/cổ đông đã hoàn thiện cơ chế động
    COMPLETED_DYNAMIC_KITS = {
        "Chuyển đổi loại hình 1TV sang 2 TV",
        "Thành lập mới công ty TNHH 2 TV",
        "Thành lập mới công ty Cổ Phần",
        "Tăng vốn công ty TNHH 2 TV",
        "Tăng vốn công ty Cổ Phần",
        "Chuyển nhượng Công ty TNHH 2 TV",
        "Giải thể công ty TNHH 2 TV",
        "Giải thể công ty Cổ Phần"
    }

    summary = {
        "group_a_completed_dynamic": [],
        "group_b_simple_standardized": [],
        "group_c_need_dynamic": [],
        "group_d_unstandardized": []
    }

    for d in sorted(tpl_v2.iterdir()):
        if not d.is_dir():
            continue
        files = [f for f in d.glob("*.docx") if not f.name.startswith(("~$", "_"))]

        all_vars = set()
        for f in files:
            try:
                doc = docx.Document(f)
                txt = "\n".join([p.text for p in doc.paragraphs] + [c.text for t in doc.tables for r in t.rows for c in r.cells])
                matches = re.findall(r"\{\{([^\}]+)\}\}", txt)
                all_vars.update(matches)
            except:
                pass

        kit_info = {
            "name": d.name,
            "file_count": len(files),
            "var_count": len(all_vars)
        }

        if len(all_vars) == 0:
            summary["group_d_unstandardized"].append(kit_info)
        elif d.name in COMPLETED_DYNAMIC_KITS:
            summary["group_a_completed_dynamic"].append(kit_info)
        else:
            summary["group_b_simple_standardized"].append(kit_info)

    return summary

if __name__ == "__main__":
    res = run_audit()
    print(f"Tổng số bộ mẫu: {sum(len(v) for v in res.values())}")
    print(f"- Nhóm A (Đã hoàn thiện toàn diện N người động): {len(res['group_a_completed_dynamic'])} bộ")
    print(f"- Nhóm B (Đã chuẩn hóa cơ bản form đơn/1 người/địa điểm/tạm dừng): {len(res['group_b_simple_standardized'])} bộ")
    print(f"- Nhóm C (Cần xử lý động): {len(res['group_c_need_dynamic'])} bộ")
    print(f"- Nhóm D (Chưa chuẩn hóa): {len(res['group_d_unstandardized'])} bộ")
    print("\nChi tiết Nhóm A:")
    for k in res["group_a_completed_dynamic"]:
        print(f"  * {k['name']} ({k['file_count']} files, {k['var_count']} biến)")
    print("\nChi tiết Nhóm B:")
    for k in res["group_b_simple_standardized"]:
        print(f"  * {k['name']} ({k['file_count']} files, {k['var_count']} biến)")
