# Trang quản trị mẫu (Mục 10)

Trang `#/admin` dành cho người làm nghiệp vụ, để cập nhật mẫu khi luật thay đổi mà không cần lập trình viên.

| Bước | Nội dung | Trạng thái |
|---|---|---|
| 10.1 | Đăng nhập quản trị | ✅ |
| 10.2 | Tải mẫu nháp, quét mẫu, sinh thử, xuất bản (API + giao diện `#/admin`) | ✅ |
| 10.3 | Tự gợi ý trường cho schema từ tên biến trong mẫu | ✅ |
| 10.4 | Phiên bản mẫu, quay lại bản cũ (API + giao diện) | ✅ |
| 10.5 | Chặn xuất bản khi quét mẫu còn lỗi | ✅ |

## Cập nhật một bộ mẫu

Trên trang `#/admin`: chọn bộ mẫu → **Quản lý** → **Tạo bản nháp**, rồi làm theo 4 mục trên màn hình bản nháp.

1. **Tạo bản nháp** từ bộ mẫu đang dùng. Bản nháp là bản sao, sửa thoải mái không ảnh hưởng người đang tạo hồ sơ.
2. **Sửa bản nháp:** tải lên file Word mới (thay file cùng tên hoặc thêm file), xóa file, sửa `_schema.json` (không được đổi `id`, `name`).
   File tải lên phải là `.docx` thật, tối đa 5 MB, không chứa macro.
   Thêm biến mới vào mẫu Word (vd `{{ ngay_ky_hop_dong }}`) thì bấm **Gợi ý trường còn thiếu**: hệ thống đọc các biến
   chưa có ô nhập và đoán kiểu theo tên (`<x>_ho_ten`, `<x>_so_cccd`... gộp thành một người `<x>`; `ngay_...` là ngày;
   `..._so_cccd` là CCCD; `von_..._so`, `phi_..._so` là tiền; `ty_le` là phần trăm; còn lại là chữ). Chọn trường rồi
   **Thêm vào cấu hình**: các trường vào bước "Thông tin bổ sung"; sửa nhãn trong ô cấu hình nếu cần.
   Dòng lệnh tương đương: `python -m tools.schema_suggest "templates/<tên bộ mẫu>"`.
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

## Người nhận ủy quyền (Bên B trong Giấy ủy quyền)

Trang `#/admin` → **Cấu hình dùng chung** → **Người nhận ủy quyền**: sửa họ tên, giới tính, ngày sinh, số định danh,
địa chỉ, điện thoại, thư điện tử rồi **Lưu**. Có hiệu lực ngay cho mọi bộ hồ sơ tạo sau đó (mọi Giấy ủy quyền dùng chung
các biến `{{ uq_ho_ten }}`, `{{ uq_so_cccd }}`...). Giá trị mặc định nằm ở `data/nguoi_nhan_uy_quyen.json`; giá trị đã sửa
lưu trong CSDL quản trị (`ADMIN_DB_PATH`), cần sao lưu cùng CSDL này.

## Khách tiềm năng và kinh doanh

Khách bấm tải hồ sơ phải để lại họ tên, số Zalo, vai trò (chủ doanh nghiệp / kế toán) và đánh dấu ô đồng ý lưu thông
tin, rồi chọn **Nhờ nộp trọn gói** hoặc **Tự nộp: tải hồ sơ miễn phí**. Khi đó:

- Khách được lưu vào CSDL quản trị: họ tên, số Zalo, vai trò, thủ tục, tên doanh nghiệp, số thành viên, gói nên chào,
  điểm ưu tiên (0–100), nguồn (`utm_*`, `ref` trên đường dẫn), câu đồng ý khách đã đánh dấu. **Không lưu** CCCD, địa chỉ
  hay dữ liệu hồ sơ.
- File .zip có thêm tờ **00. Hướng dẫn nộp hồ sơ và bảng giá dịch vụ** (các bước còn phải làm theo thủ tục, gói nên chào,
  cam kết, số Zalo).
- Email báo khách mới được gửi tới địa chỉ đặt ở trang quản trị (cần cấu hình `SMTP_*`, xem bảng dưới).

**Khách chọn Nhờ nộp trọn gói** (quyết định 14/11/2026):

1. Chọn gói (gói hợp thủ tục đứng đầu, có giá và tiền cọc) và cách gửi hồ sơ đã ký: **scan / chụp gửi qua Zalo** (mặc
   định) hoặc **gửi bản giấy qua bưu điện** tới địa chỉ nhận hồ sơ (phương án dự phòng).
2. Tải hồ sơ. Khách được cấp **mã hồ sơ** `HS0001`… Màn hình sau khi tải hiện **mã QR VietQR** đặt cọc (mặc định 50% giá
   gói, phần còn lại thu khi có kết quả): quét bằng ứng dụng ngân hàng là có sẵn số tiền và nội dung `HS0001 <số Zalo>`.
   Gói "Báo giá theo hồ sơ" không có QR, khách nhắn Zalo để được báo giá.
