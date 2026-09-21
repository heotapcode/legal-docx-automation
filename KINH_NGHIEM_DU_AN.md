# 📋 KINH NGHIỆM DỰ ÁN: Telegram Bot Điền Thông Tin File Word

> **Mục đích**: Tài liệu này tổng hợp toàn bộ kiến trúc, quy trình làm việc, các bài học kinh nghiệm, và hướng dẫn mở rộng cho dự án "Điền thông tin file Word". Agent mới chỉ cần đọc file này là nắm được toàn bộ hệ thống.

---

## 1. TỔNG QUAN DỰ ÁN

### 1.1 Mục tiêu
Xây dựng Telegram Bot tự động điền thông tin vào các mẫu hồ sơ doanh nghiệp (file Word .doc/.docx) dựa trên dữ liệu người dùng nhập. Bot hỗ trợ:
- **Trích xuất thông tin từ ảnh VNeID** (Gemini Vision API)
- **Tra cứu mã ngành nghề** (Gemini AI + Google Search + file JSON local)
- **Tra cứu thông tin công ty từ MST** (API VietQR)
- **Tự động điền vào file Word** (win32com / COM Automation) và trả file ZIP cho người dùng qua Telegram

### 1.2 Thư mục gốc
```
c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word\
```

### 1.3 Các file chính

| File | Mô tả |
|---|---|
| `telegram_bot.py` | Code chính của bot (~807 dòng) |
| `folder_keys.json` | Cấu hình danh sách trường (placeholder) cho mỗi mẫu hồ sơ |
| `ma_nganh_nghe.json` | Bảng mã ngành nghề cấp 5 theo QĐ 27/2018 (chuẩn 2026) |
| `start_bot.bat` | Script khởi động bot (tự kill instance cũ trước) |
| `stop_bot.bat` | Script dừng bot hoàn toàn |
| `Mẫu */` | Các thư mục chứa file Word mẫu (template) |

---

## 2. KIẾN TRÚC HỆ THỐNG

### 2.1 Luồng xử lý chính

```
Người dùng gửi ảnh VNeID
  → Gemini Vision trích xuất thông tin cá nhân
  → Lưu vào context.user_data["ddpl_info"] hoặc ["tv2_info"]

Người dùng chọn mẫu hồ sơ (bấm nút trên Telegram)
  → Bot lấy danh sách trường từ folder_keys.json
  → Điền sẵn từ VNeID (nếu đã gửi ảnh)
  → Hiển thị form dạng <pre> để user copy/sửa/gửi lại

Người dùng gửi bảng thông tin đã điền
  → Parse text thành dict {KEY: VALUE}
  → Merge VNeID data + MST lookup (API VietQR) + Mã ngành
  → Copy thư mục mẫu → thay thế placeholder trong file Word
  → Nén ZIP → gửi file qua Telegram
```

### 2.2 Cấu trúc thư mục mẫu

Mỗi thư mục mẫu đặt tên theo format: `Mẫu {TÊN_MẪU}/`

Ví dụ:
```
Mẫu Thành lập mới công ty TNHH 2 TV/
  ├── 01. Giấy đề nghị.docx
  ├── 02. Điều lệ.doc
  ├── 03. Danh sách thành viên.docx
  ├── 04. Giấy ủy quyền.doc
  └── 05. Danh sách chủ sở hữu hưởng lợi.docx
```

Bot tự động detect thư mục bắt đầu bằng `"Mẫu "` và hiển thị trong danh sách chọn (hàm `get_templates()`).

### 2.3 Hệ thống Placeholder

Trong các file Word, thông tin cần thay thế được đánh dấu bằng placeholder dạng `[KEY_NAME]`.

**Quy tắc đặt tên placeholder:**

