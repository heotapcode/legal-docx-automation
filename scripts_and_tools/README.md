# Scripts & công cụ bổ trợ (scripts_and_tools)

Các script dựng / sửa mẫu Word trong `webapp_v2/templates/`. Chạy từ thư mục gốc repo.
`nguon_mau/` chứa file nguồn không có dữ liệu cá nhân (form nhà nước); nguồn có dữ liệu người thật không lưu trong repo.

| Script | Việc | Chạy lại được |
|---|---|---|
| `build_muc8_thong_bao.py` | Dựng mẫu Thông báo thay đổi nội dung ĐKDN có điều kiện (Mục 8, bộ `Thay đổi nội dung ĐKKD`) | Không (từ chối nếu mẫu đã được dựng) |
| `build_muc8_quyet_dinh.py` | Dựng Quyết định và Biên bản họp của thủ tục gộp; sửa câu chữ ở đây rồi chạy lại | Có (ghi đè hai file đích) |
| `build_ho_kinh_doanh.py` | Dựng bộ mẫu `Thành lập hộ kinh doanh` từ form gốc trong `nguon_mau/ho_kinh_doanh/` (`--uq` để dựng lại Giấy ủy quyền từ file ngoài repo). Ví dụ mẫu cho quy trình `webapp_v2/docs/them-thu-tuc-moi.md` | Có (ghi đè file đích) |
| `migrate_flat_schemas.py` | Chuyển `_schema.json` dạng `fields` phẳng sang dạng `steps` | Có |
| `localize_ha_noi.py` | Thay chữ "Hà Nội" viết cứng bằng biến theo ô chọn tỉnh/thành phố (`--dry-run` để xem trước) | Có |
| `use_phong_dkkd.py` | Thay tên phòng đăng ký kinh doanh bằng `{{ phong_dkkd }}` (chạy sau `localize_ha_noi.py`) | Có |
| `uy_quyen_dung_bien.py` | Thay thông tin người nhận ủy quyền viết cứng trong mẫu bằng biến `{{ uq_* }}` (`--dry-run` để xem trước) | Có |
| `scrub_sample_people.py` | Xóa thông tin cá nhân người thật còn sót trong mẫu | Có |
| `tach_bieu_mau_thong_tu.py` | Tách file Phụ lục biểu mẫu ĐKDN (nhiều mẫu trong một file) thành mỗi mẫu một file trong `nguon_mau/thong_tu_2026_du_thao/` | Có (ghi đè) |

Các script kiểm tra / sửa chạy một lần trước đây đã được xóa (vẫn còn trong lịch sử git nếu cần tra lại).
Kiểm tra mẫu hằng ngày dùng `python -m tools.template_lint` (trong `webapp_v2`) và bộ test `webapp_v2/tests`.

**Khóa bí mật:** không viết khóa API, token, mật khẩu vào mã nguồn; đọc từ biến môi trường hoặc file `.env` (đã có trong
`.gitignore`). Test `webapp_v2/tests/test_no_secrets.py` quét cả repo và báo lỗi nếu phát hiện chuỗi có dạng khóa.
