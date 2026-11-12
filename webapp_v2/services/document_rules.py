"""Quy tắc sinh file theo khối `documents` trong _schema.json (Mục 9, bước 3).

Thay cho các điều kiện viết cứng theo tên thư mục/tên file trong render_documents. Mỗi phần tử:
    {"file": "09. Xác nhận góp vốn 1.docx",
     "when": {...},                     # điều kiện (schema_engine.eval_condition) trên RULE DATA bên dưới
     "repeat_for": "tv_moi",            # sinh 1 file cho mỗi phần tử của danh sách này
     "repeat_with": "xac_nhan_gop_von", # hàm dựng ngữ cảnh + tên file cho từng phần tử (REPEATERS)
     "post": ["fill_member_table"]}     # xử lý sau khi điền (HOOKS), theo thứ tự

RULE DATA = ngữ cảnh đã chuẩn hóa, cộng:
    tv_moi         danh sách thành viên dùng để lặp/điền bảng (= thanh_vien)
    chuyen_nhuong  danh sách giao dịch chuyển nhượng
    ddpl_changed   True/False: có thay đổi người đại diện (CCCD ĐDPL cũ khác ĐDPL mới; thiếu dữ liệu -> True)

Danh sách rỗng ở `repeat_for` -> file được điền một lần như bình thường (giữ hành vi cũ).
Các hook chỉ chạy khi `tv_moi` có phần tử (giữ hành vi cũ).
Bảng mã ngành được điền vào mọi file khi có danh sách ngành (không cần khai báo).
"""
import re
from typing import Any, Callable, Dict, List, Tuple

from services import render_service as rs

SafeDict = rs.SafeDict


def safe_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def letter(i: int) -> str:
    return chr(ord("a") + i)


# ---------- Sinh lặp: (ngữ cảnh, phần tử, chỉ số, toàn bộ danh sách, tên file mẫu) -> (tên file ra, ngữ cảnh con) ----------

def _xac_nhan_gop_von(context, m, i, items, fname):
    m_name = m.get("HO_TEN") or m.get("ho_ten") or f"TV_{i+1}"
    out_name = safe_filename(f"09{letter(i)}. Xác nhận góp vốn ({m_name}).docx")
    sub = SafeDict(context)
    sub["tv_moi_1_ho_ten"] = m_name
    sub["tv_moi_1_ngay_sinh"] = m.get("NGAY_SINH") or m.get("ngay_sinh", "")
    sub["tv_moi_1_so_cccd"] = m.get("SO_CCCD") or m.get("so_cccd", "")
    sub["tv_moi_1_gioi_tinh"] = m.get("GIOI_TINH") or m.get("gioi_tinh", "")
    sub["tv_moi_1_dia_chi_day_du"] = m.get("DIA_CHI") or m.get("dia_chi_day_du", "")
    v_raw = m.get("VON_GOP") or m.get("von_so", "")
    sub["tv_moi_1_von_so"] = rs.fmt_money(v_raw)
    sub["tv_moi_1_von_chu"] = rs.so_thanh_chu(v_raw)
    sub["tv_moi_1_ty_le"] = m.get("TY_LE") or m.get("ty_le", "")
    return out_name, sub


def _giao_dich_chuyen_nhuong(context, cn, i, items, fname):
    ben_a = cn.get("ben_a", {})
    ben_b = cn.get("ben_b", {})
    ben_a_name = ben_a.get("ho_ten") or f"BenA_{i+1}"
    ben_b_name = ben_b.get("ho_ten") or f"BenB_{i+1}"
    out_name = safe_filename(f"{fname.replace('.docx', '')}_{letter(i)} ({ben_a_name} - {ben_b_name}).docx")
    sub = SafeDict(context)
    sub["ben_a"] = SafeDict(ben_a)
    sub["ben_b"] = SafeDict(ben_b)
    for k_a, v_a in ben_a.items():
        sub[f"ben_a_{k_a}"] = v_a
    for k_b, v_b in ben_b.items():
        sub[f"ben_b_{k_b}"] = v_b
    sub["gia_tri_cn_so"] = rs.fmt_money(cn.get("gia_tri_so", ""))
    sub["gia_tri_cn_chu"] = rs.so_thanh_chu(cn.get("gia_tri_so", ""))
    sub["gia_tri_cn_ty_le"] = cn.get("ty_le", "")
    return out_name, sub


