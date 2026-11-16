"""Phễu khách: khách để lại họ tên, số Zalo (kèm đồng ý xử lý dữ liệu cá nhân) trước khi tải hồ sơ.

- `parse_lead`: kiểm tra thông tin khách gửi kèm yêu cầu sinh hồ sơ.
- `classify` / `score`: nhóm thủ tục, gói nên chào, điểm ưu tiên liên hệ.
- `record`: lưu vào bảng `leads` của CSDL quản trị. KHÔNG lưu CCCD, địa chỉ hay dữ liệu hồ sơ của khách.
- `notify`: email báo khách mới (cấu hình SMTP_* trong .env; chưa cấu hình thì chỉ ghi log).
- `cover_docx`: tờ "00. Hướng dẫn nộp hồ sơ và bảng giá dịch vụ" đặt đầu file .zip khách tải về
  (các bước còn phải làm, cách ký và gửi hồ sơ, văn bản nào ai ký, gói dịch vụ, thông tin đặt cọc).
- `payment_info`: mã QR VietQR đặt cọc cho khách nhờ nộp (services/vietqr.py).
"""
import io
import json
import logging
import re
import smtplib
import unicodedata
import zipfile
from email.message import EmailMessage
from typing import Any, Dict, List, Optional, Tuple

import config
from services import kinh_doanh

logger = logging.getLogger(__name__)

ROLES = {"chu_dn": "Chủ doanh nghiệp / người sáng lập", "ke_toan": "Kế toán / đơn vị dịch vụ"}
DELIVERY = {"scan": "Scan / chụp gửi qua Zalo", "giay": "Gửi bản giấy qua bưu điện"}
STATUSES = {
    "moi": "Mới", "da_nhan": "Đã nhắn", "bao_gia": "Đã báo giá", "da_coc": "Đã nhận cọc", "da_mua": "Đã mua",
    "ke_toan": "Đã ký kế toán", "khong_mua": "Không mua",
}
COVER_NAME = "00. Hướng dẫn nộp hồ sơ và bảng giá dịch vụ.docx"
SOURCE_KEYS = ("utm_source", "utm_medium", "utm_campaign", "utm_term", "ref", "gclid", "landing", "referrer")

# Nhóm thủ tục -> (gói nên chào, gói thứ hai, điểm cơ sở)
GROUPS = {
    "thanh_lap": ("khoi_nghiep", "co_ban", 80),
    "ho_kd": ("ho_kd", None, 65),
    "thay_doi": ("thay_doi", None, 70),
    "giai_the": ("khac", None, 75),
    "tam_dung": ("khac", None, 60),
    "khac": ("khac", None, 60),
}