| Tiền tố | Ý nghĩa | Ví dụ |
|---|---|---|
| `TEN_CONG_TY_*` | Thông tin tên công ty | `[TEN_CONG_TY_VN]`, `[TEN_CONG_TY_NN]`, `[TEN_CONG_TY_VIET_TAT]` |
| `MA_SO_THUE` | Mã số thuế | `[MA_SO_THUE]` |
| `DIA_CHI_*` | Địa chỉ trụ sở công ty | `[DIA_CHI_SO_NHA]`, `[DIA_CHI_XA_PHUONG]`, `[DIA_CHI_TINH_THANH]` |
| `SDT_CONG_TY` | SĐT công ty | `[SDT_CONG_TY]` |
| `EMAIL_CONG_TY` | Email công ty | `[EMAIL_CONG_TY]` |
| `VON_DIEU_LE_*` | Vốn điều lệ | `[VON_DIEU_LE_SO]`, `[VON_DIEU_LE_CHU]` |
| `DDPL_*` | Người đại diện pháp luật | `[DDPL_HO_TEN]`, `[DDPL_NGAY_SINH]`, `[DDPL_SO_CCCD]`, `[DDPL_GIOI_TINH]`, `[DDPL_DIA_CHI_*]` |
| `DDPL_CU_*` | ĐDPL cũ (mẫu chuyển nhượng) | `[DDPL_CU_HO_TEN]`, `[DDPL_CU_SO_CCCD]` |
| `TV2_*` | Thành viên thứ 2 | `[TV2_HO_TEN]`, `[TV2_NGAY_SINH]`, `[TV2_SO_CCCD]`, `[TV2_GIOI_TINH]`, `[TV2_DIA_CHI_*]` |
| `TV2_VON_CU_*` | Vốn thành viên 2 | `[TV2_VON_CU_SO]`, `[TV2_VON_CU_CHU]` |
| `DDPL_VON_CU_*` | Vốn ĐDPL | `[DDPL_VON_CU_SO]`, `[DDPL_TY_LE]` |
| `NGUOI_DUOC_UY_QUYEN_*` | Người được ủy quyền | `[NGUOI_DUOC_UY_QUYEN_HO_TEN]`, `[NGUOI_DUOC_UY_QUYEN_CCCD]` |
| `NAM` | Năm | `[NAM]` |
| `SO_QUYET_DINH` | Số quyết định | `[SO_QUYET_DINH]` |
| `SO_GIAY_CHUNG_NHAN` | Số giấy chứng nhận | `[SO_GIAY_CHUNG_NHAN]` |

---

## 3. QUY TRÌNH CHUẨN HÓA MẪU MỚI

### 3.1 Các bước thực hiện

**Bước 1: Phân tích file mẫu gốc**
```python
# Dùng win32com quét toàn bộ file trong thư mục mẫu
# Lấy: nội dung text, danh sách bảng (headers), thông tin hardcode
import os, re, win32com.client

folder = r"đường_dẫn_thư_mục_mẫu"
word = win32com.client.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = False

for fname in os.listdir(folder):
    if fname.startswith("~") or not (fname.endswith(".doc") or fname.endswith(".docx")):
        continue
    doc = word.Documents.Open(os.path.join(folder, fname), ReadOnly=True)
    full_text = doc.Content.Text
    
    # Tìm placeholder đã có
    placeholders = re.findall(r'\[[A-Z][A-Z0-9_]+\]', full_text)
    
    # Xem cấu trúc bảng
    for i, table in enumerate(doc.Tables):
        try:
            row1 = [cell.Range.Text.strip().replace('\r\a','') for cell in table.Rows(1).Cells]
            print(f"Table {i+1}: {row1}")
        except:
            print(f"Table {i+1}: (lỗi đọc header - có thể có merged cells)")
    doc.Close(False)
word.Quit()
```

**Bước 2: Backup thư mục gốc**
```python
import shutil
shutil.copytree(src_folder, backup_folder)
```

**Bước 3: Xây dựng bảng thay thế (REPLACEMENTS)**

> ⚠️ **BÀI HỌC QUAN TRỌNG**: Thứ tự thay thế RẤT QUAN TRỌNG!
> - Thay thế chuỗi DÀI trước, chuỗi NGẮN sau
> - VD: `"Ấp 1, Xã Quang Minh, Hà Nội"` phải thay TRƯỚC `"Ấp 1"` và `"Hà Nội"`
> - Nếu không, sẽ bị thay thế lệch, tạo ra placeholder sai

