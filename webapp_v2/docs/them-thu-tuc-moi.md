# Quy trình thêm một thủ tục mới

Ví dụ mẫu để làm theo: bộ `Thành lập hộ kinh doanh` (PR #23) và script `scripts_and_tools/build_ho_kinh_doanh.py`.

## 1. Thu thập từ người làm nghiệp vụ

| Cần có | Ghi chú |
|---|---|
| File mẫu trống của từng văn bản (.docx; .doc/PDF thì chuyển sang .docx) | Là nguồn để dựng mẫu. |
| Ít nhất một hồ sơ đã điền | Chỉ để đối chiếu cách trình bày. **Không đưa vào repo** (dữ liệu người thật). |
| Danh sách văn bản trong bộ hồ sơ | Văn bản nào luôn có, văn bản nào theo điều kiện. |
| Ai ký, nơi nộp (tên cơ quan có đổi theo tỉnh/xã không) | |
| Có bước chọn mã ngành không | `has_nganh`. |
| Giấy ủy quyền dùng nhân viên viết sẵn không | Mặc định: có. |
| Tên hiển thị và nhóm trên webapp | `display_name`, `category`. |
| Thủ tục liên quan sẽ làm sau | Để đặt tên biến dùng lại được. |

## 2. Đối chiếu và chốt trước khi làm

So file trống với hồ sơ đã điền, rồi gửi người dùng các điểm cần chốt (đừng tự quyết):

- Trình bày theo form trống hay theo hồ sơ đã điền (chú thích, ô đánh dấu, mục bỏ đi).
- Ô nào trong văn bản lấy từ ô nhập nào; ô nào để trống cố định.
- Những chỗ hai nguồn khác nhau (vd địa chỉ liên hệ khác trụ sở, ngày ký).
- Khổ giấy (mặc định A4).

Ghi các quyết định kèm ngày vào mô tả PR hoặc một file trong `docs/`.

## 3. Dựng mẫu Word bằng script

Viết `scripts_and_tools/build_<tên>.py` (chạy lại được, ghi đè file đích) thay vì sửa tay trong Word:

- Nguồn không chứa dữ liệu cá nhân (form nhà nước) lưu ở `scripts_and_tools/nguon_mau/<tên>/`.
  Nguồn có dữ liệu người thật thì truyền qua tham số dòng lệnh, không lưu trong repo.
- Kiểm tra đúng nguồn bằng `assert` trên vài tiêu đề (chuẩn hóa NFC) trước khi sửa.
- Thay cả đoạn bằng chữ + biến, giữ phông và định dạng của run đầu (`set_parts` trong script hộ kinh doanh).
- Danh sách lặp trong bảng: ba dòng `{%tr for … %}` / dòng dữ liệu / `{%tr endfor %}`.
- Đặt khổ A4; cuối script kiểm tra không còn số định danh hay tên người thật.
- Giấy ủy quyền: Bên B dùng biến `{{ uq_* }}` (chạy `python scripts_and_tools/uy_quyen_dung_bien.py` sau khi dựng).

## 4. Viết `_schema.json`

Theo `docs/schema-v2.md`. Lưu ý:

- `id` chữ thường không dấu nối bằng gạch ngang; `name` trùng tên thư mục.
- Dùng lại tên biến có sẵn (xem `CLAUDE.md`, mục quy ước đặt tên).
- Khai báo đủ mọi file .docx trong `documents`; file theo điều kiện dùng `when`.
- Ô có định dạng bắt buộc (vd phải ghi "Phường …") thêm `validate.pattern` + `message`, và thêm giá trị mẫu hợp lệ trong
  `services/sample_data.py`.
- Mẫu tự dựng bảng ngành: `"fill_nganh_table": false`.
- Biến mới cần tính toán (vd tên cơ quan theo xã/phường): thêm filter Jinja trong `create_jinja_env`
  hoặc tính trong `normalize_context`; không viết công thức dài trong file Word.

## 5. Kiểm tra

```bash
cd webapp_v2
python -m tools.template_lint "templates/<tên>"        # 0 lỗi, không có cảnh báo W030 (dữ liệu viết cứng)
UPDATE_GOLDEN=1 python -m pytest -q tests/test_golden_snapshots.py -k "<id>"
git diff --stat tests/golden                             # chỉ có file của bộ mới
python -m pytest -q                                      # toàn bộ
```

Viết `tests/test_<tên>.py` với người giả, kiểm tra: danh sách file sinh ra, các dòng quan trọng đúng như hồ sơ đã điền,
từng lựa chọn (Có/Không…), các chữ của form trống không còn sót (`(nếu có)`, `☐`, `....`, `{{`), kiểm tra định dạng trả 422.

## 6. Gửi người dùng duyệt

- Sinh một bộ hồ sơ với người giả, chuyển sang PDF (`soffice --headless --convert-to pdf`) và **tự xem từng trang**
  (bảng bị xuống dòng, cột hẹp, khoảng trắng thừa) trước khi gửi.
- Gửi PDF kèm danh sách những chỗ tự đặt mà người dùng chưa xác nhận.
- Tạo PR; chỉ merge khi người dùng nói "merge".

## Danh sách kiểm trước khi tạo PR

- [ ] Không có tên, số định danh, địa chỉ, điện thoại của người thật trong mẫu, test, script, ảnh chụp chuẩn, mô tả PR.
- [ ] `template_lint` 0 lỗi; toàn bộ test qua; ảnh chụp chuẩn của bộ khác không đổi.
- [ ] Script dựng mẫu chạy lại ra đúng mẫu đang commit.
- [ ] `schemas/template-schema.json` và `docs/schema-v2.md` đã cập nhật nếu thêm khóa mới.
- [ ] Người dùng đã xem bản PDF sinh thử.