# Các bước khách còn phải tự làm sau khi có bộ hồ sơ, theo nhóm thủ tục
NEXT_STEPS = {
    "thanh_lap": [
        "Kiểm tra lại toàn bộ thông tin, ký đủ các văn bản.",
        "Người nộp có tài khoản định danh điện tử mức 2 (VNeID) để đăng nhập Cổng thông tin quốc gia về đăng ký doanh nghiệp.",
        "Nộp hồ sơ trên Cổng, theo dõi và sửa, bổ sung khi có thông báo yêu cầu sửa đổi.",
        "Sau khi có Giấy chứng nhận: khắc dấu, mở tài khoản ngân hàng, mua chữ ký số, đăng ký hóa đơn điện tử, "
        "khai thuế ban đầu với cơ quan thuế.",
    ],
    "ho_kd": [
        "Kiểm tra lại thông tin, chủ hộ ký Giấy đề nghị.",
        "Nộp hồ sơ tới cơ quan đăng ký hộ kinh doanh cấp xã nơi đặt trụ sở (trực tiếp hoặc qua dịch vụ công trực tuyến).",
        "Sau khi có Giấy chứng nhận: đăng ký thuế, kê khai và nộp thuế theo phương pháp đã chọn.",
    ],
    "thay_doi": [
        "Kiểm tra lại thông tin, ký đủ quyết định, biên bản, thông báo theo đúng người ký.",
        "Nộp hồ sơ trên Cổng thông tin quốc gia về đăng ký doanh nghiệp, theo dõi và sửa khi có yêu cầu.",
        "Với chuyển nhượng vốn: kê khai thuế thu nhập cá nhân từ chuyển nhượng vốn (nếu có).",
        "Cập nhật lại thông tin với ngân hàng, cơ quan thuế, hóa đơn điện tử khi tên hoặc địa chỉ thay đổi.",
    ],
    "tam_dung": [
        "Gửi thông báo tới cơ quan đăng ký kinh doanh chậm nhất 03 ngày làm việc trước ngày tạm ngừng hoặc tiếp tục.",
        "Nộp trên Cổng thông tin quốc gia về đăng ký doanh nghiệp, theo dõi kết quả.",
        "Trong thời gian tạm ngừng: hoàn thành các nghĩa vụ thuế còn lại theo quy định.",
    ],
    "giai_the": [
        "Hoàn thành nghĩa vụ thuế, thanh toán các khoản nợ, làm thủ tục chấm dứt hiệu lực mã số thuế với cơ quan thuế.",
        "Ký đủ quyết định, biên bản, báo cáo thanh lý tài sản.",
        "Nộp hồ sơ giải thể trên Cổng thông tin quốc gia về đăng ký doanh nghiệp, theo dõi đến khi có kết quả.",
    ],
    "khac": [
        "Kiểm tra lại thông tin, ký đủ các văn bản.",
        "Nộp hồ sơ trên Cổng thông tin quốc gia về đăng ký doanh nghiệp, theo dõi và sửa khi có yêu cầu.",
    ],
}


def classify(template_id: str) -> str:
    tid = template_id or ""
    if tid.startswith("thanh-lap-moi-cong-ty"):
        return "thanh_lap"
    if tid == "thanh-lap-ho-kinh-doanh":
        return "ho_kd"
    if tid.startswith(("giai-the", "huy-bo")):
        return "giai_the"
    if tid.startswith(("tam-dung", "hoat-dong-lai")):
        return "tam_dung"
    if "dia-diem" in tid:
        return "khac"
    return "thay_doi"


def score(group: str, role: str, delegated: bool) -> int:
    base = GROUPS.get(group, GROUPS["khac"])[2]
    return min(100, base + (15 if delegated else 0) + (5 if role == "ke_toan" else 0))


def normalize_phone(raw: str) -> str:
    phone = re.sub(r"[\s.\-()]", "", str(raw or ""))
    if phone.startswith("+84"):
        phone = "0" + phone[3:]
    elif phone.startswith("84") and len(phone) == 11:
        phone = "0" + phone[2:]
    return phone


