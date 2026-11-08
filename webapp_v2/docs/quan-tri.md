# Trang quản trị mẫu (Mục 10)

Trang `#/admin` dành cho người làm nghiệp vụ, để cập nhật mẫu khi luật thay đổi mà không cần lập trình viên.

| Bước | Nội dung | Trạng thái |
|---|---|---|
| 10.1 | Đăng nhập quản trị | ✅ |
| 10.2 | Tải mẫu nháp, quét mẫu, sinh thử, xuất bản (API + giao diện `#/admin`) | ✅ |
| 10.3 | Tự gợi ý schema từ tên biến trong mẫu | ⏳ |
| 10.4 | Phiên bản mẫu, quay lại bản cũ (API + giao diện) | ✅ |
| 10.5 | Chặn xuất bản khi quét mẫu còn lỗi | ✅ |

## Cập nhật một bộ mẫu

Trên trang `#/admin`: chọn bộ mẫu → **Quản lý** → **Tạo bản nháp**, rồi làm theo 4 mục trên màn hình bản nháp.

1. **Tạo bản nháp** từ bộ mẫu đang dùng. Bản nháp là bản sao, sửa thoải mái không ảnh hưởng người đang tạo hồ sơ.
2. **Sửa bản nháp:** tải lên file Word mới (thay file cùng tên hoặc thêm file), xóa file, sửa `_schema.json` (không được đổi `id`, `name`).
   File tải lên phải là `.docx` thật, tối đa 5 MB, không chứa macro.
3. **Quét mẫu:** báo lỗi cú pháp, biến chưa có trong schema, file chưa khai báo trong `documents`, dữ liệu cá nhân viết cứng...
4. **Sinh thử:** tải về bộ hồ sơ sinh từ bản nháp với dữ liệu mẫu để xem trước.
5. **Xuất bản** (bắt buộc ghi chú; tùy chọn căn cứ pháp lý, ngày hiệu lực). Bị chặn nếu:
   - quét mẫu còn **lỗi** (cảnh báo không chặn);
   - bộ mẫu đã được người khác xuất bản sau khi tạo bản nháp này (tạo bản nháp mới để không ghi đè).

Mỗi lần xuất bản lưu thành một **phiên bản** (số tăng dần, ghi `version` vào `_schema.json`). Lần đầu tiên, nội dung đang có
(bản trong git) được lưu tự động làm phiên bản 1. **Quay lại bản cũ** tạo một phiên bản mới có nội dung của bản cũ, lịch sử không bị xóa.

| Thư mục | Nội dung |
|---|---|
| `templates/<tên>/` | Bộ mẫu đang dùng |
| `data/template_drafts/<mã>/` (`TEMPLATE_DRAFTS_DIR`) | Bản nháp |
| `data/template_versions/<id>/v<n>/` (`TEMPLATE_VERSIONS_DIR`) | Nội dung đầy đủ của từng phiên bản |

> **Lưu ý khi triển khai:** xuất bản ghi trực tiếp vào `templates/`. Nếu máy chủ chạy từ bản git, các thay đổi này cần được
> sao lưu (hoặc commit lại) để không mất khi cập nhật mã nguồn; thư mục `data/template_versions/` cũng cần được sao lưu.

## Tạo tài khoản

Tài khoản chỉ tạo được trên máy chủ, bằng dòng lệnh (chạy trong thư mục `webapp_v2`):

```bash
python -m tools.admin_user create quantri
```

Lệnh hỏi mật khẩu hai lần, không hiện khi gõ, tối thiểu 10 ký tự. Các lệnh khác:

| Lệnh | Việc |
|---|---|
| `python -m tools.admin_user passwd <tên>` | Đổi mật khẩu; mọi phiên đang đăng nhập của tài khoản bị đăng xuất. |
| `python -m tools.admin_user disable <tên>` | Khóa tài khoản và đăng xuất ngay. |
| `python -m tools.admin_user enable <tên>` | Mở khóa. |
| `python -m tools.admin_user list` | Danh sách tài khoản. |

## Cấu hình (biến môi trường hoặc file `.env`)

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `ADMIN_DB_PATH` | `data/admin.sqlite3` | File SQLite lưu tài khoản, phiên, nhật ký (đã có trong `.gitignore`, **không commit**). |
| `ADMIN_SESSION_HOURS` | `12` | Thời hạn một phiên đăng nhập. |
| `ADMIN_COOKIE_SECURE` | `0` | Đặt `1` khi chạy qua HTTPS để cookie phiên chỉ gửi qua HTTPS. |

## An toàn

- **Mật khẩu:** băm bằng scrypt có muối ngẫu nhiên; CSDL không chứa mật khẩu gốc.
- **Phiên đăng nhập:** mã ngẫu nhiên trong cookie `HttpOnly` (JavaScript không đọc được) và `SameSite=Strict`. CSDL chỉ lưu mã băm SHA-256 của mã phiên, nên người có file CSDL cũng không dùng được để đăng nhập.
- **Dò mật khẩu:** sai 5 lần trong 15 phút thì tên đăng nhập đó bị tạm khóa 15 phút. Sai tên đăng nhập và sai mật khẩu báo cùng một thông báo, nên không dò được tên tài khoản.
- **Giả mạo yêu cầu (CSRF):** mọi yêu cầu thay đổi dữ liệu phải có header `X-Requested-With: nac-admin`. Trang web khác không gửi được header này, vì CORS chỉ cho phép `Content-Type`.
- **Nhật ký:** tạo tài khoản, đổi mật khẩu, khóa/mở khóa, đăng nhập đều được ghi vào bảng `audit_log`.
