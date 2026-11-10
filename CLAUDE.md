# Hướng dẫn cho agent làm việc trong repo này

Webapp sinh bộ hồ sơ pháp lý doanh nghiệp (.docx) từ dữ liệu nhập trên form. Người dùng là người làm nghiệp vụ, không
phải lập trình viên: trao đổi bằng tiếng Việt, nói kết quả trước, giải thích thuật ngữ kỹ thuật khi buộc phải dùng.

## Bản đồ

| Thư mục | Nội dung |
|---|---|
| `webapp_v2/` | Ứng dụng chính (FastAPI + giao diện tĩnh). Mọi lệnh dưới đây chạy trong thư mục này. |
| `webapp_v2/templates/<tên thủ tục>/` | Một thủ tục = các file Word có biến Jinja + `_schema.json` (form, điều kiện sinh file). |
| `webapp_v2/services/render_service.py` | Chuẩn hóa dữ liệu (`normalize_context`) và sinh hồ sơ (`render_documents`). File lớn, nhiều quy tắc cũ: sửa hẹp, chạy ảnh chụp chuẩn sau mỗi thay đổi. |
| `webapp_v2/services/schema_engine.py` + `static/js/engine/schema_engine.js` | Lõi kiểm tra dữ liệu, hai bản phải cùng hành vi (`tests/engine_cases.json` chạy cho cả hai). |
| `webapp_v2/services/document_rules.py` | Quy tắc riêng theo nghiệp vụ, gọi qua khóa `prepare`, `post`, `repeat_with` trong schema. |
| `webapp_v2/static/js/pages/wizard.js`, `engine/form_renderer.js` | Form nhập liệu. Kiểu trường mới thêm vào `form_renderer.js`, không thêm vào `wizard.js`. |
| `webapp_v2/tools/` | `template_lint` (quét mẫu), `schema_suggest`, `admin_user`, `setup_ocr`. |
| `webapp_v2/docs/` | `schema-v2.md` (đặc tả `_schema.json`), `them-thu-tuc-moi.md`, `muc8-bang-nghiep-vu.md`, `quan-tri.md`. |
| `scripts_and_tools/` | Script dựng / sửa mẫu Word (xem README trong đó). |
| `crm/` | Ứng dụng Node riêng, chưa có test và CI. Không sửa khi chưa được yêu cầu. |