def parse_lead(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Thông tin khách đã kiểm tra. Sai hoặc thiếu -> ValueError (lời nhắn hiện cho khách)."""
    raw = raw or {}
    name = " ".join(str(raw.get("name") or "").split())[:100]
    phone = normalize_phone(raw.get("phone"))
    if not name:
        raise ValueError("Vui lòng nhập họ tên")
    if not re.fullmatch(r"0\d{9}", phone):
        raise ValueError("Số điện thoại Zalo gồm 10 chữ số, bắt đầu bằng 0")
    if raw.get("consent") is not True:
        raise ValueError("Cần đồng ý để lưu thông tin liên hệ trước khi tải hồ sơ")
    role = raw.get("role") if raw.get("role") in ROLES else "chu_dn"
    src = raw.get("source") if isinstance(raw.get("source"), dict) else {}
    source = {k: str(src[k])[:200] for k in SOURCE_KEYS if src.get(k)}
    delegated = bool(raw.get("delegated"))
    package = raw.get("package") if raw.get("package") in kinh_doanh.goi_by_ma() else None
    delivery = raw.get("delivery") if raw.get("delivery") in DELIVERY else ("scan" if delegated else None)
    return {"name": name, "phone": phone, "role": role, "delegated": delegated, "source": source,
            "package": package if delegated else None, "delivery": delivery if delegated else None}


def _company_name(data: Dict[str, Any]) -> str:
    for k in ("ten_cong_ty_vn", "ten_hkd", "ten_moi_vn"):
        if str(data.get(k) or "").strip():
            return str(data[k]).strip()[:200]
    return ""


def _members(data: Dict[str, Any]) -> Optional[int]:
    tv = data.get("thanh_vien")
    return len(tv) if isinstance(tv, list) and tv else None


def build(lead: Dict[str, Any], template_id: str, template_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Bản ghi khách đầy đủ (chưa lưu): nhóm thủ tục, gói nên chào, điểm."""
    group = classify(template_id)
    pkg = lead.get("package") or GROUPS.get(group, GROUPS["khac"])[0]
    cfg = kinh_doanh.get()
    amount = kinh_doanh.gia_so(kinh_doanh.goi_by_ma(cfg).get(pkg, {})) if lead.get("delegated") else 0
    return dict(lead, template_id=template_id, template_name=template_name, group=group,
                company_name=_company_name(data), members=_members(data), package=pkg,
                score=score(group, lead["role"], lead["delegated"]), amount=amount,
                deposit=kinh_doanh.tien_coc(amount, cfg) if amount else 0, pay_code=None)


def record(rec: Dict[str, Any]) -> int:
    from services import admin_db
    now = admin_db.now_iso()
    with admin_db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO leads(created_at, updated_at, name, phone, role, delegated, template_id, template_name,"
            " company_name, members, score, package, source, consent_text, delivery, amount, deposit, ref)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (now, now, rec["name"], rec["phone"], rec["role"], int(rec["delegated"]), rec["template_id"],
             rec["template_name"], rec["company_name"], rec["members"], rec["score"], rec["package"],
             json.dumps(rec["source"], ensure_ascii=False), kinh_doanh.loi_dong_y(), rec.get("delivery"),
             rec.get("amount", 0), rec.get("deposit", 0), (rec["source"].get("ref") or "").strip().lower() or None))
        lead_id = cur.lastrowid
        # Mã khách: dùng làm nội dung chuyển khoản để đối chiếu (HS0001, HS0002...)
        rec["pay_code"] = f"HS{lead_id:04d}"
        conn.execute("UPDATE leads SET pay_code = ? WHERE id = ?", (rec["pay_code"], lead_id))
        return lead_id


