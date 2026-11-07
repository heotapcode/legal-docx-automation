"""Đăng nhập quản trị (Mục 10.1): services/auth.py, routes/admin_auth.py, tools/admin_user.py."""
import sqlite3

import pytest

import config
from services import admin_db, auth

CSRF = {auth.CSRF_HEADER: auth.CSRF_VALUE}
PASSWORD = "mat-khau-thu-nghiem-123"


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ADMIN_DB_PATH", tmp_path / "admin.sqlite3")
    yield tmp_path / "admin.sqlite3"


@pytest.fixture
def admin_user():
    auth.create_user("quantri", PASSWORD)
    return "quantri"


@pytest.fixture
def api(client):
    client.cookies.clear()
    yield client
    client.cookies.clear()


def login(api, username="quantri", password=PASSWORD, headers=CSRF):
    return api.post("/api/admin/login", json={"username": username, "password": password}, headers=headers)


# ---------- Mật khẩu & tài khoản ----------

def test_password_hash_roundtrip_and_salted():
    h1, h2 = auth.hash_password("abc-123-xyz"), auth.hash_password("abc-123-xyz")
    assert h1 != h2 and h1.startswith("scrypt$")
    assert auth.verify_password("abc-123-xyz", h1)
    assert not auth.verify_password("abc-123-xyZ", h1)
    assert not auth.verify_password("x", "rác")


def test_password_never_stored_in_plain_text(temp_db, admin_user):
    raw = temp_db.read_bytes() + (temp_db.with_name(temp_db.name + "-wal").read_bytes()
                                  if temp_db.with_name(temp_db.name + "-wal").exists() else b"")
    assert PASSWORD.encode() not in raw


def test_create_user_rules(admin_user):
    with pytest.raises(ValueError, match="ít nhất"):
        auth.create_user("ngan", "123")
    with pytest.raises(ValueError, match="đã tồn tại"):
        auth.create_user("QuanTri", PASSWORD)  # không phân biệt hoa thường
    assert [u["username"] for u in auth.list_users()] == ["quantri"]


def test_migrations_are_versioned(temp_db, admin_user):
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("PRAGMA user_version").fetchone()[0] == len(admin_db.MIGRATIONS)


# ---------- API ----------

def test_login_sets_httponly_strict_cookie_and_me_works(api, admin_user):
    r = login(api)
    assert r.status_code == 200 and r.json() == {"username": "quantri", "role": "admin"}
    cookie = r.headers["set-cookie"]
    assert auth.COOKIE_NAME in cookie and "HttpOnly" in cookie and "SameSite=strict" in cookie
    assert api.get("/api/admin/me").json()["username"] == "quantri"


def test_wrong_password_and_unknown_user_look_the_same(api, admin_user):
    a, b = login(api, password="sai-mat-khau-000"), login(api, username="khong-co")
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()
    assert api.get("/api/admin/me").status_code == 401


def test_session_token_stored_hashed(api, admin_user, temp_db):
    login(api)
    token = api.cookies.get(auth.COOKIE_NAME)
    conn = sqlite3.connect(str(temp_db))
    stored = [r[0] for r in conn.execute("SELECT token_hash FROM sessions")]
    assert token and token not in stored and len(stored) == 1


def test_login_requires_csrf_header(api, admin_user):
    assert login(api, headers={}).status_code == 403


def test_mutating_admin_request_requires_csrf(api, admin_user):
    login(api)
    assert api.post("/api/admin/logout").status_code == 403
    assert api.get("/api/admin/me").status_code == 200  # GET không cần
    assert api.post("/api/admin/logout", headers=CSRF).status_code == 200
    assert api.get("/api/admin/me").status_code == 401


def test_lockout_after_repeated_failures(api, admin_user):
    for _ in range(auth.MAX_FAILED):
        assert login(api, password="sai-mat-khau-000").status_code == 401
    r = login(api)  # đúng mật khẩu nhưng đang bị khóa
    assert r.status_code == 429 and "thử lại" in r.json()["detail"]


def test_success_resets_failure_count(api, admin_user):
    for _ in range(auth.MAX_FAILED - 1):
        login(api, password="sai-mat-khau-000")
    assert login(api).status_code == 200
    for _ in range(auth.MAX_FAILED - 1):
        login(api, password="sai-mat-khau-000")
    assert login(api).status_code == 200


def test_expired_session_rejected(api, admin_user, temp_db):
    login(api)
    conn = sqlite3.connect(str(temp_db))
    conn.execute("UPDATE sessions SET expires_at = '2000-01-01T00:00:00+00:00'")
    conn.commit()
    assert api.get("/api/admin/me").status_code == 401


def test_disable_and_password_change_end_sessions(api, admin_user):
    login(api)
    auth.set_password("quantri", "mat-khau-moi-456789")
    assert api.get("/api/admin/me").status_code == 401
    assert login(api, password="mat-khau-moi-456789").status_code == 200
    auth.set_active("quantri", False)
    assert api.get("/api/admin/me").status_code == 401
    assert login(api, password="mat-khau-moi-456789").status_code == 401


def test_audit_log_records_actions(temp_db, api, admin_user):
    login(api)
    conn = sqlite3.connect(str(temp_db))
    assert [r[0] for r in conn.execute("SELECT action FROM audit_log ORDER BY id")] == ["user.create", "login"]


# ---------- Dòng lệnh ----------

def test_cli_create_and_list(monkeypatch, capsys):
    from tools import admin_user

    answers = iter([PASSWORD, PASSWORD])
    monkeypatch.setattr(admin_user.getpass, "getpass", lambda prompt="": next(answers))
    assert admin_user.main(["create", "nhanvien"]) == 0
    assert admin_user.main(["list"]) == 0
    assert "nhanvien\tadmin\thoạt động" in capsys.readouterr().out


def test_cli_rejects_mismatched_password(monkeypatch, capsys):
    from tools import admin_user

    answers = iter([PASSWORD, PASSWORD + "x"])
    monkeypatch.setattr(admin_user.getpass, "getpass", lambda prompt="": next(answers))
    assert admin_user.main(["create", "nhanvien"]) == 1
    assert "không khớp" in capsys.readouterr().err
