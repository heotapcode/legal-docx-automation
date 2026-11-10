# Hệ Thống Tự Động Hóa Hồ Sơ Pháp Lý Doanh Nghiệp (Legal Docx WebApp V2)

Hệ thống webapp thông minh hỗ trợ nhập liệu, tra cứu, trích xuất dữ liệu tự động (OCR/MST) và sinh trọn gói các bộ hồ sơ Đăng ký kinh doanh (ĐKKD) định dạng chuẩn Microsoft Word (`.docx`).

---

## 🌟 Tính Năng Nổi Bật

1. **Hỗ Trợ Toàn Diện 19 Bộ Hồ Sơ Pháp Lý Chuẩn:**
   - **Thành lập mới:** TNHH 1 TV, TNHH 2 TV trở lên, Cổ Phần, Địa điểm kinh doanh.
   - **Thay đổi ĐKKD:** Thay đổi nội dung ĐKKD chung, Cấp lại giấy chứng nhận ĐKKD.
   - **Tăng vốn điều lệ:** TNHH 2 TV trở lên, Cổ Phần.
   - **Chuyển nhượng phần vốn góp:** TNHH 1 TV, TNHH 2 TV trở lên.
   - **Chuyển đổi loại hình:** Chuyển đổi từ TNHH 1 TV sang TNHH 2 TV trở lên (Hợp đồng chuyển nhượng, Giấy chứng nhận góp vốn, Điều lệ, Quyết định...).
   - **Tạm dừng hoạt động & Hoạt động lại:** TNHH 1 TV, TNHH 2 TV, Cổ Phần.
   - **Giải thể doanh nghiệp:** TNHH 1 TV, TNHH 2 TV, Cổ Phần.

2. **Cơ Chế Danh Sách Động Đa Thành Viên / Cổ Đông ($N$ người):**
   - Tự động co giãn theo số lượng thực tế thành viên/cổ đông: bảng biểu, điều lệ, biên bản họp và chữ ký tự động mở rộng không giới hạn.
   - Tự động sinh riêng từng cặp Hợp đồng chuyển nhượng + Biên bản thanh lý và Giấy chứng nhận/xác nhận vốn góp tương ứng cho mỗi cá nhân.

3. **Tích Hợp Tiện Ích Thông Minh:**
   - **Tra cứu Mã số thuế tự động:** Tự động lấy tên công ty, địa chỉ trụ sở qua API VietQR.
   - **OCR Nhận diện thẻ CCCD / VNeID:** Đọc mã QR trên thẻ, không có QR thì OCR bằng Tesseract; chạy hoàn toàn trên máy, không cần khóa API, ảnh không gửi ra ngoài. Ô cần rà lại được viền cam.
   - **Chuẩn hóa văn bản hành chính:** Định dạng phông chữ Times New Roman đồng bộ, tự động đọc số tiền thành chữ tiếng Việt chuẩn xác.

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Yêu cầu hệ thống
- Python 3.10 trở lên
- Hệ điều hành: Windows / macOS / Linux

### 2. Cài đặt các thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

### 3. Cài dữ liệu OCR tiếng Việt và cấu hình môi trường (Tùy chọn)
Chạy một lần trong `webapp_v2/`: `python -m tools.setup_ocr` (tải khoảng 12 MB, cần cho OCR ảnh không có QR). Cấu hình khác: sao chép `.env.example` thành `.env` trong `webapp_v2/`:
```bash
# TESSDATA_DIR=data/tessdata
# Tùy chọn: origin được phép gọi API từ trình duyệt (CORS), mặc định chỉ localhost
# CORS_ORIGINS=https://hoso.example.com
```

### 4. Khởi chạy WebApp V2
```bash
cd webapp_v2
python main.py
```
Ứng dụng sẽ chạy tại địa chỉ: `http://localhost:8002`

### 5. Chạy kiểm thử tự động
```bash
cd webapp_v2
pip install -r requirements.txt -r requirements-dev.txt
pytest
```
Bộ test (`webapp_v2/tests/`) gồm:
- **Sinh hồ sơ end-to-end** cho mọi bộ mẫu (1 và 3 thành viên): không sót placeholder, không có `None`, mọi dữ liệu nhập đều xuất hiện trong file Word.
- **Kiểm tra cấu trúc `_schema.json`** (định dạng `steps`, kiểu trường hợp lệ, `has_nganh` khớp với bảng mã ngành).
- **Bảo mật API**: path traversal, chèn mã template, CORS.
- **Giao diện (Playwright)**: chống XSS, kiểm tra trường bắt buộc. Tự bỏ qua nếu chưa cài trình duyệt; để chạy:
  `pip install playwright && python -m playwright install chromium`.

- **Ảnh chụp chuẩn** (`tests/golden/`): toàn bộ chữ trong hồ sơ của 24 bộ mẫu với dữ liệu cố định; mọi thay đổi nội dung đều bị phát hiện. Khi cố ý thay đổi: `UPDATE_GOLDEN=1 pytest tests/test_golden_snapshots.py` rồi xem `git diff tests/golden/`.

**Quét bộ mẫu** trước khi thêm/sửa file Word:
```bash
cd webapp_v2
python -m tools.template_lint                 # mọi bộ mẫu
python -m tools.template_lint tam-dung-cong-ty-tnhh-1-tv --strict
```
Công cụ báo lỗi cú pháp Jinja, dấu `{{ }}` không cân, biến không có nguồn dữ liệu, placeholder kiểu cũ và dữ liệu cá nhân bị viết cứng. Định dạng `_schema.json` xem [`webapp_v2/docs/schema-v2.md`](webapp_v2/docs/schema-v2.md). Mỗi bộ mẫu có `id` ASCII cố định (vd `tang-von-cong-ty-tnhh-2-tv`), dùng được thay tên thư mục khi gọi API.

GitHub Actions (`.github/workflows/webapp-tests.yml`) tự quét bộ mẫu và chạy toàn bộ test mỗi khi `webapp_v2/` thay đổi.

> Khi thêm bộ mẫu mới: dùng định dạng `"steps"` trong `_schema.json` (xem các bộ có sẵn). Định dạng `"fields"` phẳng sẽ không hiển thị trên giao diện; có thể chuyển đổi bằng `python scripts_and_tools/migrate_flat_schemas.py`.

---

## 📁 Cấu Trúc Dự Án

```text
├── webapp_v2/                  # Mã nguồn chính WebApp V2 (FastAPI)
│   ├── main.py                 # Điểm khởi chạy server (Cổng 8002)
│   ├── config.py               # Cấu hình hệ thống & nạp .env
│   ├── routes/                 # API endpoints (Documents, MST, OCR, Templates)
│   ├── services/               # Nghiệp vụ xử lý Word, chuẩn hóa font, OCR
│   ├── templates/              # 19 bộ mẫu Docx chuẩn hóa Jinja2 + _schema.json
│   └── static/                 # Giao diện người dùng (HTML, CSS Ember theme, JS)
├── scripts_and_tools/          # Script dựng / sửa mẫu Word (xem scripts_and_tools/README.md)
├── ma_nganh_nghe.json          # Cơ sở dữ liệu danh mục ngành nghề kinh doanh Việt Nam
├── requirements.txt            # Danh sách thư viện Python
└── README.md                   # Tài liệu hướng dẫn sử dụng
```

---

## 📄 Bản Quyền & Giấy Phép
Dự án được xây dựng phục vụ công tác nghiệp vụ pháp lý doanh nghiệp.
