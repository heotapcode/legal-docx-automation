"""Trang giới thiệu (/) và các trang đích quảng cáo (/thanh-lap-cong-ty...) dựng sẵn ở máy chủ để Google đọc được, kèm robots.txt và sitemap.xml.

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


def ga_snippet(ga4_id: str, spa: bool = False, ads_id: str = "", ads_lead_label: str = "") -> str:
    """Khai báo mã đo lường cho static/js/track.js (rỗng khi chưa cấu hình gì).

    Các mã đã được kiểm tra dạng ở services/kinh_doanh.validate (G-..., AW-..., nhãn chuyển đổi) và còn được
    json.dumps nên không chèn được mã lạ vào trang.
    """
    if not ga4_id and not ads_id:
        return ""
    parts = []
    if ga4_id:
        parts.append(f"window.NAC_GA4 = {json.dumps(ga4_id)};")
    if ads_id:
        parts.append(f"window.NAC_ADS = {json.dumps(ads_id)};")
        if ads_lead_label:
            parts.append(f"window.NAC_ADS_LEAD = {json.dumps(ads_lead_label)};")
    if spa:
        parts.append("window.NAC_SPA = true;")
    return "<script>" + " ".join(parts) + "</script>"


def tracking(cfg: Dict[str, Any], spa: bool = False) -> str:
    return ga_snippet(cfg.get("ga4_id", ""), spa, cfg.get("google_ads_id", ""), cfg.get("google_ads_nhan_lead", ""))


# Trang chủ và các trang đích cho quảng cáo theo nhóm từ khóa (cùng khung pages/trang_chu.html).
# nhom: các nhóm thủ tục hiện trên trang; goi: các gói hiện trong bảng giá; faq_rieng: câu hỏi thêm ở đầu.
# Câu chữ là bản nháp chờ người dùng duyệt (docs/quan-tri.md).
PAGES: Dict[str, Dict[str, Any]] = {
    "": {
        "title": "Soạn hồ sơ đăng ký doanh nghiệp miễn phí, nộp hộ trọn gói",
        "h1": ("Soạn hồ sơ đăng ký doanh nghiệp ", "miễn phí", ", nộp hộ khi bạn cần"),
        "lead": "Điền thông tin, quét căn cước bằng điện thoại, tải ngay bộ hồ sơ Word theo biểu mẫu mới. Bận hoặc "
                "chưa quen thủ tục? Chọn nộp trọn gói: chúng tôi kiểm tra, nộp và báo kết quả qua Zalo.",
        "mo_ta": "Tự soạn bộ hồ sơ thành lập, thay đổi, tạm ngừng, giải thể doanh nghiệp theo biểu mẫu mới, tải file "
                 "Word miễn phí.",
        "nhom": None, "goi": None, "faq_rieng": [],
    },
    "thanh-lap-cong-ty": {
        "title": "Thành lập công ty: soạn hồ sơ miễn phí, nộp hộ trọn gói",
        "h1": ("Thành lập công ty: ", "soạn hồ sơ miễn phí", ", nộp hộ khi bạn cần"),
        "lead": "Công ty TNHH một thành viên, hai thành viên, công ty cổ phần hoặc hộ kinh doanh. Điền thông tin, quét "
                "căn cước của các thành viên, tải ngay bộ hồ sơ: giấy đề nghị, điều lệ, danh sách thành viên, giấy "
                "ủy quyền.",
        "mo_ta": "Soạn hồ sơ thành lập công ty TNHH, cổ phần, hộ kinh doanh theo biểu mẫu mới, tải file Word miễn phí.",
        "nhom": ["Thành lập mới"], "goi": ["khoi_nghiep", "co_ban", "ho_kd"],
        "faq_rieng": [
            {"q": "Thành lập công ty cần chuẩn bị gì?",
             "a": "Tên công ty dự kiến, địa chỉ trụ sở, vốn điều lệ, ngành nghề kinh doanh và căn cước của từng thành "
                  "viên hoặc cổ đông, người đại diện theo pháp luật. Form có ô tra mã ngành theo mô tả."},
            {"q": "Gói Khởi nghiệp khác Gói Cơ bản thế nào?",
             "a": "Gói Cơ bản: soạn, nộp hồ sơ và nhận kết quả. Gói Khởi nghiệp thêm các việc ngay sau khi có giấy "
                  "chứng nhận (xem bảng giá bên dưới)."},
        ],
    },
    "thay-doi-dang-ky-kinh-doanh": {
        "title": "Thay đổi đăng ký kinh doanh: soạn hồ sơ miễn phí, nộp hộ trọn gói",
        "h1": ("Thay đổi đăng ký kinh doanh: ", "soạn hồ sơ miễn phí", ", nộp hộ khi bạn cần"),
        "lead": "Đổi địa chỉ, tăng giảm vốn, thêm bớt ngành nghề, chuyển nhượng vốn, đổi người đại diện, nhiều nội dung "
                "trong một bộ hồ sơ. Nhập mã số thuế để lấy thông tin công ty, tải ngay bộ hồ sơ Word.",
        "mo_ta": "Soạn hồ sơ thay đổi đăng ký doanh nghiệp: địa chỉ, vốn, ngành nghề, thành viên, người đại diện. Tải "
                 "file Word miễn phí.",
        "nhom": ["Thay đổi ĐKKD", "Thay đổi", "Tăng vốn", "Giảm vốn", "Chuyển nhượng & Chuyển đổi",
                 "Cấp lại & Thay đổi"],
        "goi": ["thay_doi"],
        "faq_rieng": [
            {"q": "Thay đổi nhiều nội dung cùng lúc được không?",
             "a": "Được. Chọn thủ tục \"Thay đổi nội dung ĐKKD\" để làm một bộ hồ sơ cho nhiều nội dung thay đổi."},
            {"q": "Có thời hạn đăng ký thay đổi không?",
             "a": "Có. Theo Luật Doanh nghiệp, doanh nghiệp đăng ký thay đổi trong 10 ngày kể từ ngày có thay đổi."},
        ],
    },
}


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


def render(request_base: str, slug: str = "") -> str:
    from services import kinh_doanh
    spec = PAGES[slug]
    cfg = kinh_doanh.get()
    base = site_url(request_base)
    ten = cfg.get("ten_don_vi") or "NAC"
    goi = [dict(g, gia_so=kinh_doanh.gia_so(g)) for g in cfg["goi"] if not spec["goi"] or g["ma"] in spec["goi"]]
    for g in goi:
        g["coc"] = kinh_doanh.tien_coc(g["gia_so"], cfg) if g["gia_so"] else 0
    gia_tu = min([g["gia_so"] for g in goi if g["gia_so"]], default=0)
    groups = [g for g in procedure_groups() if not spec["nhom"] or g["ten"] in spec["nhom"]]
    so_thu_tuc = sum(len(g["thu_tuc"]) for g in groups)
    vnd = lambda n: f"{int(n):,}".replace(",", ".") + "đ"  # noqa: E731
    questions = spec["faq_rieng"] + faq(cfg)
    page = {
        "slug": slug, "path": "/" + slug, "title": spec["title"], "h1": spec["h1"], "lead": spec["lead"],
        "description": spec["mo_ta"] + (f" Nhờ nộp trọn gói từ {vnd(gia_tu)}, đặt cọc {cfg.get('ty_le_coc', 50)}%."
                                        if gia_tu else ""),
        "fact": (f"{so_thu_tuc} thủ tục: thành lập, thay đổi, tạm ngừng, giải thể" if not spec["nhom"]
                 else f"{so_thu_tuc} thủ tục có sẵn"),
        "proc_title": f"{so_thu_tuc} thủ tục có sẵn",
    }
    return _env.get_template("trang_chu.html").render(
        page=page, cfg=cfg, ten=ten, goi=goi, gia_tu=gia_tu, groups=groups, so_thu_tuc=so_thu_tuc,
        faq=questions, json_ld=json_ld(cfg, base, ten, questions), site_url=base,
        tracking=tracking(cfg), vnd=vnd, zalo_url="https://zalo.me/" + cfg["zalo"],
    )


def robots(request_base: str) -> str:
    return f"User-agent: *\nDisallow: /api/\nDisallow: /app\nSitemap: {site_url(request_base)}/sitemap.xml\n"


def sitemap(request_base: str) -> str:
    base = site_url(request_base)
    urls = "".join(f"  <url><loc>{base}/{slug}</loc></url>\n" for slug in PAGES)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{urls}</urlset>\n")
