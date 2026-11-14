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
        assert f'/app#/wizard?t={t["id"]}"' in html, t["id"]
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
