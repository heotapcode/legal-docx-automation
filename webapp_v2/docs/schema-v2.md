# Đặc tả `_schema.json` v2

Mỗi bộ mẫu hồ sơ là một thư mục trong `webapp_v2/templates/`, gồm các file Word (`.docx`) và một file `_schema.json` mô tả:

- **form nhập liệu**: các bước và các trường của wizard;
- **cách sinh file** ([v2]): file nào sinh khi nào, sinh lặp theo danh sách nào, xử lý gì sau khi điền.

Đặc tả máy đọc được nằm ở [`schemas/template-schema.json`](../schemas/template-schema.json) (JSON Schema 2020-12). Bộ test (`tests/test_schemas.py`) và công cụ quét mẫu (`tools/template_lint.py`, mã `E002`) kiểm tra mọi schema theo file này.

> **Lõi kiểm tra dữ liệu (Mục 9, bước 1).** `show_if`, `validate`, `rules` và các kiểu cũ (`person`, `person_list`, `transfer_list`) đã được cài đặt ở `services/schema_engine.py` (backend) và `static/js/engine/schema_engine.js` (trình duyệt), hai bản chạy chung ca kiểm thử `tests/engine_cases.json`. Đã nối (bước 2): API `/api/documents/generate` trả 422 kèm danh sách lỗi khi dữ liệu không hợp lệ, và wizard dùng chung lõi để chặn bước tiếp/tải hồ sơ. Hai bộ dùng wizard riêng (Chuyển nhượng 2 TV, Chuyển đổi 1TV→2TV) tạm chưa kiểm tra ở API cho tới khi chuyển sang bộ máy chung.
>
> **Trạng thái triển khai.** Các phần đánh dấu **[v2]** đã có trong đặc tả để thống nhất định dạng, nhưng wizard (`static/js/pages/wizard.js`) và `render_service.py` **chưa dùng tới**. Chúng sẽ được triển khai ở Mục 9 (bộ máy wizard chung). Hiện tại bộ mẫu thật chỉ nên dùng các kiểu trường wizard đang hỗ trợ (`tests/test_schemas.py::SUPPORTED_TYPES`).

---

## 1. Cấp gốc

| Khóa | Bắt buộc | Mô tả |
|---|---|---|
| `id` | ✔ | Mã ASCII cố định, vd `tang-von-cong-ty-tnhh-2-tv`. Dùng được thay tên thư mục trong API: `POST /api/documents/generate` với `"template_name": "<id>"`, `GET /api/templates/<id>/schema`. Không đổi `id` sau khi đã dùng. |
| `name` | ✔ | Trùng **chính xác** tên thư mục. |
| `display_name` | ✔ | Tên hiển thị trên giao diện. |
| `category` | | Nhóm thủ tục: Thành lập mới, Thay đổi, Tăng vốn, Giải thể… |
| `description` | | Mô tả ngắn. |
| `has_nganh` | | `true` nếu wizard có bước chọn mã ngành (bộ mẫu có bảng *Mã ngành / Tên ngành*). |
| `steps` | ✔ | Danh sách bước của wizard (mục 2). |
| `schema_version` | | [v2] `1` hoặc `2`. |
| `version` | | [v2] Phiên bản nội dung bộ mẫu, tăng mỗi lần xuất bản (Mục 10). |
| `legal_basis` | | [v2] Căn cứ pháp lý, vd số hiệu biểu mẫu theo thông tư hiện hành. |
| `effective_from` | | [v2] Ngày bắt đầu áp dụng, `YYYY-MM-DD`. |
| `documents` | | Quy tắc sinh file (mục 5). Không khai báo thì sinh mọi file `.docx` trong thư mục. |

Khóa không có trong bảng sẽ bị báo lỗi (`additionalProperties: false`), để bắt lỗi gõ sai như `requried`.

## 2. Bước (`steps[]`)

```json
{ "id": "ddpl", "title": "Người đại diện theo pháp luật", "fields": [ ... ],
  "show_if": { "field": "ddpl_changed", "equals": true } }
```

| Khóa | Bắt buộc | Mô tả |
|---|---|---|
| `id` | ✔ | Chữ thường, số, `_`. |
| `title` | ✔ | Tiêu đề bước. |
| `fields` | ✔ | Ít nhất 1 trường. |
| `description` | | Ghi chú dưới tiêu đề. |
| `show_if` | | Chỉ hiện bước khi điều kiện đúng (mục 4). |

## 3. Trường (`fields[]`)