```python
REPLACEMENTS = [
    # Thay chuỗi dài/cụ thể trước
    ("CÔNG TY TNHH NÔNG SẢN HÀ HUY", "[TEN_CONG_TY_VN]"),
    ("HA HUY AGRICULTURAL COMPANY LIMITED", "[TEN_CONG_TY_NN]"),
    # ...
    # Thay tên người, CCCD
    ("HOÀNG THỊ HÀ", "[DDPL_HO_TEN]"),
    ("001182057142", "[DDPL_SO_CCCD]"),
    # ...
    # Thay năm CUỐI CÙNG (vì "2025" xuất hiện trong CCCD, ngày tháng)
    ("2025", "[NAM]"),
]
```

**Bước 4: Chạy script thay thế**

Dùng `Word Find & Replace` qua COM API, iterate qua tất cả StoryRanges (bao gồm cả header/footer/textbox):

```python
for old_text, new_text in REPLACEMENTS:
    for story in doc.StoryRanges:
        while story:
            rng = story.Duplicate
            while True:
                rng.Find.ClearFormatting()
                rng.Find.Text = old_text
                rng.Find.Forward = True
                rng.Find.Wrap = 0  # wdFindStop
                rng.Find.MatchCase = True
                found = rng.Find.Execute()
                if not found: break
                rng.Text = new_text
                rng.HighlightColorIndex = 7  # wdYellow - tô vàng
                rng.Collapse(0)
            story = story.NextStoryRange
```

**Bước 5: Kiểm tra (verification)**
```python
# Quét lại file sau khi thay thế
# 1. Kiểm tra KHÔNG CÒN thông tin cũ
OLD_DATA = ["HOÀNG THỊ HÀ", "001182057142", ...]
sot = [x for x in OLD_DATA if x in full_text]
# 2. Kiểm tra CÓ placeholder mới
placeholders = re.findall(r'\[[A-Z][A-Z0-9_]+\]', full_text)
# 3. Kiểm tra tên placeholder ĐÚNG QUY TẮC (không thiếu dấu _)
```

**Bước 6: Cập nhật `folder_keys.json`**

Thêm entry cho mẫu mới (key = phần sau "Mẫu " trong tên thư mục):
```json
{
  "Tên mẫu (không có 'Mẫu ' ở đầu)": [
    "TEN_CONG_TY_VN",
    "MA_SO_THUE",
    "DDPL_HO_TEN",
    ...
  ]
}
```

> ⚠️ **BÀI HỌC**: Tên trường trong `folder_keys.json` PHẢI KHỚP CHÍNH XÁC với placeholder trong file Word. Nếu file Word có `[TV2_VON_CU_CHU]` thì folder_keys.json cũng phải có `TV2_VON_CU_CHU`, KHÔNG PHẢI `TV2_VON_CU_MOI` hay tên khác.

**Bước 7: Khởi động lại bot**

---

## 4. CÁC API SỬ DỤNG

### 4.1 Gemini Vision (đọc ảnh VNeID)
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent`
- **Mục đích**: Trích xuất họ tên, ngày sinh, CCCD, giới tính, địa chỉ từ ảnh chụp VNeID
- **Lưu ý**: Prompt phải rất cụ thể về cách tách địa chỉ (số nhà, xã/phường, tỉnh/thành)

### 4.2 Gemini AI + Google Search (tra mã ngành)
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`
- **Mục đích**: Tìm mã ngành nghề phù hợp từ mô tả người dùng
- **Cơ chế**: AI gợi ý mã ngành cũ → map sang bảng mã ngành 2026 (file `ma_nganh_nghe.json`)
- **Fallback**: Nếu AI không trả kết quả, dùng tìm kiếm local theo từ khóa (normalize tiếng Việt)
- **Lưu ý**: Phải dùng `"tools": [{"googleSearch": {}}]` để bật Google Search grounding

### 4.3 VietQR API (tra MST)
- **Endpoint**: `https://api.vietqr.io/v2/business/{MST}`
- **Mục đích**: Lấy tên công ty + địa chỉ trụ sở từ Mã Số Thuế
- **Trả về**: `{code: "00", data: {name, address, internationalName, shortName, status}}`
- **Lưu ý**: 
  - Cần gửi User-Agent header (giả lập trình duyệt) để không bị chặn
  - Timeout nên đặt 15s
  - Có cơ chế retry 3 lần
  - Địa chỉ trả về dạng chuỗi, cần split bằng dấu `,` để tách thành phần

---

## 5. XỬ LÝ FILE WORD (COM AUTOMATION)

