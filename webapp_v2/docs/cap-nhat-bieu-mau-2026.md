# Cập nhật biểu mẫu đăng ký doanh nghiệp theo thông tư 2026 (dự thảo 20/8/2026)

Nguồn: `scripts_and_tools/nguon_mau/thong_tu_2026_du_thao/` (file Phụ lục gốc + từng mẫu tách bằng
`scripts_and_tools/tach_bieu_mau_thong_tu.py`). Khi có bản chính thức: thay file gốc, chạy lại script tách và các script dựng
bên dưới, rồi xem `git diff tests/golden`.

## Mẫu số 12 – Giấy đề nghị / Thông báo thay đổi nội dung ĐKDN

Script: `scripts_and_tools/build_mau12_thong_bao_thay_doi.py` (dựng lại 10 file, giữ tên biến từng thủ tục).

Quyết định của người dùng (12/11/2026):

1. Dòng "Doanh nghiệp có Giấy chứng nhận quyền sử dụng đất tại đảo…": giữ nguyên như form, không đánh dấu sẵn.
2. Ô "Đề nghị Quý Cơ quan cấp Giấy xác nhận thay đổi…": luôn đánh dấu X.
3. Chức danh người ký: để nguyên dòng dài của form (người dùng tự sửa khi cần).
4. Không in: thay đổi trên cơ sở tách/sáp nhập, sửa đổi chi tiết ngành + "Lưu ý", mục C hiệu đính
   (cùng các phần app không dùng: vốn đầu tư DNTN, người đại diện theo ủy quyền, cổ đông sáng lập/NĐT nước ngoài).
5. Chủ sở hữu hưởng lợi: in cả hai đoạn của form.

Thay đổi form nhập kèm theo:

- Thay đổi địa chỉ và thuế TNHH 2 TV: địa chỉ trụ sở mới nhập 3 ô (`dia_chi_moi_so_nha|xa_phuong|tinh_thanh`, ghép lại
  thành `dia_chi_moi` cho Quyết định/Biên bản); thêm ngày sinh, giới tính kế toán trưởng (mẫu cũ ghi cứng "Nữ").
- Thay đổi ngành nghề TNHH 1 TV: thêm ô chọn tỉnh/thành phố nơi đăng ký (mẫu cũ ghi cứng "Nghệ An"; Quyết định và
  Giấy ủy quyền của bộ này vẫn còn ghi cứng, chưa sửa).
- Tăng vốn TNHH 1 TV: bỏ ô "Địa chỉ trụ sở" (Mẫu 12 không có dòng này, không văn bản nào khác dùng).
- Bỏ hết chú thích cuối trang của Mẫu 12 (người dùng yêu cầu 12/11/2026): sau khi lược phần, số thứ tự chú thích không còn khớp nội dung.

## Mẫu số 2, 3, 4 – Giấy đề nghị đăng ký doanh nghiệp (thành lập mới TNHH 1 TV, TNHH 2 TV, Cổ phần)

Script: `scripts_and_tools/build_mau234_giay_de_nghi.py` (giữ tên biến; giữ các ô đã đánh dấu / điền sẵn của mẫu cũ:
Thành lập mới, Hạch toán độc lập, Khấu trừ, BHXH hàng tháng, BOT: Không, năm tài chính 01/01–31/12 (2 TV, CP),
số lao động 02/04, chức danh Giám đốc).

Quyết định của người dùng (12/11/2026):

1. Giữ các phần cho trường hợp đặc biệt (chia/tách/hợp nhất/chuyển đổi, hộ kinh doanh, cơ sở bảo trợ xã hội, chủ sở
   hữu là tổ chức, Giấy chứng nhận đăng ký đầu tư, Phụ lục Cam kết nhà đầu tư nước ngoài): để trống, người dùng tự sửa.
2. Giữ khối "Trường hợp không có số định danh cá nhân…" (để trống).
3. TNHH 1 TV: "Mô hình tổ chức công ty" đánh dấu "Chủ tịch công ty, Giám đốc hoặc Tổng Giám đốc".
4. Bỏ đoạn "Lưu ý" về phương thức đóng bảo hiểm xã hội.

Sửa kèm: mẫu Cổ phần trước ghi cứng số cổ phần 600.000 và "năm 2025", nay dùng `{{ so_luong_cp_moi }}` (vốn ÷ 10.000) và
năm theo ngày lập; địa chỉ người đăng ký dùng đúng tỉnh của người đại diện (trước lấy nhầm tỉnh của trụ sở).