def _giao_dich_chuyen_doi(context, cn, i, items, fname):
    ben_a = cn.get("ben_a", {})
    ben_b = cn.get("ben_b", {})
    ben_a_name = ben_a.get("ho_ten") or f"BenA_{i+1}"
    ben_b_name = ben_b.get("ho_ten") or f"BenB_{i+1}"
    if len(items) == 1:
        out_name = f"{fname.replace('.docx', '')} ({ben_a_name} - {ben_b_name}).docx"
    else:
        out_name = f"{fname.replace('.docx', '')}_{letter(i)} ({ben_a_name} - {ben_b_name}).docx"
    out_name = safe_filename(out_name)

    sub = SafeDict(context)
    # Bên A
    sub["ddpl_ho_ten"] = ben_a.get("ho_ten", "")
    sub["ddpl_so_cccd"] = ben_a.get("so_cccd") or ben_a.get("cccd", "")
    sub["ddpl_ngay_sinh"] = ben_a.get("ngay_sinh", "")
    sub["ddpl_gioi_tinh"] = ben_a.get("gioi_tinh", "Nam")
    sub["ddpl_dia_chi_day_du"] = ben_a.get("dia_chi_day_du") or ben_a.get("dia_chi", "")
    sn_a, xp_a, tt_a = rs.parse_address_str(sub["ddpl_dia_chi_day_du"])
    sub["ddpl_dia_chi_so_nha"] = sn_a
    sub["ddpl_dia_chi_xa_phuong"] = xp_a
    sub["ddpl_dia_chi_tinh_thanh"] = tt_a
    # Bên B
    sub["tv2_ho_ten"] = ben_b.get("ho_ten", "")
    sub["tv2_so_cccd"] = ben_b.get("so_cccd") or ben_b.get("cccd", "")
    sub["tv2_ngay_sinh"] = ben_b.get("ngay_sinh", "")
    sub["tv2_gioi_tinh"] = ben_b.get("gioi_tinh", "Nam")
    sub["tv2_dia_chi_day_du"] = ben_b.get("dia_chi_day_du") or ben_b.get("dia_chi", "")
    sn_b, xp_b, tt_b = rs.parse_address_str(sub["tv2_dia_chi_day_du"])
    sub["tv2_dia_chi_so_nha"] = sn_b
    sub["tv2_dia_chi_xa_phuong"] = xp_b
    sub["tv2_dia_chi_tinh_thanh"] = tt_b

    v_raw = cn.get("von_cn_so") or cn.get("von", "")
    sub["tv2_von_cu_so"] = rs.fmt_money(v_raw)
    sub["tv2_von_cu_chu"] = rs.so_thanh_chu(v_raw)
    sub["tv2_von_cu_moi"] = rs.so_thanh_chu(v_raw)
    sub["tv2_ty_le"] = cn.get("ty_le_cn") or cn.get("ty_le", "")
    return out_name, sub


def _giay_chung_nhan_gop_von(context, m, i, items, fname):
    m_name = m.get("HO_TEN") or m.get("ho_ten") or f"TV_{i+1}"
    out_name = (f"07. Giấy chứng nhận góp vốn_{letter(i)} ({m_name}).docx" if "07." in fname
                else f"Giấy chứng nhận góp vốn_{letter(i)} ({m_name}).docx")
    out_name = safe_filename(out_name)
    sub = SafeDict(context)
    ho_ten = m_name
    ngay_sinh = m.get("NGAY_SINH") or m.get("ngay_sinh", "")
    so_cccd = m.get("SO_CCCD") or m.get("so_cccd", "")
    gioi_tinh = m.get("GIOI_TINH") or m.get("gioi_tinh", "Nam")
    dia_chi = m.get("DIA_CHI") or m.get("dia_chi_day_du", "")
    sn_m, xp_m, tt_m = rs.parse_address_str(dia_chi)
    for pfx in ("tv2_", "tv_"):
        sub[f"{pfx}ho_ten"] = ho_ten
        sub[f"{pfx}ngay_sinh"] = ngay_sinh
        sub[f"{pfx}so_cccd"] = so_cccd
        sub[f"{pfx}gioi_tinh"] = gioi_tinh
        sub[f"{pfx}dia_chi_day_du"] = dia_chi
        sub[f"{pfx}dia_chi_so_nha"] = sn_m
        sub[f"{pfx}dia_chi_xa_phuong"] = xp_m
        sub[f"{pfx}dia_chi_tinh_thanh"] = tt_m
    v_raw = str(m.get("VON_GOP") or m.get("von_gop") or m.get("von_so", ""))
    v_fmt = rs.fmt_money(v_raw) if v_raw else ""
    v_chu = rs.so_thanh_chu(v_raw) if v_raw else ""
    sub["tv2_von_cu_so"] = v_fmt
    sub["tv_von_so"] = v_fmt
    sub["tv2_von_cu_chu"] = v_chu
    sub["tv_von_chu"] = v_chu
    ty_le = str(m.get("TY_LE") or m.get("ty_le", ""))
    sub["tv2_ty_le"] = ty_le
    sub["tv_ty_le"] = ty_le
    return out_name, sub


