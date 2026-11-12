"""Dựng lại Thông báo tạm ngừng / tiếp tục kinh doanh (Mẫu số 27) và Thông báo giải thể (Mẫu số 30) mới.

Nguồn: scripts_and_tools/nguon_mau/thong_tu_2026_du_thao/Mẫu số 27|30 ... .docx (tách bằng tach_bieu_mau_thong_tu.py).
Giữ tên biến và các nội dung app đang ghi sẵn (khoảng thời gian tạm ngừng, lý do).

Quyết định của anh (12/11/2026):
  1. Mẫu 27 (sửa lại 12/11/2026): Thông báo tạm ngừng chỉ giữ mục "1. Trường hợp tạm ngừng" a) Đối với doanh nghiệp;
     Thông báo hoạt động lại chỉ giữ mục "2. Trường hợp tiếp tục kinh doanh" a) Đối với doanh nghiệp.
     Bỏ các mục chi nhánh/địa điểm kinh doanh/văn phòng đại diện và phần của trường hợp kia.
  2. Mẫu 30: bỏ dòng "Số Giấy chứng nhận đăng ký kinh doanh (chỉ kê khai nếu không có mã số...)".
     Dòng "gửi kèm bản sao sổ đăng ký cổ đông" chỉ in cho công ty cổ phần (theo chú thích của form).
  3. Chữ ký theo form ("NGƯỜI ĐẠI DIỆN THEO PHÁP LUẬT CỦA DOANH NGHIỆP"), không thêm "Giám đốc".
  Như các mẫu trước: bỏ chú thích cuối trang.

Chạy từ thư mục gốc repo (ghi đè file đích):
    python scripts_and_tools/build_mau27_30_tam_ngung_giai_the.py
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NGUON = ROOT / "nguon_mau" / "thong_tu_2026_du_thao"

_spec = importlib.util.spec_from_file_location("m234", ROOT / "build_mau234_giay_de_nghi.py")
m234 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m234)
Form, set_text, rows = m234.Form, m234.set_text, m234.rows

MAU27 = NGUON / "Mẫu số 27 - Thông báo tạm ngừng - tiếp tục kinh doanh trước thời hạn.docx"
MAU30 = NGUON / "Mẫu số 30 - Thông báo về việc giải thể doanh nghiệp.docx"

LY_DO_TAM_NGUNG = "Do quá trình hoạt động không hiệu quả, không đạt được kết quả mong muốn"
LY_DO_TIEP_TUC = "Doanh nghiệp thấy được cơ hội kinh doanh và khách hàng tiềm năng mới."


def common(f):
    hdr = f.table("TÊN DOANH NGHIỆP")
    set_text(rows(hdr)[0][0].find(m234.qn("w:p")), "{{ ten_cong_ty_vn }}")
    m234.header(f)
    f.fill("Tên doanh nghiệp (ghi bằng chữ in hoa):", "{{ ten_cong_ty_vn }}")
    f.fill("Mã số doanh nghiệp/Mã số thuế:", "{{ ma_so_thue }}")


def drop_range(f, start, stop):
    """Xóa các đoạn từ đoạn bắt đầu bằng `start` đến ngay trước đoạn bắt đầu bằng `stop` (cùng cấp thân văn bản)."""
    body = f.body
    els = list(body.iterchildren())
    i = next(k for k, e in enumerate(els) if m234.key(m234.text(e)).startswith(m234.key(start)))
    j = next(k for k, e in enumerate(els) if k > i and m234.key(m234.text(e)).startswith(m234.key(stop)))
    for e in els[i:j]:
        body.remove(e)


def tam_ngung(rel):
    f = Form(MAU27)
    common(f)
    set_text(f.next("Thông báo tạm ngừng kinh doanh kể từ ngày"),
             "Thông báo tạm ngừng kinh doanh kể từ ngày     tháng     năm {{ ngay_lap_ngan[-4:] }} đến hết ngày     tháng     năm "
             "{{ (ngay_lap_ngan[-4:] | int) + 1 if ngay_lap_ngan else '' }}",
             bold=False)
    f.fill("Lý do tạm ngừng:", LY_DO_TAM_NGUNG)
    f.fill("Họ, chữ đệm và tên:", "{{ ddpl_ho_ten }}")
    drop_range(f, "b) Đối với chi nhánh/địa điểm kinh doanh", "Doanh nghiệp cam kết hoàn toàn")
    f.save(rel)


def hoat_dong_lai():
    f = Form(MAU27)
    common(f)
    f.next("2. Trường hợp tiếp tục kinh doanh")
    set_text(f.next("Thông báo tiếp tục kinh doanh kể từ ngày"),
             "Thông báo tiếp tục kinh doanh kể từ ngày     tháng     năm {{ ngay_lap_ngan[-4:] }}", bold=False)
    f.fill("Lý do tiếp tục kinh doanh:", LY_DO_TIEP_TUC)
    drop_range(f, "1. Trường hợp tạm ngừng", "2. Trường hợp tiếp tục kinh doanh")
    drop_range(f, "b) Đối với chi nhánh/văn phòng đại diện/địa điểm", "Doanh nghiệp cam kết hoàn toàn")
    f.save("Hoạt động lại trước thời hạn/Thông báo hoạt động trở lại trước thời hạn tạm dừng.docx")


def giai_the(rel, co_phan):
    f = Form(MAU30)
    common(f)
    f.drop_paras("Số Giấy chứng nhận đăng ký kinh doanh")
    if not co_phan:
        f.drop_paras("Doanh nghiệp gửi kèm Thông báo này bản sao sổ đăng ký cổ đông")
    f.save(rel)


if __name__ == "__main__":
    for loai in ("TNHH 1 TV", "TNHH 2 TV", "Cổ Phần"):
        tam_ngung(f"Tạm dừng công ty {loai}/01. Thông báo tạm ngừng.docx")
    hoat_dong_lai()
    giai_the("Giải thể công ty TNHH 1 TV/01. Thông báo giải thể.docx", co_phan=False)
    giai_the("Giải thể công ty TNHH 2 TV/03. Thông báo giải thể.docx", co_phan=False)
    giai_the("Giải thể công ty Cổ Phần/03. Thông báo giải thể.docx", co_phan=True)