| Khóa | Mô tả |
|---|---|
| `key` ✔ | Tên biến, cũng là tên dùng trong mẫu Word: `{{ key }}`. Chữ thường, số, `_`. |
| `label` ✔ | Nhãn hiển thị. |
| `type` ✔ | Xem bảng kiểu bên dưới. |
| `required` | Bắt buộc nhập. Wizard chặn bước tiếp theo và nút tải hồ sơ khi còn trống. |
| `placeholder` | Gợi ý mờ trong ô nhập. |
| `ocr` | Cho phép quét ảnh CCCD/VNeID (kiểu `person`, `person_list`). |
| `min` / `max` | Số phần tử tối thiểu / tối đa ([v2] `max`) của danh sách. |
| `extra_fields` | Trường thêm cho mỗi người trong `person_list` (vd vốn góp, tỷ lệ). |
| `options` | Danh sách `{value, label}` cho `checkbox_group`, `select`. |
| `options_source` | `select` lấy lựa chọn từ danh mục dùng chung do API cung cấp. Hiện có `tinh_thanh` (34 tỉnh/thành phố, `GET /api/dia-ban/tinh-thanh`). |
| `help` | [v2] Ghi chú dưới ô nhập. |
| `default` | Giá trị chọn sẵn (wizard hiện dùng cho `select`; các kiểu khác: [v2]). **Không dùng dữ liệu người thật.** |
| `item` | [v2] Các trường con của `list` / `group`. |
| `options_from` | [v2] `select` lấy lựa chọn từ một `list` khác. |
| `show_if` | Chỉ hiện trường khi điều kiện đúng (ẩn/hiện ngay khi nhập; trường ẩn không bị kiểm tra). |
| `validate` | [v2] Ràng buộc giá trị (mục 3.2). |
| `rules` | [v2] Ràng buộc trên cả danh sách (mục 3.3). |

### 3.1. Kiểu trường

| Kiểu | Wizard hiện tại | Ghi chú |
|---|---|---|
| `text`, `number`, `phone`, `email` | ✔ | |
| `money` | ✔ | Tự định dạng `1,000,000` và hiện số tiền bằng chữ. |
| `mst_lookup` | ✔ | Ô MST kèm nút tra cứu. |
| `person` | ✔ | Nhóm cố định: sinh các biến `<key>_ho_ten`, `<key>_so_cccd`, `<key>_ngay_sinh`, `<key>_gioi_tinh`, `<key>_dia_chi_*`. |
| `person_list` | ✔ | Danh sách người, dữ liệu gửi lên ở `thanh_vien`. |
| `transfer_list` | ✔ | Danh sách giao dịch chuyển nhượng (`chuyen_nhuong`). |
| `checkbox_group` | ✔ | Bắt buộc có `options`. |
| `select` | ✔ | Danh sách sổ xuống. Cần `options`, `options_source` hoặc [v2] `options_from`. |
| `date`, `cccd`, `percent`, `address` | ✔ | Bộ vẽ form chung (`static/js/engine/form_renderer.js`). `date` nhập DD/MM/YYYY; `cccd` 12 chữ số. |
| `list` | ✔ | Danh sách lặp tổng quát, bắt buộc có `item`; có nút Thêm/Xóa, giới hạn `min`/`max`; dữ liệu gửi lên là mảng ở `data[key]`. |
| `group` | [v2] | Bắt buộc có `item`. Thay dần `person` bằng định nghĩa tường minh. |

### 3.2. `validate` [v2]

```json
{ "key": "von_moi_so", "type": "money", "validate": { "greater_than": "von_cu_so", "message": "Vốn mới phải lớn hơn vốn cũ" } }
{ "key": "ngay_sinh", "type": "date", "validate": { "min_age": 18 } }
{ "key": "so_cccd", "type": "cccd", "validate": { "pattern": "^\\d{12}$" } }
```
Khóa hỗ trợ: `pattern`, `message`, `min`, `max`, `min_age`, `greater_than`, `less_than`.

### 3.3. `rules` trên danh sách [v2]

```json
"rules": [
  { "sum": "ty_le", "equals": 100, "message": "Tổng tỷ lệ phải bằng 100%" },
  { "sum": "von_gop", "equals": "von_dieu_le_so" },
  { "unique": "so_cccd" }
]
```
`equals` là số, hoặc tên một trường khác để so với giá trị của trường đó.

## 4. Điều kiện (`show_if`, `when`) [v2]

