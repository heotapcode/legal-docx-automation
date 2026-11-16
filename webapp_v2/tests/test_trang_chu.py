"""Trang giới thiệu dựng sẵn ở máy chủ (/), robots.txt, sitemap.xml, mã Google Analytics."""
import json
import re

import pytest

import config
from services import auth, kinh_doanh

CSRF = {auth.CSRF_HEADER: auth.CSRF_VALUE}


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ADMIN_DB_PATH", tmp_path / "admin.sqlite3")


def test_landing_is_server_rendered_with_prices_and_procedures(client):
    r = client.get("/")
    assert r.status_code == 200 and r.headers["cache-control"] == "no-cache"
    html = r.text
    cfg = kinh_doanh.get()
    assert "<h1>" in html and "miễn phí" in html
    for g in cfg["goi"]:
        assert g["ten"] in html and g["gia"] in html
    assert "Đặt cọc 600.000đ" in html                  # Gói Cơ bản 1.200.000đ, cọc 50%
    assert cfg["cam_ket"] in html and "https://zalo.me/0987135358" in html
    assert "Ngọc Trục" in html and "mực xanh" in html
    templates = client.get("/api/templates").json()["templates"]
    for t in templates:
        assert f'/thu-tuc/{t["id"]}"' in html, t["id"]
    assert f"{len(templates)} thủ tục" in html
    # Link cũ /#/wizard, /#/admin chuyển sang ứng dụng
    assert "location.replace('/app'" in html and "hashchange" in html
    # Tài nguyên nội bộ có số phiên bản
    assert re.search(r'src="/static/js/track\.js\?v=\d+"', html)


def test_landing_structured_data_and_meta(client):
    html = client.get("/").text
    assert '<link rel="canonical" href="http://testserver/">' in html
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    data = json.loads(m.group(1))
    types = {d["@type"] for d in data}
    assert types == {"ProfessionalService", "FAQPage"}
    faq = next(d for d in data if d["@type"] == "FAQPage")["mainEntity"]
    assert len(faq) >= 5 and all(q["acceptedAnswer"]["text"] for q in faq)
    desc = re.search(r'<meta name="description" content="([^"]+)"', html).group(1)
    assert "800.000đ" in desc and 50 < len(desc) < 300


def test_site_url_setting(client, monkeypatch):
    monkeypatch.setattr(config, "SITE_URL", "https://tenmien.vn")
    assert '<link rel="canonical" href="https://tenmien.vn/">' in client.get("/").text
    assert "Sitemap: https://tenmien.vn/sitemap.xml" in client.get("/robots.txt").text
    sm = client.get("/sitemap.xml")
    assert sm.headers["content-type"].startswith("application/xml") and "<loc>https://tenmien.vn/</loc>" in sm.text


def test_robots_hides_api_and_app(client):
    txt = client.get("/robots.txt").text
    assert "Disallow: /api/" in txt and "Disallow: /app" in txt


def test_app_still_served(client):
    r = client.get("/app")
    assert r.status_code == 200 and "/static/js/router.js" in r.text and "/static/js/track.js" in r.text


def test_no_analytics_until_configured(client):
    for path in ("/", "/app"):
        assert "NAC_GA4" not in client.get(path).text


@pytest.fixture
def admin(client):
    client.cookies.clear()
    auth.create_user("quantri", "mat-khau-thu-nghiem-123")
    r = client.post("/api/admin/login", json={"username": "quantri", "password": "mat-khau-thu-nghiem-123"},
                    headers=CSRF)
    assert r.status_code == 200
    yield client
    client.cookies.clear()


def test_analytics_id_from_admin_settings(admin):
    cfg = admin.get("/api/admin/settings/kinh-doanh").json()["value"]
    bad = dict(cfg, ga4_id="UA-12345-1")
    assert admin.put("/api/admin/settings/kinh-doanh", json=bad, headers=CSRF).status_code == 400
    bad = dict(cfg, ga4_id='G-ABC"><script>')
    assert admin.put("/api/admin/settings/kinh-doanh", json=bad, headers=CSRF).status_code == 400
    ok = dict(cfg, ga4_id=" g-abc123xyz ", ten_don_vi="Văn phòng Thử")
    assert admin.put("/api/admin/settings/kinh-doanh", json=ok, headers=CSRF).json()["value"]["ga4_id"] == "G-ABC123XYZ"
    landing = admin.get("/").text
    assert 'window.NAC_GA4 = "G-ABC123XYZ";' in landing and "NAC_SPA" not in landing
    assert "<title>" in landing and "Văn phòng Thử" in landing
    app = admin.get("/app").text
    assert 'window.NAC_GA4 = "G-ABC123XYZ"; window.NAC_SPA = true;' in app
    assert app.index("NAC_GA4") < app.index("/static/js/track.js")