### 5.1 Khởi tạo COM

```python
import pythoncom
import win32com.client

pythoncom.CoInitialize()  # BẮT BUỘC khi chạy trong thread khác
word = win32com.client.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = False
```

> ⚠️ **BÀI HỌC**: Nếu không gọi `pythoncom.CoInitialize()`, sẽ bị lỗi COM khi hàm `process_word_files` chạy trong async context.

### 5.2 Mở file với Retry

```python
doc = None
for attempt in range(5):
    try:
        doc = word.Documents.Open(
            path,
            ReadOnly=False,
            ConfirmConversions=False,  # QUAN TRỌNG cho file .doc
            Format=0
        )
        break
    except Exception as e:
        if attempt < 4:
            time.sleep(1)
        else:
            raise
```

> ⚠️ **BÀI HỌC**: Lỗi `-2147418111 'Call was rejected by callee'` xảy ra khi:
> - Word đang bận xử lý file khác
> - File `.doc` (định dạng cũ) cần thêm thời gian convert
> - Không có `ConfirmConversions=False` → Word hiện dialog xác nhận
> 
> **Giải pháp**: Retry 5 lần, delay 1s giữa mỗi lần.

### 5.3 Thay thế Placeholder qua StoryRanges

Phải iterate qua **tất cả StoryRanges** (không chỉ Content) vì placeholder có thể nằm trong:
- Header/Footer
- TextBox
- Footnotes

```python
for story in doc.StoryRanges:
    while story:
        rng = story.Duplicate
        # ... Find & Replace ...
        story = story.NextStoryRange
```

### 5.4 Điền Bảng Mã Ngành Nghề

Bảng "Ngành, nghề kinh doanh" có cấu trúc cố định:

| STT | Tên ngành | Mã ngành | Ngành nghề kinh doanh chính |

Cách xử lý:
1. Quét tất cả bảng trong document
2. Nhận dạng bảng đúng bằng cách kiểm tra header row chứa `"Mã ngành"` và `"Tên ngành"`
3. Xóa tất cả dòng từ row 2 trở đi
4. Thêm dòng mới cho mỗi mã ngành đã chọn
5. Đánh dấu `X` vào cột "Ngành nghề kinh doanh chính" cho dòng đầu tiên

> ⚠️ **BÀI HỌC**: 
> - **Merged cells** trong bảng Word gây lỗi `table.Rows(i)`. Phải bọc trong `try/except`.
> - Khi xóa rows, xóa **từ cuối lên** (row 2 trở đi) hoặc dùng vòng `while table.Rows.Count > 1`.

### 5.5 Tô Highlight Vàng

Tất cả vị trí được thay thế đều phải tô nền vàng (`HighlightColorIndex = 7`) để người dùng dễ kiểm tra và đối soát.

```python
rng.Text = val
rng.HighlightColorIndex = 7  # wdYellow
```

### 5.6 Dọn dấu phẩy thừa

Khi placeholder trống (user không điền), sẽ tạo ra chuỗi lỗi như `" ,"` hoặc `", ,"`. Cần dọn:
```python
for old, new in [(" ,", ","), (", ,", ","), (": ,", ": "), (":,", ": ")]:
    rng.Find.Execute(old, ..., new, 2)  # 2 = wdReplaceAll
```

---

## 6. CÁC LỖI HAY GẶP & CÁCH KHẮC PHỤC

### 6.1 `telegram.error.Conflict: terminated by other getUpdates request`
- **Nguyên nhân**: Có nhiều instance bot đang chạy cùng lúc
- **Khắc phục**: Chạy `stop_bot.bat` trước khi khởi động lại. Script này:
  ```bat
  taskkill /F /IM python.exe /T
  ```
  Hoặc trong PowerShell:
  ```powershell
  taskkill /F /IM python.exe /T 2>$null; Start-Sleep -Seconds 2
  ```

### 6.2 `-2147418111 'Call was rejected by callee'`
- **Nguyên nhân**: Word COM bận, đặc biệt với file `.doc` cũ
- **Khắc phục**: Thêm `pythoncom.CoInitialize()`, `ConfirmConversions=False`, retry 5 lần

