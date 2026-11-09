# Thư mục Scripts & Công cụ bổ trợ (scripts_and_tools)

Thư mục này chứa tất cả các script bổ trợ, file kiểm tra (check, review), phân tích (analysis), nhật ký log, và các file tạm của dự án:
- Các file Python tiện ích: trích xuất placeholder, chuẩn hóa, sửa lỗi, test API...
- Các file phân tích văn bản: , , ...

**Quy tắc dự án:**
Từ nay, mọi file nhỏ, script hỗ trợ, file test hoặc phân tích mới khi sinh ra sẽ được lưu trực tiếp vào thư mục  này để giữ cho thư mục gốc luôn gọn gàng, sạch sẽ.

**Khóa bí mật:** không viết khóa API, token, mật khẩu vào mã nguồn; đọc từ biến môi trường hoặc file `.env` (đã có trong `.gitignore`). Test `webapp_v2/tests/test_no_secrets.py` quét cả repo và báo lỗi nếu phát hiện chuỗi có dạng khóa.
