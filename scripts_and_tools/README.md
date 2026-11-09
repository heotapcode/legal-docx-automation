# Thư mục Scripts & Công cụ bổ trợ (scripts_and_tools)

Thư mục này chứa tất cả các script bổ trợ, file kiểm tra (check, review), phân tích (analysis), nhật ký log, và các file tạm của dự án:
- Các file Python tiện ích: trích xuất placeholder, chuẩn hóa, sửa lỗi, test API...
- Các file phân tích văn bản: , , ...
- Các bot thử nghiệm cũ (Telegram bot, start/stop bot...)

**Quy tắc dự án:**
Từ nay, mọi file nhỏ, script hỗ trợ, file test hoặc phân tích mới khi sinh ra sẽ được lưu trực tiếp vào thư mục  này để giữ cho thư mục gốc luôn gọn gàng, sạch sẽ.

**Khóa bí mật:** `telegram_bot.py` và `wizard_cn2tv.py` đọc khóa từ biến môi trường `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`; không viết khóa vào mã nguồn.