REPEATERS: Dict[str, Callable[..., Tuple[str, Dict[str, Any]]]] = {
    "xac_nhan_gop_von": _xac_nhan_gop_von,
    "giao_dich_chuyen_nhuong": _giao_dich_chuyen_nhuong,
    "giao_dich_chuyen_doi": _giao_dich_chuyen_doi,
    "giay_chung_nhan_gop_von": _giay_chung_nhan_gop_von,
}


# ---------- Xử lý sau khi điền: (doc, ngữ cảnh, danh sách thành viên) ----------

def _qd_chuyen_doi(doc, context, members):
    csh_info = {
        "ho_ten": context.get("csh_ho_ten") or context.get("csh", {}).get("HO_TEN", ""),
        "so_cccd": context.get("csh_so_cccd") or context.get("csh", {}).get("CCCD", ""),
        "gioi_tinh": context.get("csh_gioi_tinh") or context.get("csh", {}).get("GIOI_TINH", "Nam"),
        "dia_chi_day_du": context.get("csh_dia_chi_day_du") or context.get("csh", {}).get("DIA_CHI", ""),
        "von_cu_so": context.get("von_cu_so") or context.get("von_dieu_le_so", ""),
    }
    rs.populate_qd_tables(doc, members, csh_info, context.get("hinh_thuc_cn", "mot_phan"))


HOOKS: Dict[str, Callable[[Any, Dict[str, Any], List[dict]], None]] = {
    "fill_member_table": lambda doc, ctx, m: rs.populate_dstv(doc, m, is_tang_von=False),
    "fill_member_table_tang_von": lambda doc, ctx, m: rs.populate_dstv(doc, m, is_tang_von=True),
    "fill_founders_table": lambda doc, ctx, m: rs.populate_cdsl(doc, m),
    "fill_cshhl_table": lambda doc, ctx, m: rs.populate_cshhl(doc, m, co_phan=ctx.get("loai_hinh") == "cp"),
    "fill_cshhl_table_cp": lambda doc, ctx, m: rs.populate_cshhl(doc, m, co_phan=True),
    "fill_qd_chuyen_doi": _qd_chuyen_doi,
    "fill_dieu_le_chuyen_doi": lambda doc, ctx, m: rs.populate_dieu_le(doc, m),
    "fill_dieu_le_tlm_2tv": lambda doc, ctx, m: rs.populate_dieu_le_tlm_2tv(doc, m),
    "fill_dieu_le_tlm_cp": lambda doc, ctx, m: rs.populate_dieu_le_tlm_cp(
        doc, m, ctx.get("von_dieu_le_so", ""), ctx.get("von_dieu_le_chu", "")),
    "fill_bbh_tang_von_cp": lambda doc, ctx, m: rs.populate_bbh_tang_von_cp(
        doc, m, von_cu_so=ctx.get("von_cu_so", ""), von_moi_so=ctx.get("von_dieu_le_so", "")),
    "fill_bbh_giam_von_cp": lambda doc, ctx, m: rs.populate_bbh_giam_von_cp(
        doc, m, von_cu_so=ctx.get("von_cu_so", ""), von_moi_so=ctx.get("von_dieu_le_so", "")),
    "fill_bbh_tang_von_2tv": lambda doc, ctx, m: rs.populate_bbh_tang_von_2tv(doc, m),
    "fill_bbh_giai_the_cp": lambda doc, ctx, m: rs.populate_bbh_giai_the_cp(doc, m),
}


# ---------- Dựng dữ liệu trước khi chuẩn hóa (khóa "prepare" ở cấp gốc _schema.json) ----------

