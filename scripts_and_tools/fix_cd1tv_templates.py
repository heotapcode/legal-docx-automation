import docx
import re
from pathlib import Path

template_dir = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Chuyển đổi loại hình 1TV sang 2 TV")

print("=== FIXING TEMPLATES FOR 'Chuyển đổi loại hình 1TV sang 2 TV' ===\n")

# -------------------------------------------------------------
# 1. FIX 01. Quyết định.docx
# -------------------------------------------------------------
doc1_path = template_dir / "01. Quyết định.docx"
doc1 = docx.Document(str(doc1_path))

for idx, p in enumerate(doc1.paragraphs):
    txt = p.text
    # 1. Tên công ty chuyển đổi
    if "1. Tên công ty chuyển đổi:" in txt and "{{ ten_cong_ty_vn_cu }}" not in txt:
        p.text = "1. Tên công ty chuyển đổi: {{ ten_cong_ty_vn_cu }}"
        print("  [01. Quyết định] Fixed P: 1. Tên công ty chuyển đổi: {{ ten_cong_ty_vn_cu }}")
    # 2. Tên công ty được chuyển đổi
    elif "2. Tên công ty được chuyển đổi:" in txt and "{{ ten_cong_ty_vn }}" not in txt:
        p.text = "2. Tên công ty được chuyển đổi: {{ ten_cong_ty_vn }}"
        print("  [01. Quyết định] Fixed P: 2. Tên công ty được chuyển đổi: {{ ten_cong_ty_vn }}")
    # Clean hack tags
    elif "<<BEGIN_TV_BLOCK>>" in txt or "<<END_TV_BLOCK>>" in txt:
        p.text = txt.replace("<<BEGIN_TV_BLOCK>>", "").replace("<<END_TV_BLOCK>>", "").strip()
        print("  [01. Quyết định] Removed <<...TV_BLOCK>>")
    # Replace hardcoded Ong/Ba in cam ket
    elif "Ông {{ tv2_ho_ten }} cam kết không vi phạm" in txt:
        p.text = txt.replace("Ông {{ tv2_ho_ten }} cam kết không vi phạm", '{{ "Ông" if tv2_gioi_tinh == "Nam" else "Bà" }} {{ tv2_ho_ten }} cam kết không vi phạm')
        print("  [01. Quyết định] Fixed dynamic title in cam ket")
    # Replace transfer text
    elif "nhận chuyển nhượng phần vốn góp từ bà {{ ddpl_ho_ten }}" in txt or "nhận chuyển nhượng phần vốn góp từ" in txt:
        p.text = '- {{ "Ông" if tv2_gioi_tinh == "Nam" else "Bà" }} {{ tv2_ho_ten }} nhận chuyển nhượng phần vốn góp từ {{ "ông" if ddpl_gioi_tinh == "Nam" else "bà" }} {{ ddpl_ho_ten }} là {{ tv2_von_cu_so }} đồng ({{ tv2_von_cu_chu }}).'
        print("  [01. Quyết định] Fixed transfer sentence in P")
    # Dia chi DDPL tai muc 7
    elif "Địa chỉ liên lạc: {{ dia_chi_so_nha }}, {{ dia_chi_xa_phuong }}, {{ dia_chi_tinh_thanh }}" in txt:
        prev_txt = "".join([doc1.paragraphs[i].text for i in range(max(0, idx-5), idx)])
        if "7. Người đại diện" in prev_txt:
            p.text = "Địa chỉ liên lạc: {{ ddpl_dia_chi_so_nha }}, {{ ddpl_dia_chi_xa_phuong }}, {{ ddpl_dia_chi_tinh_thanh }}"
            print("  [01. Quyết định] Fixed DDPL address in Section 7")

# Fix Table 3 (swap swapped foreign name and short name)
if len(doc1.tables) > 3:
    t3 = doc1.tables[3]
    for r in t3.rows:
        if "tiếng nước ngoài" in r.cells[0].text:
            r.cells[1].text = "{{ ten_cong_ty_nn }}"
            print("  [01. Quyết định] Fixed Table 3 tiếng nước ngoài -> {{ ten_cong_ty_nn }}")
        elif "viết tắt" in r.cells[0].text:
            r.cells[1].text = "{{ ten_cong_ty_viet_tat }}"
            print("  [01. Quyết định] Fixed Table 3 viết tắt -> {{ ten_cong_ty_viet_tat }}")

# Fix Table 6 (Member address instead of company address)
if len(doc1.tables) > 6:
    t6 = doc1.tables[6]
    if len(t6.rows) >= 3:
        # Row 1 is TV1 (CSH)
        t6.rows[1].cells[2].text = "{{ ddpl_dia_chi_so_nha }}, {{ ddpl_dia_chi_xa_phuong }}, {{ ddpl_dia_chi_tinh_thanh }}"
        # Row 2 is TV2
        t6.rows[2].cells[2].text = "{{ tv2_dia_chi_so_nha }}, {{ tv2_dia_chi_xa_phuong }}, {{ tv2_dia_chi_tinh_thanh }}"
        print("  [01. Quyết định] Fixed Table 6 members address")

doc1.save(str(doc1_path))
print("Saved 01. Quyết định.docx!\n")


# -------------------------------------------------------------
# 2. FIX 02. Điều lệ.docx
# -------------------------------------------------------------
doc2_path = template_dir / "02. Điều lệ.docx"
doc2 = docx.Document(str(doc2_path))