3. Tờ hướng dẫn trong file .zip ghi: ký bút mực xanh, không cần đóng dấu; ai ký văn bản nào; cách gửi hồ sơ đã ký; số
   tiền cọc và nội dung chuyển khoản.

Đối chiếu tiền về: nội dung chuyển khoản có mã hồ sơ, tìm mã đó ở cột **Hình thức, điểm, gói, đặt cọc** rồi đổi trạng
thái sang **Đã nhận cọc**. Mã QR tạo ngay trên máy chủ (thư viện `segno`), không gửi thông tin ra dịch vụ ngoài.

Trang `#/admin` → **Khách tiềm năng**: danh sách khách mới nhất trước, số Zalo bấm được; đổi trạng thái (Mới → Đã nhắn →
Đã báo giá → Đã nhận cọc → Đã mua → Đã ký kế toán / Không mua), ghi doanh thu, ghi chú; **Xóa** khi khách yêu cầu xóa dữ liệu.

Trang `#/admin` → **Cấu hình dùng chung** → **Kinh doanh**: tên đơn vị, số Zalo, email nhận báo, câu cam kết, thời gian
lưu thông tin khách, tỷ lệ đặt cọc, địa chỉ nhận hồ sơ giấy, **tài khoản nhận cọc** (ngân hàng, số tài khoản, chủ tài
khoản in hoa không dấu), bảng giá các gói. Giá trị mặc định ở `data/kinh_doanh.json` (tài khoản ở đó là **tài khoản demo**
`0000000000`: phải sửa thành tài khoản thật trước khi chạy thật).

### Trang giới thiệu và Google Analytics (14/11/2026)

- **Địa chỉ:** `/` là trang giới thiệu (máy chủ dựng sẵn để Google đọc được: bảng giá, các thủ tục, hỏi đáp). Ứng dụng tạo
  hồ sơ ở `/app#/wizard`, trang quản trị ở `/app#/admin`. Link cũ `/#/wizard`, `/#/admin` vẫn chạy (tự chuyển sang `/app`).
- **Nội dung đổi theo trang quản trị:** bảng giá, tiền cọc, số Zalo, câu cam kết, địa chỉ nhận hồ sơ, tên đơn vị. Câu chữ
  cố định (tiêu đề, các bước, hỏi đáp) ở `pages/trang_chu.html` và `services/trang_chu.py` (hàm `faq`).
- **Bấm một thủ tục** trên trang giới thiệu mở thẳng form thủ tục đó (`/app#/wizard?t=<mã bộ mẫu>`): dùng làm link quảng cáo
  cho từng thủ tục.
- **Tên miền:** đặt `SITE_URL=https://<tên miền>` trong `.env` để đường dẫn chuẩn và `sitemap.xml` đúng tên miền. Có sẵn
  `/robots.txt`, `/sitemap.xml` (khai báo trong Google Search Console).
- **Google Analytics 4:** tạo luồng dữ liệu web trong Google Analytics, lấy **Mã đo lường** `G-…`, dán vào
  **Kinh doanh → Mã Google Analytics 4**. Để trống thì không nạp gì. Sự kiện gửi lên (không kèm họ tên, số điện thoại,
  dữ liệu hồ sơ):

  | Sự kiện | Khi nào | Tham số |
  |---|---|---|
  | `page_view` | Mỗi trang (trang quản trị không tính) | |
  | `cta_click` | Bấm nút "Tạo hồ sơ" / một thủ tục trên trang giới thiệu | `vi_tri`, `template_id` |
  | `begin_form` | Chọn thủ tục, bắt đầu điền | `template_id` |
  | `tai_ho_so` | Tải bộ hồ sơ thành công | `template_id` |
  | `generate_lead` | Tải hồ sơ kèm thông tin khách | `template_id`, `hinh_thuc` (tu_nop / nho_nop), `goi`, `cach_gui` |
  | `contact_zalo` | Bấm nút nhắn Zalo | `vi_tri` |

  Trong Google Analytics: **Quản trị → Sự kiện**, đánh dấu `generate_lead` (và `contact_zalo`) là **sự kiện chính** để
  đếm chuyển đổi; xem phễu ở **Khám phá → Khám phá phễu** với các bước `page_view → begin_form → generate_lead`.

### Đối tác giới thiệu và hoa hồng (14/11/2026)

Trang `/app#/admin` → **Đối tác giới thiệu, hoa hồng**:

1. **Thêm đối tác:** mã (dùng trong link, chữ thường không dấu, vd `ketoan-an`), tên, số Zalo, tỷ lệ hoa hồng (% doanh
   thu), ghi chú. Mã không đổi được sau khi tạo (để không mất liên kết với khách cũ).
2. **Bấm Chép link** gửi cho đối tác: `https://<tên miền>/?ref=ketoan-an`. Muốn dẫn thẳng vào một thủ tục:
   `https://<tên miền>/app#/wizard?t=<mã bộ mẫu>&ref=ketoan-an`.
