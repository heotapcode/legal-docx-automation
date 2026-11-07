"""Đăng nhập quản trị (Mục 10.1): mật khẩu băm scrypt, phiên lưu trong SQLite, chống dò mật khẩu, chống CSRF.

- Mật khẩu: hashlib.scrypt (thư viện chuẩn), muối ngẫu nhiên, so sánh hằng thời gian.
- Phiên: mã ngẫu nhiên 256 bit trong cookie HttpOnly + SameSite=Strict; CSDL chỉ lưu SHA-256 của mã,
  nên lộ file CSDL không dùng được để đăng nhập.
- Dò mật khẩu: quá MAX_FAILED lần sai trong LOCK_MINUTES phút cho một tên đăng nhập -> tạm khóa.
- CSRF: yêu cầu thay đổi dữ liệu phải có header X-Requested-With: nac-admin. Trình duyệt không gửi
  header tùy chỉnh sang trang khác nếu CORS không cho phép (CORS chỉ cho Content-Type), nên trang lạ
  không giả mạo được yêu cầu dù cookie có được gửi kèm.
"""
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Request

import config
from services import admin_db

COOKIE_NAME = "nac_admin_session"
CSRF_HEADER = "X-Requested-With"
CSRF_VALUE = "nac-admin"
MIN_PASSWORD_LENGTH = 10
MAX_FAILED = 5
LOCK_MINUTES = 15
ROLES = ("admin",)

_SCRYPT = dict(n=2 ** 14, r=8, p=1, dklen=32)


class LoginLocked(Exception):
    """Tên đăng nhập đang bị tạm khóa vì sai mật khẩu nhiều lần."""


# ---------- Mật khẩu ----------

def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, **_SCRYPT)
    return f"scrypt${_SCRYPT['n']}${_SCRYPT['r']}${_SCRYPT['p']}${_b64(salt)}${_b64(dk)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt, dk = stored.split("$")
        if algo != "scrypt":
            return False
        expected = base64.b64decode(dk)
        got = hashlib.scrypt(password.encode("utf-8"), salt=base64.b64decode(salt),
                             n=int(n), r=int(r), p=int(p), dklen=len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(got, expected)


# Băm sẵn một mật khẩu giả: khi tên đăng nhập không tồn tại vẫn tốn thời gian như khi sai mật khẩu
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def check_password_policy(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Mật khẩu phải có ít nhất {MIN_PASSWORD_LENGTH} ký tự")


# ---------- Tài khoản ----------

def create_user(username: str, password: str, role: str = "admin") -> int:
    username = username.strip()
    if not username:
        raise ValueError("Tên đăng nhập không được để trống")
    if role not in ROLES:
        raise ValueError(f"Vai trò không hợp lệ: {role}")
    check_password_policy(password)
    with admin_db.connect() as conn:
        if conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
            raise ValueError(f"Tên đăng nhập đã tồn tại: {username}")
        cur = conn.execute("INSERT INTO users(username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                           (username, hash_password(password), role, admin_db.now_iso()))
        admin_db.audit(conn, cur.lastrowid, "user.create", username)
        return cur.lastrowid


def set_password(username: str, password: str) -> None:
    check_password_policy(password)
    with admin_db.connect() as conn:
        row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if not row:
            raise ValueError(f"Không có tài khoản: {username}")
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(password), row["id"]))
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (row["id"],))  # đăng xuất mọi nơi
        admin_db.audit(conn, row["id"], "user.password", username)


def set_active(username: str, active: bool) -> None:
    with admin_db.connect() as conn:
        row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if not row:
            raise ValueError(f"Không có tài khoản: {username}")
        conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if active else 0, row["id"]))
        if not active:
            conn.execute("DELETE FROM sessions WHERE user_id = ?", (row["id"],))
        admin_db.audit(conn, row["id"], "user.enable" if active else "user.disable", username)


def list_users():
    with admin_db.connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, username, role, is_active, created_at FROM users ORDER BY username")]


# ---------- Đăng nhập ----------

def _recent_failures(conn, username: str) -> int:
    since = (datetime.now(timezone.utc) - timedelta(minutes=LOCK_MINUTES)).isoformat(timespec="seconds")
    # Chỉ đếm các lần sai sau lần đăng nhập đúng gần nhất
    last_ok = conn.execute("SELECT MAX(at) FROM login_attempts WHERE username = ? AND success = 1",
                           (username,)).fetchone()[0]
    since = max(since, last_ok or since)
    return conn.execute("SELECT COUNT(*) FROM login_attempts WHERE username = ? AND success = 0 AND at > ?",
                        (username, since)).fetchone()[0]


def authenticate(username: str, password: str, ip: Optional[str] = None) -> Optional[dict]:
    """Tài khoản nếu đúng; None nếu sai. Raise LoginLocked nếu đang tạm khóa (không kiểm tra mật khẩu)."""
    username = (username or "").strip()
    with admin_db.connect() as conn:
        if _recent_failures(conn, username) >= MAX_FAILED:
            raise LoginLocked()
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        ok = verify_password(password or "", row["password_hash"] if row else _DUMMY_HASH)
        ok = ok and row is not None and bool(row["is_active"])
        conn.execute("INSERT INTO login_attempts(username, ip, at, success) VALUES (?, ?, ?, ?)",
                     (username, ip, admin_db.now_iso(), 1 if ok else 0))
        if ok:
            admin_db.audit(conn, row["id"], "login", ip or "")
        return {"id": row["id"], "username": row["username"], "role": row["role"]} if ok else None


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def create_session(user_id: int, ip: Optional[str] = None) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    with admin_db.connect() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now.isoformat(timespec="seconds"),))
        conn.execute("INSERT INTO sessions(token_hash, user_id, created_at, expires_at, ip) VALUES (?, ?, ?, ?, ?)",
                     (_token_hash(token), user_id, now.isoformat(timespec="seconds"),
                      (now + timedelta(hours=config.ADMIN_SESSION_HOURS)).isoformat(timespec="seconds"), ip))
    return token


def session_user(token: Optional[str]) -> Optional[dict]:
    if not token:
        return None
    with admin_db.connect() as conn:
        row = conn.execute(
            "SELECT u.id, u.username, u.role FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.token_hash = ? AND s.expires_at > ? AND u.is_active = 1",
            (_token_hash(token), admin_db.now_iso())).fetchone()
    return dict(row) if row else None


def delete_session(token: Optional[str]) -> None:
    if token:
        with admin_db.connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))


# ---------- Dùng trong route ----------

def require_csrf(request: Request) -> None:
    if request.headers.get(CSRF_HEADER) != CSRF_VALUE:
        raise HTTPException(status_code=403, detail="Thiếu header chống giả mạo yêu cầu (CSRF)")


def require_admin(request: Request) -> dict:
    """Dependency FastAPI: người dùng quản trị đang đăng nhập; yêu cầu thay đổi dữ liệu phải qua kiểm tra CSRF."""
    user = session_user(request.cookies.get(COOKIE_NAME))
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập quản trị")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        require_csrf(request)
    return user
