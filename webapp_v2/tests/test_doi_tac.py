"""Đối tác giới thiệu: mã ?ref=, đếm khách, hoa hồng theo % doanh thu, mã lạ, email báo, nâng cấp CSDL cũ."""
import json
import sqlite3

import pytest

import config
from conftest import build_payload
from services import admin_db, auth, doi_tac, kinh_doanh, leads

CSRF = {auth.CSRF_HEADER: auth.CSRF_VALUE}


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ADMIN_DB_PATH", tmp_path / "admin.sqlite3")
    monkeypatch.setattr(config, "LEAD_REQUIRED", True)
    monkeypatch.setattr(leads, "notify", lambda rec: True)


@pytest.fixture
def admin(client):
    client.cookies.clear()
    auth.create_user("quantri", "mat-khau-thu-nghiem-123")
    r = client.post("/api/admin/login", json={"username": "quantri", "password": "mat-khau-thu-nghiem-123"},
                    headers=CSRF)
    assert r.status_code == 200
    yield client
    client.cookies.clear()


def lead_from(client, ref, delegated=False, phone="0901234567"):
    payload, _, _ = build_payload("Thành lập mới công ty TNHH 2 TV", 2)
    payload["lead"] = {"name": "Nguyễn Văn Thử", "phone": phone, "role": "chu_dn", "consent": True,
                       "delegated": delegated, "source": {"ref": ref} if ref else {}}
    assert client.post("/api/documents/generate", json=payload).status_code == 200
    return leads.list_leads()[0]


def test_partner_validation(admin):
    ok = {"code": "Ketoan-An", "name": "Kế toán Thử", "phone": "0912 345 678", "pct": "10"}
    r = admin.post("/api/admin/partners", json=ok, headers=CSRF)
    assert r.status_code == 200
    p = r.json()["partner"]
    assert (p["code"], p["phone"], p["pct"], p["active"]) == ("ketoan-an", "0912345678", 10, 1)
    for bad, msg in [(dict(ok), "đã có"), (dict(ok, code="a b"), "Mã đối tác"), (dict(ok, code="ab"), "Mã đối tác"),
                     (dict(ok, code="moi1", pct="150"), "0 đến 100"), (dict(ok, code="moi2", name=" "), "tên"),
                     (dict(ok, code="moi3", phone="123"), "10 chữ số")]:
        r = admin.post("/api/admin/partners", json=bad, headers=CSRF)
        assert r.status_code == 400 and msg in r.json()["detail"], bad
    # Không đổi được mã (khách cũ sẽ mất liên kết)
    r = admin.patch(f"/api/admin/partners/{p['id']}", json={"code": "khac", "pct": 15}, headers=CSRF)
    assert r.json()["partner"]["code"] == "ketoan-an" and r.json()["partner"]["pct"] == 15
    assert admin.patch("/api/admin/partners/999", json={"pct": 1}, headers=CSRF).status_code == 404


def test_commission_report(admin):
    p = doi_tac.create({"code": "ketoan-an", "name": "Kế toán Thử", "pct": 10})
    lead_from(admin, "KETOAN-AN", delegated=True)
    second = lead_from(admin, "ketoan-an", phone="0909999999")
    lead_from(admin, "ma-la")
    lead_from(admin, None)
    assert second["ref"] == "ketoan-an"
    leads.update(second["id"], {"status": "da_mua", "revenue": "3.200.000"})
    doi_tac.update(p["id"], {"paid": "100.000"})
    rep = admin.get("/api/admin/partners").json()
    row = rep["partners"][0]
    assert (row["so_khach"], row["nho_nop"], row["da_mua"]) == (2, 1, 1)
    assert (row["doanh_thu"], row["hoa_hong"], row["con_no"]) == (3200000, 320000, 220000)
    assert rep["unknown"] == [{"code": "ma-la", "so_khach": 1}]
    # Danh sách khách hiện tên đối tác
    assert admin.get("/api/admin/leads").json()["partners"] == {"ketoan-an": "Kế toán Thử"}


def test_partners_need_login(client):
    client.cookies.clear()
    assert client.get("/api/admin/partners").status_code == 401
    assert client.post("/api/admin/partners", json={}, headers=CSRF).status_code == 401


def test_email_names_partner():
    doi_tac.create({"code": "ketoan-an", "name": "Kế toán Thử", "pct": 10})
    rec = leads.build(leads.parse_lead({"name": "Nguyễn Văn Thử", "phone": "0901234567", "consent": True,
                                        "source": {"ref": "ketoan-an"}}),
                      "tang-von-cong-ty-tnhh-1-tv", "Tăng vốn công ty TNHH 1 TV", {})
    assert "Đối tác giới thiệu: Kế toán Thử (ketoan-an, hoa hồng 10%)" in leads.email_text(rec, kinh_doanh.get())[1]
    rec["source"]["ref"] = "chua-co"
    assert "Mã giới thiệu chưa có trong danh sách đối tác: chua-co" in leads.email_text(rec, kinh_doanh.get())[1]


def test_upgrade_fills_ref_for_old_leads(tmp_path, monkeypatch):
    path = tmp_path / "cu.sqlite3"
    conn = sqlite3.connect(str(path))
    for v, sql in enumerate(admin_db.MIGRATIONS[:5], start=1):
        conn.executescript(sql)
        conn.execute(f"PRAGMA user_version = {v}")
    conn.execute("INSERT INTO leads(created_at, updated_at, name, phone, consent_text, source) VALUES ('x', 'x', 'A', '0901234567', 'c', ?)",
                 (json.dumps({"ref": "KeToan-An"}),))
    conn.execute("INSERT INTO leads(created_at, updated_at, name, phone, consent_text, source) VALUES ('x', 'x', 'B', '0901234568', 'c', '{}')")
    conn.commit()
    conn.close()
    monkeypatch.setattr(config, "ADMIN_DB_PATH", path)
    with admin_db.connect() as c:
        assert [r[0] for r in c.execute("SELECT ref FROM leads ORDER BY id")] == ["ketoan-an", None]
        assert c.execute("PRAGMA user_version").fetchone()[0] == len(admin_db.MIGRATIONS)