def _person(raw: Dict[str, Any], prefix: str) -> Dict[str, str]:
    """Người nhập theo kiểu `person` (<prefix>_ho_ten...) -> dạng dùng trong merge_cd1tv2tv_data."""
    parts = [raw.get(f"{prefix}_dia_chi_{k}") or "" for k in ("so_nha", "xa_phuong", "tinh_thanh")]
    return {
        "HO_TEN": raw.get(f"{prefix}_ho_ten") or "",
        "CCCD": raw.get(f"{prefix}_so_cccd") or "",
        "NGAY_SINH": raw.get(f"{prefix}_ngay_sinh") or "",
        "GIOI_TINH": raw.get(f"{prefix}_gioi_tinh") or "Nam",
        "DIA_CHI": raw.get(f"{prefix}_dia_chi_day_du") or ", ".join(p for p in parts if p),
    }


def _member_address(m: Dict[str, Any]) -> str:
    parts = [m.get(f"dia_chi_{k}") or "" for k in ("so_nha", "xa_phuong", "tinh_thanh")]
    return m.get("dia_chi_day_du") or m.get("dia_chi") or ", ".join(p for p in parts if p)


def _prepare_chuyen_doi_1tv_2tv(raw: Dict[str, Any]) -> None:
    """Chuyển đổi Công ty TNHH 1 TV -> 2 TV trở lên.

    Form nhập: chủ sở hữu cũ `csh`, hình thức `hinh_thuc_cn` (mot_phan: giữ lại `csh_von_giu_lai`;
    toan_bo: rút hết vốn), các thành viên MỚI ở `thanh_vien`, ĐDPL mới `ddpl`.
    Dựng: danh sách thành viên đầy đủ (chủ sở hữu cũ là Thành viên 1 nếu giữ lại vốn) và mỗi thành viên mới
    một giao dịch nhận chuyển nhượng từ chủ sở hữu cũ, rồi dùng merge_cd1tv2tv_data như wizard riêng cũ.
    """
    hinh_thuc = raw.get("hinh_thuc_cn") or "mot_phan"
    members = []
    if hinh_thuc == "mot_phan":
        # Để trống thông tin cá nhân: merge_cd1tv2tv_data điền từ chủ sở hữu cũ
        members.append({"ho_ten": "", "von": raw.get("csh_von_giu_lai") or "", "ty_le": raw.get("csh_ty_le") or ""})
    for m in raw.get("thanh_vien") or []:
        if not isinstance(m, dict):
            continue
        members.append({
            "ho_ten": m.get("ho_ten") or "", "cccd": m.get("so_cccd") or m.get("cccd") or "",
            "ngay_sinh": m.get("ngay_sinh") or "", "gioi_tinh": m.get("gioi_tinh") or "Nam",
            "dia_chi": _member_address(m), "von": m.get("von_gop") or m.get("von") or "",
            "ty_le": m.get("ty_le") or "", "nhan_cn": "",
        })
    raw.pop("chuyen_nhuong", None)  # hợp đồng được dựng từ danh sách thành viên
    rs.merge_cd1tv2tv_data(raw, {
        "hinh_thuc_cn": hinh_thuc,
        "oldCompany": {"name": raw.get("ten_cong_ty_vn_cu") or "", "mst": raw.get("ma_so_thue") or "",
                       "von": raw.get("von_dieu_le_so") or ""},
        "csh": _person(raw, "csh"),
        "newCompany": {"nameVn": raw.get("ten_cong_ty_vn") or "", "nameEn": raw.get("ten_cong_ty_nn") or "",
                       "nameShort": raw.get("ten_cong_ty_viet_tat") or "", "phone": raw.get("sdt_cong_ty") or "",
                       "email": raw.get("email_cong_ty") or ""},
        "ddplMoi": _person(raw, "ddpl"),
        "members": members,
    })


PREPARERS: Dict[str, Callable[[Dict[str, Any]], None]] = {
    "chuyen_doi_1tv_2tv": _prepare_chuyen_doi_1tv_2tv,
}


def plan_documents(schema: dict, template_dir) -> List[dict]:
    """Danh sách file cần sinh. Không khai báo `documents` -> mọi file .docx, điền bình thường."""
    if schema.get("documents"):
        return [dict(d) for d in schema["documents"]]
    return [{"file": f.name} for f in sorted(template_dir.glob("*.docx")) if not f.name.startswith(("~$", "_"))]
