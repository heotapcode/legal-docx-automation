# Trang quản trị mẫu (Mục 10)

Trang `#/admin` dành cho người làm nghiệp vụ, để cập nhật mẫu khi luật thay đổi mà không cần lập trình viên.

| Bước | Nội dung | Trạng thái |
|---|---|---|
| 10.1 | Đăng nhập quản trị | ✅ |
| 10.2 | API tải mẫu nháp, quét mẫu, sinh thử, xuất bản | ⏳ |
| 10.3 | Tự gợi ý schema từ tên biến trong mẫu | ⏳ |
| 10.4 | Phiên bản mẫu, quay lại bản cũ | ⏳ |
| 10.5 | Chặn xuất bản khi quét mẫu còn lỗi | ⏳ |

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