def list_leads(limit: int = 500) -> List[Dict[str, Any]]:
    from services import admin_db
    with admin_db.connect() as conn:
        rows = conn.execute("SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["source"] = json.loads(d["source"] or "{}")
        out.append(d)
    return out


def update(lead_id: int, changes: Dict[str, Any], user_id=None) -> Dict[str, Any]:
    from services import admin_db
    fields = {}
    if "status" in changes:
        if changes["status"] not in STATUSES:
            raise ValueError("Trạng thái không hợp lệ")
        fields["status"] = changes["status"]
    if "revenue" in changes:
        try:
            fields["revenue"] = max(0, int(re.sub(r"[^\d]", "", str(changes["revenue"])) or 0))
        except ValueError:
            raise ValueError("Doanh thu phải là số")
    if "note" in changes:
        fields["note"] = str(changes["note"] or "")[:2000]
    if not fields:
        raise ValueError("Không có gì để cập nhật")
    with admin_db.connect() as conn:
        sets = ", ".join(f"{k} = ?" for k in fields)
        cur = conn.execute(f"UPDATE leads SET {sets}, updated_at = ? WHERE id = ?",
                           (*fields.values(), admin_db.now_iso(), lead_id))
        if cur.rowcount == 0:
            raise KeyError(lead_id)
        admin_db.audit(conn, user_id, "lead_update", f"{lead_id}: {', '.join(fields)}")
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    return dict(row)


def delete(lead_id: int, user_id=None) -> None:
    """Xóa hẳn thông tin một khách (khi khách yêu cầu xóa dữ liệu)."""
    from services import admin_db
    with admin_db.connect() as conn:
        cur = conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        if cur.rowcount == 0:
            raise KeyError(lead_id)
        admin_db.audit(conn, user_id, "lead_delete", str(lead_id))


# ---------- Đặt cọc qua mã QR ----------

def transfer_content(pay_code: str, phone: str) -> str:
    return f"{pay_code} {phone}"


def payment_info(pay_code: str, phone: str) -> Optional[Dict[str, Any]]:
    """Thông tin đặt cọc của một khách nhờ nộp (mã khách + số Zalo phải khớp). None nếu không có."""
    from services import admin_db, vietqr
    with admin_db.connect() as conn:
        row = conn.execute("SELECT * FROM leads WHERE pay_code = ? AND phone = ?",
                           (pay_code, normalize_phone(phone))).fetchone()
    if not row or not row["delegated"]:
        return None
    cfg = kinh_doanh.get()
    goi = kinh_doanh.goi_by_ma(cfg).get(row["package"], {})
    bank = cfg.get("ngan_hang") or {}
    out = {"pay_code": pay_code, "package": goi.get("ten", row["package"]), "gia": goi.get("gia", ""),
           "amount": row["amount"], "deposit": row["deposit"], "ty_le_coc": cfg.get("ty_le_coc", 50),
           "delivery": row["delivery"], "dia_chi_nhan_ho_so": cfg.get("dia_chi_nhan_ho_so", ""),
           "bank": {"ten": vietqr.BANKS.get(bank.get("ma_bin"), ""), "so_tk": bank.get("so_tk", ""),
                    "chu_tk": bank.get("chu_tk", "")},
           "content": transfer_content(pay_code, row["phone"]), "qr_svg": None}
    if row["deposit"] and bank.get("ma_bin") and bank.get("so_tk"):
        out["qr_svg"] = vietqr.svg(vietqr.payload(bank["ma_bin"], bank["so_tk"], row["deposit"], out["content"]))
    return out


def vnd(n: int) -> str:
    return f"{int(n):,}".replace(",", ".") + "đ"


# ---------- Email báo khách mới ----------

def _partner_line(ref: Optional[str]) -> List[str]:
    if not ref:
        return []
    from services import doi_tac
    try:
        p = doi_tac.by_code(ref)
    except Exception:  # CSDL quản trị chưa sẵn sàng: email vẫn gửi
        p = None
    return [f"Đối tác giới thiệu: {p['name']} ({p['code']}, hoa hồng {p['pct']}%)" if p
            else f"Mã giới thiệu chưa có trong danh sách đối tác: {ref}"]


def email_text(rec: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[str, str]:
    goi = kinh_doanh.goi_by_ma(cfg).get(rec["package"], {})
    hinh_thuc = "Nhờ nộp trọn gói" if rec["delegated"] else "Tự nộp (tải hồ sơ miễn phí)"
    subject = f"[Khách mới {rec['score']}/100] {rec['name']} – {rec['template_name']}"
    src = rec.get("source") or {}
    nguon = ", ".join(f"{k}={v}" for k, v in src.items()) or "trực tiếp"
    lines = [
        f"Khách: {rec['name']} – Zalo: {rec['phone']} (https://zalo.me/{rec['phone']})",
        f"Vai trò: {ROLES.get(rec['role'], rec['role'])}",
        f"Hình thức: {hinh_thuc}",
        f"Thủ tục: {rec['template_name']}",
        f"Doanh nghiệp: {rec['company_name'] or '(chưa có tên)'}"
        + (f" – {rec['members']} thành viên/cổ đông" if rec.get("members") else ""),
        f"{'Gói khách chọn' if rec['delegated'] else 'Gói nên chào'}: {goi.get('ten', rec['package'])} ({goi.get('gia', '')})",
        f"Điểm ưu tiên: {rec['score']}/100",
        f"Nguồn: {nguon}",
        *_partner_line(src.get("ref")),
        "",
        "Mục tiêu: nhắn Zalo trong 5 phút, kèm một nhận xét cụ thể về hồ sơ của khách.",
    ]
    if rec["delegated"]:
        extra = [f"Cách gửi hồ sơ đã ký: {DELIVERY.get(rec.get('delivery'), '')}"]
        if rec.get("deposit"):
            extra.append(f"Tiền cọc: {vnd(rec['deposit'])} – nội dung chuyển khoản: "
                         f"{transfer_content(rec.get('pay_code') or '', rec['phone'])}")
        lines[6:6] = extra
    return subject, "\n".join(lines)


def notify(rec: Dict[str, Any]) -> bool:
    """Gửi email báo khách mới. Không cấu hình SMTP hoặc gửi lỗi -> ghi log, trả False (không làm hỏng việc tải)."""
    cfg = kinh_doanh.get()
    to = cfg.get("email_nhan_bao")
    if not (config.SMTP_HOST and config.SMTP_USER and config.SMTP_PASSWORD and to):
        logger.info("Khách mới %s (%s) – chưa cấu hình SMTP nên không gửi email", rec["name"], rec["template_name"])
        return False
    subject, body = email_text(rec, cfg)
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, config.SMTP_FROM, to
    msg.set_content(body)
    try:
        if config.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as s:
                s.login(config.SMTP_USER, config.SMTP_PASSWORD)
                s.send_message(msg)
        else:
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as s:
                s.starttls()
                s.login(config.SMTP_USER, config.SMTP_PASSWORD)
                s.send_message(msg)
        return True
    except Exception:
        logger.exception("Không gửi được email báo khách mới")
        return False


# ---------- Tờ hướng dẫn trong file .zip ----------

# Ai ký văn bản nào, theo loại văn bản (tên file). Luôn kèm nguyên tắc: ký đúng người có tên in dưới chỗ ký.
SIGN_RULES = [
    (("danh sách thành viên", "danh sách cổ đông"),
     "từng thành viên / cổ đông ký vào ô chữ ký của mình; người đại diện theo pháp luật ký cuối trang"),
    (("chủ sở hữu hưởng lợi",), "người đại diện theo pháp luật"),
    (("điều lệ",), "tất cả thành viên / cổ đông sáng lập (hoặc chủ sở hữu) và người đại diện theo pháp luật"),
    (("biên bản họp",), "chủ tọa và thư ký cuộc họp (và các thành viên dự họp nếu có chỗ ký)"),
    (("quyết định",), "chủ sở hữu / Chủ tịch Hội đồng thành viên / Chủ tịch Hội đồng quản trị (người có tên ở chỗ ký)"),
    (("ủy quyền", "uỷ quyền"), "Bên ủy quyền (Bên A) ký; Bên nhận ủy quyền (Bên B) do chúng tôi ký khi nhận hồ sơ"),
    (("hợp đồng chuyển nhượng", "biên bản thanh lý"), "bên chuyển nhượng và bên nhận chuyển nhượng"),
    (("góp vốn",), "người đại diện theo pháp luật"),
    (("giấy đề nghị", "thông báo"), "người đại diện theo pháp luật (hoặc người có chức danh in ở chỗ ký)"),
]


def who_signs(filename: str) -> str:
    low = unicodedata.normalize("NFC", filename).lower()
    for keys, text in SIGN_RULES:
        if any(k in low for k in keys):
            return text
    return "người có tên in dưới chỗ ký"


def cover_docx(rec: Dict[str, Any], files: Optional[List[str]] = None) -> bytes:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt

    cfg = kinh_doanh.get()
    goi = kinh_doanh.goi_by_ma(cfg)
    group = rec["group"]
    first, second, _ = GROUPS.get(group, GROUPS["khac"])
    delegated = rec.get("delegated")

    d = Document()
    normal = d.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(13)

    def para(text="", bold=False, size=None, center=False):
        p = d.add_paragraph()
        run = p.add_run(text)
        run.bold = bold
        if size:
            run.font.size = Pt(size)
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return p

    para("HƯỚNG DẪN NỘP HỒ SƠ VÀ BẢNG GIÁ DỊCH VỤ", bold=True, size=15, center=True)
    para(rec["template_name"].upper(), bold=True, center=True)
    para()
    if rec.get("company_name"):
        para(f"Doanh nghiệp: {rec['company_name']}"
             + (f" – {rec['members']} thành viên/cổ đông" if rec.get("members") else ""))
    if rec.get("pay_code"):
        para(f"Mã hồ sơ: {rec['pay_code']}")
    para("Bộ hồ sơ trong file này là bản soạn thảo. Anh/chị kiểm tra lại toàn bộ thông tin trước khi ký"
         + ("." if delegated else "; anh/chị chịu trách nhiệm về hồ sơ khi tự nộp."))

    n = 0

    def heading(text):
        nonlocal n
        n += 1
        para(f"{n}. {text}", bold=True)

    heading("Cách ký hồ sơ")
    para("• Ký bằng bút mực xanh vào mọi chỗ ký; không cần đóng dấu.")
    para("• Ký đúng người có tên in dưới chỗ ký. Theo loại văn bản:")
    for f in files or []:
        if f.lower().endswith(".docx"):
            para(f"   – {f.rsplit('.', 1)[0]}: {who_signs(f)}.")

    if delegated:
        heading("Gửi hồ sơ đã ký cho chúng tôi")
        para(f"• Cách nhanh nhất: scan hoặc chụp đủ các trang, đúng thứ tự, rõ chữ ký (file PDF), gửi qua Zalo "
             f"{cfg['zalo']}. Không có máy scan: dùng tính năng quét tài liệu trên điện thoại.")
        if cfg.get("dia_chi_nhan_ho_so"):
            para(f"• Hoặc gửi bản giấy đã ký qua bưu điện tới: {cfg['dia_chi_nhan_ho_so']}"
                 f" (ghi mã hồ sơ {rec.get('pay_code') or ''} ngoài phong bì).")
        para("• Anh/chị giữ lại một bản đã ký để đối chiếu.")
        g = goi.get(rec["package"], {})
        heading("Gói dịch vụ và đặt cọc")
        para(f"• {g.get('ten', rec['package'])} – {g.get('gia', '')}: {g.get('mo_ta', '')}")
        if rec.get("deposit"):
            bank = cfg.get("ngan_hang") or {}
            from services import vietqr
            para(f"• Đặt cọc {cfg.get('ty_le_coc', 50)}%: {vnd(rec['deposit'])}; phần còn lại thanh toán khi có kết quả.")
            para(f"• Chuyển khoản: {vietqr.BANKS.get(bank.get('ma_bin'), '')} – số tài khoản {bank.get('so_tk', '')} – "
                 f"{bank.get('chu_tk', '')}. Nội dung: {transfer_content(rec.get('pay_code') or '', rec['phone'])}")
        else:
            para("• Chúng tôi sẽ báo giá qua Zalo sau khi xem hồ sơ.")
    else:
        heading("Các bước anh/chị còn phải làm")
        for i, step in enumerate(NEXT_STEPS.get(group, NEXT_STEPS["khac"]), 1):
            para(f"{i}. {step}")
        heading("Nếu anh/chị muốn nhờ chúng tôi nộp")
        for ma in [m for m in (first, second) if m]:
            g = goi.get(ma)
            if g:
                para(f"• {g['ten']} – {g['gia']}: {g['mo_ta']}")
    if cfg.get("cam_ket"):
        para(f"Cam kết: {cfg['cam_ket']}")
    para(f"Liên hệ Zalo: {cfg['zalo']} (https://zalo.me/{cfg['zalo']})", bold=True)
    para()
    para(f"Bảng giá đầy đủ: " + "; ".join(f"{g['ten']} {g['gia']}" for g in cfg["goi"]) + ".", size=11)

    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def add_cover(zip_bytes: bytes, rec: Dict[str, Any]) -> bytes:
    """File .zip mới: tờ hướng dẫn đứng đầu, sau đó là các file hồ sơ như cũ."""
    src = zipfile.ZipFile(io.BytesIO(zip_bytes))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(COVER_NAME, cover_docx(rec, [i.filename for i in src.infolist()]))
        for info in src.infolist():
            zf.writestr(info, src.read(info.filename))
    return out.getvalue()
