"""Dựng lại Thông báo tạm ngừng / tiếp tục kinh doanh (Mẫu số 27) và Thông báo giải thể (Mẫu số 30) mới.

Nguồn: scripts_and_tools/nguon_mau/thong_tu_2026_du_thao/Mẫu số 27|30 ... .docx (tách bằng tach_bieu_mau_thong_tu.py).
Giữ tên biến và các nội dung app đang ghi sẵn (khoảng thời gian tạm ngừng, lý do).

Quyết định của anh (12/11/2026):
  1. Mẫu 27: giữ nguyên toàn bộ form (cả phần tạm ngừng và tiếp tục, mục chi nhánh/địa điểm/văn phòng đại diện);
     Thông báo tạm ngừng chỉ điền mục 1a), Thông báo hoạt động lại chỉ điền mục 2a).
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


def tam_ngung(rel):
    f = Form(MAU27)
    common(f)
    set_text(f.next("Thông báo tạm ngừng kinh doanh kể từ ngày"),
             "Thông báo tạm ngừng kinh doanh kể từ ngày     tháng     năm 2026 đến hết ngày     tháng     năm 2027",
             bold=False)
    f.fill("Lý do tạm ngừng:", LY_DO_TAM_NGUNG)
    f.fill("Họ, chữ đệm và tên:", "{{ ddpl_ho_ten }}")
    f.save(rel)


def hoat_dong_lai():
    f = Form(MAU27)
    common(f)
    f.next("2. Trường hợp tiếp tục kinh doanh")
    set_text(f.next("Thông báo tiếp tục kinh doanh kể từ ngày"),
             "Thông báo tiếp tục kinh doanh kể từ ngày     tháng     năm 2026", bold=False)
    f.fill("Lý do tiếp tục kinh doanh:", LY_DO_TIEP_TUC)
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