@pytest.mark.parametrize("path, must, must_not", [
    ("/thanh-lap-cong-ty", ["Thành lập mới công ty TNHH 1 TV", "Thành lập hộ kinh doanh", "Gói Khởi nghiệp",
                            "Thành lập công ty cần chuẩn bị gì?"],
     ["Tăng vốn công ty TNHH 1 TV", "Thay đổi đăng ký doanh nghiệp</b>"]),
    ("/thay-doi-dang-ky-kinh-doanh", ["Tăng vốn công ty TNHH 1 TV", "Thay đổi nội dung ĐKKD", "Chuyển nhượng",
                                      "Thay đổi đăng ký doanh nghiệp", "10 ngày"],
     ["Thành lập mới công ty TNHH 1 TV", "Gói Khởi nghiệp"]),
])
def test_ads_landing_pages(client, path, must, must_not):
    r = client.get(path)
    assert r.status_code == 200
    html = r.text
    for text in must:
        assert text in html, text
    for text in must_not:
        assert text not in html, text
    assert f'<link rel="canonical" href="http://testserver{path}">' in html
    assert f'data-trang="{path[1:]}"' in html
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert json.loads(m.group(1))
    assert "<h1>" in html and "/app#/wizard?t=" in html
    assert f"<loc>http://testserver{path}</loc>" in client.get("/sitemap.xml").text


def test_google_ads_settings_and_tags(admin):
    cfg = admin.get("/api/admin/settings/kinh-doanh").json()["value"]
    for bad in [dict(cfg, google_ads_id="123456789"), dict(cfg, google_ads_id="AW-12"),
                dict(cfg, google_ads_id="AW-123456789", google_ads_nhan_lead="có dấu cách!"),
                dict(cfg, google_ads_id="", google_ads_nhan_lead="AbCdEf123")]:
        assert admin.put("/api/admin/settings/kinh-doanh", json=bad, headers=CSRF).status_code == 400, bad
    ok = dict(cfg, google_ads_id=" aw-123456789 ", google_ads_nhan_lead="AbC-dEf_123")
    saved = admin.put("/api/admin/settings/kinh-doanh", json=ok, headers=CSRF).json()["value"]
    assert (saved["google_ads_id"], saved["google_ads_nhan_lead"]) == ("AW-123456789", "AbC-dEf_123")
    for path in ("/", "/thanh-lap-cong-ty", "/app"):
        html = admin.get(path).text
        assert 'window.NAC_ADS = "AW-123456789"; window.NAC_ADS_LEAD = "AbC-dEf_123";' in html, path
        assert "NAC_GA4" not in html


def test_gclid_kept_with_lead():
    from services import leads
    lead = leads.parse_lead({"name": "Nguyễn Văn Thử", "phone": "0901234567", "consent": True,
                             "source": {"gclid": "Cj0KCQ-thu", "landing": "/thanh-lap-cong-ty"}})
    assert lead["source"] == {"gclid": "Cj0KCQ-thu", "landing": "/thanh-lap-cong-ty"}


def test_procedure_page_for_every_template(client):
    templates = client.get("/api/templates").json()["templates"]
    sitemap = client.get("/sitemap.xml").text
    for t in templates:
        r = client.get(f"/thu-tuc/{t['id']}")
        assert r.status_code == 200, t["id"]
        html = r.text
        assert t["display_name"] in html and f'/app#/wizard?t={t["id"]}"' in html
        assert f'<link rel="canonical" href="http://testserver/thu-tuc/{t["id"]}">' in html
        assert f"<loc>http://testserver/thu-tuc/{t['id']}</loc>" in sitemap
        docs = re.search(r'<ol class="docs" id="ds-van-ban">(.*?)</ol>', html, re.S).group(1)
        assert docs.count("<li>") == len(set(re.findall(r"<li>([^<(]+?)\s*(?:<|$)", docs)))  # không trùng tên
        assert ".docx" not in docs and not re.search(r"\d{3,}", docs) and "dkdn" not in docs
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        types = {d["@type"] for d in json.loads(m.group(1))}
        assert types == {"ProfessionalService", "FAQPage", "BreadcrumbList"}
        assert 'href="/#bang-gia"' in html  # menu về các mục của trang chủ


def test_procedure_page_content(client):
    html = client.get("/thu-tuc/thanh-lap-moi-cong-ty-tnhh-2-tv").text
    for text in ["Giấy đề nghị", "Điều lệ", "Danh sách thành viên", "Danh sách chủ sở hữu hưởng lợi",
                 "Ngành nghề kinh doanh", "VNeID", "Gói Khởi nghiệp", "Gói Cơ bản", "Thành lập mới công ty Cổ Phần"]:
        assert text in html, text
    assert "Gói Hộ kinh doanh" not in html and "Thay đổi đăng ký doanh nghiệp</b>" not in html
    html = client.get("/thu-tuc/chuyen-nhuong-cong-ty-tnhh-2-tv").text
    assert html.count("Xác nhận góp vốn") == 1 and "tùy trường hợp" in html


def test_unknown_procedure_404(client):
    assert client.get("/thu-tuc/khong-co-thu-tuc-nay").status_code == 404
    assert client.get("/thu-tuc/..%2F..%2Fconfig").status_code == 404
