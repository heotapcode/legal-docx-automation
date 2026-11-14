"""Trang giới thiệu (/) dựng sẵn ở máy chủ để Google đọc được, kèm robots.txt và sitemap.xml.

Nội dung lấy từ cấu hình Kinh doanh (bảng giá, Zalo, cam kết, tỷ lệ cọc: services/kinh_doanh.py) và danh sách bộ mẫu,
nên sửa giá / số Zalo trên trang quản trị là trang giới thiệu đổi theo. Câu chữ cố định nằm ở pages/trang_chu.html.
"""
import json
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

import config

PAGES_DIR = config.BASE_DIR / "pages"
_env = Environment(loader=FileSystemLoader(str(PAGES_DIR)), autoescape=select_autoescape(["html", "xml"]))

# Thứ tự nhóm thủ tục trên trang (nhóm khác xếp sau)
CATEGORY_ORDER = ["Thành lập mới", "Thay đổi ĐKKD", "Thay đổi", "Tăng vốn", "Giảm vốn", "Chuyển nhượng & Chuyển đổi",
                  "Địa điểm kinh doanh", "Tạm dừng & Hoạt động lại", "Giải thể", "Cấp lại & Thay đổi"]


def ga_snippet(ga4_id: str, spa: bool = False) -> str:
    """Khai báo mã GA4 cho static/js/track.js (rỗng khi chưa cấu hình). Mã đã được kiểm tra dạng G-[A-Z0-9]."""
    if not ga4_id:
        return ""
    return (f'<script>window.NAC_GA4 = {json.dumps(ga4_id)};'
            + (" window.NAC_SPA = true;" if spa else "") + "</script>")


def procedure_groups() -> List[Dict[str, Any]]:
    from routes.templates import get_templates
    groups: Dict[str, List[Dict[str, str]]] = {}
    for t in get_templates()["templates"]:
        if t.get("id"):
            groups.setdefault(t["category"] or "Khác", []).append(t)
    order = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    return [{"ten": c, "thu_tuc": sorted(groups[c], key=lambda t: t["display_name"])}
            for c in sorted(groups, key=lambda c: (order.get(c, 99), c))]


def faq(cfg: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {"q": "Tải bộ hồ sơ có mất phí không?",
         "a": "Không. Bạn điền thông tin, để lại họ tên và số Zalo rồi tải bộ hồ sơ Word về sửa, in, ký và tự nộp."},
        {"q": "Hồ sơ có cần đóng dấu không?",
         "a": "Không. Các văn bản trong bộ hồ sơ chỉ cần ký bằng bút mực xanh, đúng người có tên dưới chỗ ký. "
              "Tờ hướng dẫn đầu file .zip ghi rõ ai ký văn bản nào."},
        {"q": "Nhờ nộp trọn gói thì thanh toán thế nào?",
         "a": f"Chọn gói, quét mã QR để đặt cọc {cfg.get('ty_le_coc', 50)}% giá gói; phần còn lại thanh toán khi có "
              "kết quả. Gói báo giá theo hồ sơ thì tư vấn viên báo giá qua Zalo trước."},
        {"q": "Gửi hồ sơ đã ký cho bên nộp hộ bằng cách nào?",
         "a": "Scan hoặc chụp rõ các trang đã ký rồi gửi qua Zalo (nhanh nhất)"
              + (f", hoặc gửi bản giấy qua bưu điện tới {cfg['dia_chi_nhan_ho_so']}." if cfg.get("dia_chi_nhan_ho_so")
                 else ".")},
        {"q": "Thông tin cá nhân tôi nhập có được lưu không?",
         "a": "Chỉ lưu họ tên, số Zalo, tên thủ tục và tên doanh nghiệp để liên hệ tư vấn. Số định danh, địa chỉ và nội "
              f"dung hồ sơ không được lưu. Thông tin được giữ tối đa {cfg.get('thoi_gian_luu_thang', 24)} tháng, "
              f"bạn có thể yêu cầu xóa qua Zalo {cfg['zalo']}."},
        {"q": "Bao lâu thì có kết quả?",
         "a": "Theo Luật Doanh nghiệp, Phòng Đăng ký kinh doanh xem xét trong 3 ngày làm việc kể từ ngày nhận hồ sơ "
              "hợp lệ."},
    ]


def json_ld(cfg: Dict[str, Any], site_url: str, ten: str, questions: List[Dict[str, str]]) -> str:
    data = [
        {"@context": "https://schema.org", "@type": "ProfessionalService", "name": ten, "url": site_url + "/",
         "telephone": cfg["zalo"], "areaServed": "VN",
         **({"address": {"@type": "PostalAddress", "streetAddress": cfg["dia_chi_nhan_ho_so"], "addressCountry": "VN"}}
            if cfg.get("dia_chi_nhan_ho_so") else {})},
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": f["q"],
                         "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in questions]},
    ]
    # Chặn đóng thẻ <script> sớm nếu nội dung có "</"
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def site_url(request_base: str) -> str:
    return (config.SITE_URL or request_base).rstrip("/")


def render(request_base: str) -> str:
    from services import kinh_doanh
    cfg = kinh_doanh.get()
    base = site_url(request_base)
    ten = cfg.get("ten_don_vi") or "NAC"
    goi = [dict(g, gia_so=kinh_doanh.gia_so(g)) for g in cfg["goi"]]
    for g in goi:
        g["coc"] = kinh_doanh.tien_coc(g["gia_so"], cfg) if g["gia_so"] else 0
    groups = procedure_groups()
    questions = faq(cfg)
    return _env.get_template("trang_chu.html").render(
        cfg=cfg, ten=ten, goi=goi, gia_tu=min([g["gia_so"] for g in goi if g["gia_so"]], default=0), groups=groups, so_thu_tuc=sum(len(g["thu_tuc"]) for g in groups),
        faq=questions, json_ld=json_ld(cfg, base, ten, questions), site_url=base,
        ga=ga_snippet(cfg.get("ga4_id", "")), vnd=lambda n: f"{int(n):,}".replace(",", ".") + "đ",
        zalo_url="https://zalo.me/" + cfg["zalo"],
    )


def robots(request_base: str) -> str:
    return f"User-agent: *\nDisallow: /api/\nDisallow: /app\nSitemap: {site_url(request_base)}/sitemap.xml\n"


def sitemap(request_base: str) -> str:
    base = site_url(request_base)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"  <url><loc>{base}/</loc></url>\n"
            "</urlset>\n")