## Lệnh thường dùng (trong `webapp_v2/`)

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m tools.template_lint                      # quét mọi bộ mẫu; lỗi E phải bằng 0
python -m tools.template_lint "templates/<tên>"    # quét một bộ
python -m pytest -q                                # toàn bộ, khoảng 5 phút
python -m pytest -q tests/test_golden_snapshots.py # ảnh chụp chuẩn nội dung hồ sơ
UPDATE_GOLDEN=1 python -m pytest -q tests/test_golden_snapshots.py -k "<id bộ mẫu>"   # cập nhật có chủ đích
python main.py                                     # chạy máy chủ
```

Test giao diện cần Chromium; trên máy đã cài sẵn thì đặt `PLAYWRIGHT_CHROMIUM_EXECUTABLE=<đường dẫn>`.
Sau khi cập nhật ảnh chụp chuẩn, luôn xem `git diff tests/golden`: chỉ bộ mẫu định sửa được phép thay đổi.

## Quy tắc bắt buộc

- **Không đưa dữ liệu người thật vào repo**: tên, số định danh, địa chỉ, điện thoại của khách không được nằm trong mẫu,
  test, script, ảnh chụp chuẩn hay mô tả PR. Hồ sơ đã điền người dùng gửi chỉ để đối chiếu; test dùng người giả
  (`conftest.sample_person`, "NGUYỄN VĂN THỬ…"). Ngoại lệ đã được duyệt: thông tin nhân viên nhận ủy quyền, lưu MỘT chỗ ở
  `webapp_v2/data/nguoi_nhan_uy_quyen.json` (sửa được trên trang quản trị). Mẫu Word dùng biến `{{ uq_ho_ten }}`,
  `{{ uq_so_cccd }}`, `{{ uq_sdt }}`…, không chép thông tin này vào file Word
  (`python scripts_and_tools/uy_quyen_dung_bien.py` thay giúp).
- **Không viết khóa bí mật vào mã nguồn** (đọc từ biến môi trường / `.env`); `tests/test_no_secrets.py` chặn việc này.
- **Câu chữ pháp lý do người dùng quyết định.** Không tự sửa nội dung văn bản; chỗ chưa rõ thì hỏi và ghi quyết định kèm
  ngày vào `webapp_v2/docs/`.
- Không viết lại lịch sử git. Mỗi việc một PR; chỉ merge khi người dùng nói "merge".
- Sửa `schema_engine.py` thì sửa cả `schema_engine.js` và thêm ca vào `tests/engine_cases.json`.
- Thêm khóa mới cho `_schema.json` thì cập nhật `schemas/template-schema.json` và `docs/schema-v2.md`.

## Bẫy đã gặp

- **docxtpl**: không viết `{}` trong thẻ `{%p ... %}` (bị đọc nhầm, báo "unknown tag 'p'"); dùng `dict()`.
  `{%p %}` / `{%tr %}` phải đứng riêng một đoạn / một dòng bảng.
- **Unicode**: file Word hay lưu chữ có dấu ở dạng tổ hợp. So sánh chuỗi lấy từ docx phải
  `unicodedata.normalize("NFC", ...)`.
- **Bảng ngành nghề**: sau khi điền, mọi bảng có cột "Tên ngành" + "Mã ngành" bị điền lại theo danh sách ngành đã chọn.
  Mẫu tự dựng bảng bằng `{%tr for n in ma_nganh %}` phải đặt `"fill_nganh_table": false` ở mục `documents`.
- **Kiểu `person`** sinh biến phẳng `<key>_ho_ten`, `<key>_so_cccd`, `<key>_ngay_sinh`, `<key>_gioi_tinh`,
  `<key>_dia_chi_so_nha|xa_phuong|tinh_thanh`. Danh sách `person_list` luôn gửi lên ở `thanh_vien`.
- **Ngày và địa danh**: `{{ noi_lap }}`, `{{ phong_dkkd }}`, `{{ ngay_lap }}`, `{{ ngay_lap_ngan }}` do
  `normalize_context` tạo từ `tinh_dang_ky` / `ngay_lap`. Cơ quan đăng ký hộ kinh doanh: `{{ <xã phường> | co_quan_hkd }}`.
- **Tiền**: `| money` ra `1,000,000`; `| so_thanh_chu` ra chữ. Muốn dấu chấm: `| money | replace(',', '.')`.
- **File chuyển từ .doc bằng LibreOffice** rồi lưu bằng python-docx có thể trùng `docProps/core.xml` (docxtpl cảnh báo
  "Duplicate name"); xem `dedupe_zip` trong `scripts_and_tools/build_ho_kinh_doanh.py`.
- **Dữ liệu mẫu cho test** sinh tự động từ schema (`services/sample_data.py`). Ô có `validate.pattern` cần giá trị mẫu
  hợp lệ ở đó, nếu không test sinh hồ sơ của bộ mẫu sẽ trả 422.
- **Xuất bản từ trang quản trị** ghi thẳng vào `templates/` trên máy chủ: nội dung trên máy chủ có thể mới hơn git.

## Quy ước đặt tên biến

`ten_cong_ty_vn`, `ma_so_thue`, `dia_chi_so_nha|xa_phuong|tinh_thanh` (trụ sở công ty), `ddpl_…` (người đại diện),
`chu_tich_…` (người ký quyết định), `von_dieu_le_so`, `von_cu_so`, `thanh_vien` (danh sách), `tinh_dang_ky`.
Hộ kinh doanh: `chu_ho_…`, `ten_hkd`, `hkd_dia_chi_…`, `hkd_sdt`, `von_kinh_doanh_so`, `thue_dia_chi_…`.
Thủ tục mới dùng lại tên có sẵn khi cùng ý nghĩa.

## Thêm thủ tục mới

Làm theo `webapp_v2/docs/them-thu-tuc-moi.md`.