```json
{ "field": "thay_doi", "contains": "A2" }
{ "field": "loai_hinh", "in": ["tnhh_2tv", "cp"] }
{ "field": "ddpl_changed", "equals": true }
{ "all": [ { "field": "thay_doi", "contains": "A3" }, { "field": "loai_hinh", "equals": "tnhh_2tv" } ] }
{ "any": [ ... ] }
```
Toán tử: `equals`, `not_equals`, `contains` (danh sách chứa giá trị), `in`, `not_empty`; kết hợp bằng `all` / `any`. Mỗi điều kiện dùng **đúng một** trong `field`, `all`, `any`.

## 5. Quy tắc sinh file (`documents[]`)

Đã dùng thật (Mục 9, bước 3): `render_documents` đọc khối này thay cho các điều kiện viết cứng theo tên thư mục.
Cả 24 bộ mẫu đều khai báo; khi đã khai báo thì phải liệt kê **đủ** mọi file `.docx` (test và công cụ quét báo `E003` nếu thiếu/thừa).

```json
"documents": [
  { "file": "01. Thông báo.docx" },
  { "file": "02. Thông báo thay đổi người đại diện.docx", "when": { "field": "ddpl_changed", "equals": true } },
  { "file": "09. Xác nhận góp vốn 1.docx", "repeat_for": "tv_moi", "repeat_with": "xac_nhan_gop_von" },
  { "file": "10. Xác nhận góp vốn 2.docx", "when": { "field": "tv_moi", "not_empty": false } },
  { "file": "03. Danh sách thành viên.docx", "post": ["fill_member_table"] }
]
```

| Khóa | Mô tả |
|---|---|
| `file` ✔ | Tên file `.docx` trong thư mục bộ mẫu. |
| `when` | Chỉ sinh khi điều kiện (mục 4) đúng trên **dữ liệu quy tắc**: ngữ cảnh đã chuẩn hóa cộng `tv_moi` (danh sách thành viên), `chuyen_nhuong` (danh sách giao dịch), `ddpl_changed` (có đổi người đại diện, mặc định `true`). |
| `repeat_for` + `repeat_with` | Sinh một file cho mỗi phần tử của `tv_moi` hoặc `chuyen_nhuong`; `repeat_with` là hàm dựng ngữ cảnh và tên file: `xac_nhan_gop_von`, `giao_dich_chuyen_nhuong`, `giao_dich_chuyen_doi`, `giay_chung_nhan_gop_von`. Danh sách rỗng -> điền một lần như bình thường. |
| `post` | Xử lý sau khi điền, theo thứ tự, chỉ chạy khi có thành viên: `fill_member_table`, `fill_member_table_tang_von`, `fill_founders_table`, `fill_cshhl_table`, `fill_qd_chuyen_doi`, `fill_dieu_le_chuyen_doi`, `fill_dieu_le_tlm_2tv`, `fill_dieu_le_tlm_cp`, `fill_bbh_tang_von_cp`, `fill_bbh_giam_von_cp`, `fill_bbh_tang_von_2tv`, `fill_bbh_giai_the_cp`. |
| `output`, `item_alias` | [v2] Dự phòng cho sinh lặp tổng quát (chưa dùng). |

Bảng mã ngành luôn được điền vào mọi file khi có danh sách ngành, không cần khai báo.
Thêm hàm lặp / hàm xử lý mới: viết trong `services/document_rules.py` (`REPEATERS`, `HOOKS`) và thêm tên vào `schemas/template-schema.json` (test kiểm tra hai nơi khớp nhau).

## 6. Quy ước cho file Word

- Chỉ dùng cú pháp Jinja của docxtpl: `{{ bien }}`, `{%p if ... %}` … `{%p endif %}` cho đoạn văn theo điều kiện, `{%tr for ... %}` cho dòng bảng lặp.
- Không viết cứng dữ liệu người thật (CCCD, số điện thoại, email); công cụ quét báo `W030`.
- Mỗi biến trong mẫu phải có nguồn dữ liệu (trường trong schema hoặc biến do backend tính); nếu không, công cụ quét báo `W021` vì biến đó luôn in ra trống.

## 7. Kiểm tra trước khi commit

```bash
cd webapp_v2
python -m tools.template_lint <id-hoặc-thư-mục>   # E = lỗi phải sửa, W = cảnh báo nên xem
pytest tests/test_schemas.py tests/test_template_lint.py
pytest tests/test_golden_snapshots.py             # nội dung hồ sơ có đổi không
```
Nếu cố ý thay đổi nội dung hồ sơ: `UPDATE_GOLDEN=1 pytest tests/test_golden_snapshots.py`, rồi xem `git diff tests/golden/`.