### 6.3 Placeholder bị thiếu/sai tên
- **Nguyên nhân**: Tên trường trong `folder_keys.json` không khớp với placeholder trong file Word
- **Ví dụ thực tế**: 
  - File Word có `[TV2_VON_CU_CHU]` nhưng `folder_keys.json` ghi `TV2_VON_CU_MOI` → bot hỏi sai trường → user điền giá trị nhưng không thay thế được trong Word
  - Placeholder `[TV2DIA_CHI_SO_NHA]` thiếu dấu `_` → đúng phải là `[TV2_DIA_CHI_SO_NHA]`
- **Phòng tránh**: Sau khi chuẩn hóa, chạy script kiểm tra tên placeholder có đúng quy tắc không

### 6.4 Thông tin công ty không tự điền khi có MST
- **Nguyên nhân**: API VietQR timeout/bị chặn hoặc MST có khoảng trắng thừa
- **Khắc phục**: 
  - Thêm `User-Agent` header
  - `.strip().replace(" ", "")` cho MST
  - Hiển thị trạng thái "⏳ Đang tra cứu..." và "✅ Thành công" / "⚠️ Thất bại" để user biết

### 6.5 Thứ tự thay thế sai
- **Nguyên nhân**: Thay chuỗi ngắn trước chuỗi dài → phá hỏng chuỗi dài
- **Ví dụ**: Nếu thay `"Hà Nội"` trước `"Ấp 1, Xã Quang Minh, Hà Nội"`, sẽ tạo ra `"Ấp 1, Xã Quang Minh, [DIA_CHI_TINH_THANH]"` thay vì `"[DIA_CHI_SO_NHA], [DIA_CHI_XA_PHUONG], [DIA_CHI_TINH_THANH]"`
- **Phòng tránh**: Luôn thay chuỗi dài trước, đặc biệt khi có chuỗi lồng nhau

### 6.6 Năm "2025" bị thay vào giữa số CCCD
- **Nguyên nhân**: Thay "2025" quá sớm (trước khi thay CCCD)
- **Phòng tránh**: Thay CCCD trước, thay năm CUỐI CÙNG trong danh sách

---

## 7. DANH SÁCH MẪU ĐÃ CHUẨN HÓA

| STT | Mẫu | Số file | Trạng thái |
|---|---|---|---|
| 1 | Thành lập mới công ty TNHH 1 TV | 4 | ✅ |
| 2 | Thành lập mới công ty TNHH 2 TV | 6 | ✅ |
| 3 | Thành lập mới công ty Cổ Phần | 5 | ✅ |
| 4 | Thành lập mới địa điểm kinh doanh | 2 | ✅ |
| 5 | Tạm dừng công ty TNHH 1 TV | 3 | ✅ |
| 6 | Tạm dừng công ty TNHH 2 TV | 3 | ✅ |
| 7 | Tạm dừng công ty Cổ Phần | 3 | ✅ |
| 8 | Hoạt động lại trước thời hạn | 2 | ✅ |
| 9 | Giải thể công ty TNHH 1 TV | 6 | ✅ |
| 10 | Giải thể công ty TNHH 2 TV | 7 | ✅ |
| 11 | Giải thể công ty Cổ Phần | 6 | ✅ |
| 12 | Chấm dứt hoạt động địa điểm kinh doanh | 2 | ✅ |
| 13 | Cấp lại giấy đăng ký kinh doanh | 2 | ✅ |
| 14 | Chuyển nhượng công ty TNHH 1 TV | 8 | ✅ |
| 15 | Tăng vốn công ty TNHH 2TV | 7 | ✅ |
| 16 | Chuyển đổi loại hình 1TV sang 2 TV | 8 | ✅ |
| 17 | Tăng vốn công ty cổ phần | 5 | ⚠️ Chưa có trong folder_keys.json |

---

## 8. HƯỚNG DẪN MỞ RỘNG

### 8.1 Thêm mẫu hồ sơ mới

1. Tạo thư mục `Mẫu {Tên mẫu}/` chứa các file Word
2. Chạy script phân tích để tìm thông tin hardcode (xem Mục 3.1 Bước 1)
3. Chạy script chuẩn hóa thay thế thông tin → placeholder (Bước 3-4)
4. Kiểm tra kết quả (Bước 5)
5. Thêm entry vào `folder_keys.json` (Bước 6)
6. Khởi động lại bot