3. Khách mở link rồi tải hồ sơ **trong 30 ngày** (cùng trình duyệt) thì được tính cho đối tác; khách mở link của đối tác
   khác sau đó thì tính cho đối tác mới nhất. Email báo khách mới ghi tên đối tác; danh sách khách hiện "Đối tác: <tên>".
4. **Hoa hồng** = tỷ lệ % × tổng **doanh thu** anh ghi ở các khách của đối tác (trang Khách tiềm năng). Khi trả tiền cho
   đối tác, cộng dồn vào ô **Đã trả**; cột **Còn phải trả** tự tính. Bỏ đánh dấu **Đang hợp tác** khi ngừng (số liệu cũ vẫn giữ).
5. **Mã chưa có trong danh sách:** khách vào bằng `?ref=` lạ (gõ sai, đối tác chưa đăng ký) hiện ở cuối trang; bấm vào mã
   để thêm đối tác với mã đó, số khách cũ được tính luôn.

Gắn nguồn cho link quảng cáo hoặc đối tác: thêm `?utm_source=google&utm_campaign=mau-ho-so` hoặc `?ref=<mã đối tác>`
vào đường dẫn trang; nguồn hiện ở cột **Nguồn** của danh sách khách và trong email báo.

**Gửi email bằng Gmail:** tài khoản Gmail gửi bật xác minh 2 bước → Tài khoản Google → Bảo mật → **Mật khẩu ứng dụng** →
tạo một mật khẩu 16 ký tự, rồi điền vào file `.env` của máy chủ: `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=465`,
`SMTP_USER=<gmail gửi>`, `SMTP_PASSWORD=<mật khẩu ứng dụng>`; khởi động lại máy chủ. Chưa cấu hình thì khách vẫn được
lưu và hiện trên trang quản trị, chỉ không có email.

## Sao lưu

Xuất bản từ trang quản trị ghi thẳng vào `templates/` trên máy chủ, nên nội dung trên máy chủ có thể mới hơn git.
Chạy định kỳ (vd mỗi đêm bằng Task Scheduler / cron), trong thư mục `webapp_v2`:

```bash
python -m tools.backup                         # tạo data/backups/backup-YYYYmmdd-HHMMSS.zip, giữ 14 bản mới nhất
python -m tools.backup --keep 30 --dir "D:/SaoLuu"
```

File sao lưu gồm: `templates/`, `data/template_versions/`, CSDL quản trị (tài khoản, nhật ký, người nhận ủy quyền),
`data/inquiries.json`. Nên đặt `--dir` ở ổ đĩa khác hoặc thư mục được đồng bộ ra ngoài máy chủ.
Khôi phục: tắt máy chủ, giải nén, chép `templates/` và `data/` về đúng chỗ.

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
| `RATE_LIMIT_GENERATE` | `30` | Số lần sinh hồ sơ tối đa mỗi phút từ một địa chỉ IP (0 = tắt). Quá mức trả lỗi 429. |
| `RATE_LIMIT_OCR` | `20` | Số lần quét CCCD/VNeID tối đa mỗi phút từ một IP. |
| `RATE_LIMIT_INQUIRY` | `5` | Số lần gửi yêu cầu tư vấn tối đa mỗi phút từ một IP. |
| `LEAD_REQUIRED` | `1` | `1` = khách phải để lại họ tên, số Zalo và đồng ý trước khi tải hồ sơ. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | trống, `465` | Máy chủ gửi email báo khách mới (Gmail: `smtp.gmail.com`, mật khẩu ứng dụng). Trống = không gửi. **Không commit mật khẩu.** |
| `LOG_LEVEL` | `INFO` | Mức ghi log (`DEBUG`, `INFO`, `WARNING`, `ERROR`). Lỗi hệ thống được ghi kèm chi tiết vào log; người dùng chỉ thấy thông báo chung. |

## An toàn

- **Mật khẩu:** băm bằng scrypt có muối ngẫu nhiên; CSDL không chứa mật khẩu gốc.
- **Phiên đăng nhập:** mã ngẫu nhiên trong cookie `HttpOnly` (JavaScript không đọc được) và `SameSite=Strict`. CSDL chỉ lưu mã băm SHA-256 của mã phiên, nên người có file CSDL cũng không dùng được để đăng nhập.
- **Dò mật khẩu:** sai 5 lần trong 15 phút thì tên đăng nhập đó bị tạm khóa 15 phút. Sai tên đăng nhập và sai mật khẩu báo cùng một thông báo, nên không dò được tên tài khoản.
- **Giả mạo yêu cầu (CSRF):** mọi yêu cầu thay đổi dữ liệu phải có header `X-Requested-With: nac-admin`. Trang web khác không gửi được header này, vì CORS chỉ cho phép `Content-Type`.
- **Nhật ký:** tạo tài khoản, đổi mật khẩu, khóa/mở khóa, đăng nhập đều được ghi vào bảng `audit_log`.