for p in doc2.paragraphs:
    txt = p.text
    if "<<BEGIN_TV_BLOCK>>" in txt or "<<END_TV_BLOCK>>" in txt:
        p.text = txt.replace("<<BEGIN_TV_BLOCK>>", "").replace("<<END_TV_BLOCK>>", "").strip()
        print("  [02. Điều lệ] Removed <<...TV_BLOCK>>")

doc2.save(str(doc2_path))
print("Saved 02. Điều lệ.docx!\n")


# -------------------------------------------------------------
# 3. FIX 03. Giấy đề nghị.docx
# -------------------------------------------------------------
doc3_path = template_dir / "03. Giấy đề nghị.docx"
doc3 = docx.Document(str(doc3_path))

for idx, p in enumerate(doc3.paragraphs):
    txt = p.text
    if "Tỉnh/Thành phố trực thuộc trung ương: Hà Nội" in txt:
        # Check context
        p.text = txt.replace("Tỉnh/Thành phố trực thuộc trung ương: Hà Nội", "Tỉnh/Thành phố trực thuộc trung ương: {{ dia_chi_tinh_thanh }}")
        print("  [03. Giấy đề nghị] Replaced hardcoded 'Hà Nội' with {{ dia_chi_tinh_thanh }}")
    if "Điện thoại (nếu có): …………………" in txt:
        p.text = txt.replace("Điện thoại (nếu có): …………………", "Điện thoại: {{ sdt_cong_ty }}").replace("Thư điện tử (nếu có): ……………", "Email: {{ email_cong_ty }}")
        print("  [03. Giấy đề nghị] Replaced blank dots with {{ sdt_cong_ty }} and {{ email_cong_ty }}")
    if "Tên doanh nghiệp (ghi bằng chữ in hoa): {{ ten_cong_ty_vn }}" in txt:
        prev_txt = "".join([doc3.paragraphs[i].text for i in range(max(0, idx-3), idx)])
        if "Thông tin về các doanh nghiệp được chuyển đổi" in prev_txt or "Mã số doanh nghiệp/Mã số thuế" in txt:
            p.text = txt.replace("{{ ten_cong_ty_vn }}", "{{ ten_cong_ty_vn_cu }}")
            print("  [03. Giấy đề nghị] Replaced company name with {{ ten_cong_ty_vn_cu }} in converted company section")

# Fix Table 5 (Tax table - Giám đốc info)
if len(doc3.tables) > 5:
    t5 = doc3.tables[5]
    for r in t5.rows:
        if len(r.cells) >= 2 and r.cells[0].text.strip() == "9.1":
            new_tax_txt = (
                "Thông tin về Giám đốc/Tổng giám đốc (nếu có):\n"
                "Họ, chữ đệm và tên Giám đốc/Tổng giám đốc: {{ ddpl_ho_ten }}\n"
                "Ngày, tháng, năm sinh: {{ ddpl_ngay_sinh }}      Giới tính: {{ ddpl_gioi_tinh }}\n"
                "Số định danh cá nhân: {{ ddpl_so_cccd }}\n"
                "Điện thoại: {{ sdt_cong_ty }}"
            )
            for c in r.cells[1:]:
                c.text = new_tax_txt
            print("  [03. Giấy đề nghị] Populated Table 5 9.1 Giám đốc tax info with placeholders!")

doc3.save(str(doc3_path))
print("Saved 03. Giấy đề nghị.docx!\n")


# -------------------------------------------------------------
# 4. FIX 07. Hợp đồng chuyển nhượng + Biên bản thanh lý.docx
# -------------------------------------------------------------
doc7_path = template_dir / "07. Hợp đồng chuyển nhượng + Biên bản thanh lý.docx"
doc7 = docx.Document(str(doc7_path))

for p in doc7.paragraphs:
    txt = p.text
    if "Hôm nay, ngày    tháng    năm" in txt:
        p.text = txt.replace("Hôm nay, ngày    tháng    năm       ,", "Hôm nay, {{ today_vn() }},")
        print("  [07. Hợp đồng] Added {{ today_vn() }} to agreement header")
    if "Thời điểm chuyển nhượng: ngày     tháng    năm" in txt:
        p.text = txt.replace("Thời điểm chuyển nhượng: ngày     tháng    năm", "Thời điểm chuyển nhượng: {{ today_vn() }}")
        print("  [07. Hợp đồng] Added {{ today_vn() }} to transfer date")
    if "Hôm nay, ngày    tháng     năm      ," in txt:
        p.text = txt.replace("Hôm nay, ngày    tháng     năm      ,", "Hôm nay, {{ today_vn() }},")
        print("  [07. Hợp đồng] Added {{ today_vn() }} to liquidation header")
    if "ĐIỀU 1. Thanh lý hợp đồng chuyển nhượng phần vốn góp được ký ngày    tháng    năm" in txt:
        p.text = txt.replace("được ký ngày    tháng    năm", "được ký {{ today_vn() }}")
        print("  [07. Hợp đồng] Added {{ today_vn() }} to liquidation Article 1")
    if "Hợp đồng chuyển nhượng vốn góp được ký ngày      tháng      năm" in txt:
        p.text = txt.replace("được ký ngày      tháng      năm", "được ký {{ today_vn() }}")
        print("  [07. Hợp đồng] Added {{ today_vn() }} to liquidation Article 2")

doc7.save(str(doc7_path))
print("Saved 07. Hợp đồng chuyển nhượng + Biên bản thanh lý.docx!\n")

print("=== ALL TEMPLATE PLACEHOLDERS FIXED SUCCESSFULLY! ===")