### 8.2 Thêm trường mới cho mẫu đã có

1. Mở file Word, thêm placeholder `[TEN_TRUONG_MOI]`
2. Thêm `TEN_TRUONG_MOI` vào danh sách trong `folder_keys.json`
3. Thêm `"TEN_TRUONG_MOI"` vào `possible_keys` trong hàm `process_word_files()` (line 115-134 trong telegram_bot.py)
4. Khởi động lại bot

### 8.3 Thêm nhân vật mới (VD: TV3, TV4...)

1. Thêm xử lý trong `build_vneid_prefilled()` (dòng 44-69)
2. Thêm merge logic trong `handle_message()` (dòng 653-685)
3. Thêm các placeholder tương ứng vào `possible_keys`
4. Chuẩn hóa file Word với placeholder `[TV3_*]`

### 8.4 File Giấy ủy quyền

> ⚠️ **LƯU Ý ĐẶC BIỆT**: Trong một số mẫu, người dùng muốn **cố định** thông tin người được ủy quyền (không dùng placeholder). Khi chuẩn hóa, cần hỏi người dùng trước: "File Giấy ủy quyền có cần thay thế thông tin người được ủy quyền không?"

---

## 9. THÔNG TIN KỸ THUẬT BỔ SUNG

### 9.1 Dependencies

```
python-telegram-bot
httpx
pywin32 (win32com)
pythoncom (đi kèm pywin32)
```

### 9.2 API Keys

| Service | Key Location |
|---|---|
| Telegram Bot Token | Dòng 15, `telegram_bot.py` |
| Gemini API Key | Dòng 16, `telegram_bot.py` |

### 9.3 Bot Commands

| Command | Mô tả |
|---|---|
| `/start` | Hiển thị danh sách mẫu hồ sơ |
| `/reset` | Xóa toàn bộ dữ liệu phiên làm việc |
| `/nganh [mô tả]` | Tra cứu mã ngành nghề |
| `🔄 Làm lại từ đầu` | Nút bấm = `/reset` + hướng dẫn |

### 9.4 User Data Context (Telegram)

| Key | Type | Mô tả |
|---|---|---|
| `selected_template` | str | Tên mẫu đang chọn |
| `ddpl_info` | dict | Thông tin ĐDPL từ VNeID |
| `tv2_info` | dict | Thông tin TV2 từ VNeID |
| `selected_ma_nganh` | str | Mã ngành đơn (legacy) |
| `selected_ma_nganh_list` | list[dict] | Danh sách mã ngành đã chọn |
| `nganh_results` | list | Kết quả tìm kiếm mã ngành |
| `waiting_nganh_choice` | bool | Đang chờ user chọn mã ngành |
| `vneid_target` | str | Ảnh VNeID tiếp theo sẽ lưu cho ai ("DDPL" hoặc "TV2") |

### 9.5 File ma_nganh_nghe.json

Cấu trúc mỗi entry:
```json
{"ma": "46201", "ten": "Bán buôn nông, lâm sản nguyên liệu (trừ gỗ, tre, nứa) và động vật sống"}
```
- Mã cấp 5 (5 chữ số) được dùng cho tra cứu
- File được build từ file Word `Danh sách mã ngành nghề 2026.docx` bằng script `build_nganh_json.py`

---

## 10. CHECKLIST KHI CHUẨN HÓA MẪU MỚI

- [ ] Đã backup thư mục gốc
- [ ] Đã phân tích toàn bộ file Word (text + bảng)
- [ ] Xác định đúng nhân vật nào = ĐDPL, TV2, người ủy quyền, etc.
- [ ] Hỏi user: File Giấy ủy quyền có cần placeholder không?
- [ ] Thay thế đúng thứ tự (dài → ngắn, CCCD trước năm)
- [ ] Kiểm tra không còn sót thông tin cũ
- [ ] Kiểm tra tên placeholder đúng quy tắc (có `_` phân cách)
- [ ] Tên trường trong `folder_keys.json` KHỚP CHÍNH XÁC với placeholder trong file Word
- [ ] Đã thêm trường vào `possible_keys` trong `process_word_files()` nếu là trường mới
- [ ] Khởi động lại bot và test thử

---

*Tài liệu cập nhật: 2026-06-19*
