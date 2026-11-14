"""CSDL SQLite cho phần quản trị (Mục 10): tài khoản, phiên đăng nhập, lần đăng nhập, nhật ký.

Chỉ dùng thư viện chuẩn (sqlite3). Đường dẫn file: config.ADMIN_DB_PATH (mặc định data/admin.sqlite3).
Cấu trúc bảng được nâng cấp dần bằng MIGRATIONS, đánh số qua PRAGMA user_version:
thêm thay đổi mới vào CUỐI danh sách, không sửa các phần tử đã có.
"""
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

import config

MIGRATIONS = [
    # 1: tài khoản, phiên, lần đăng nhập, nhật ký
    """
    CREATE TABLE users (
        id            INTEGER PRIMARY KEY,
        username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        role          TEXT NOT NULL DEFAULT 'admin',
        is_active     INTEGER NOT NULL DEFAULT 1,
        created_at    TEXT NOT NULL
    );
    CREATE TABLE sessions (
        token_hash TEXT PRIMARY KEY,
        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        ip         TEXT
    );
    CREATE INDEX idx_sessions_user ON sessions(user_id);
    CREATE TABLE login_attempts (
        id       INTEGER PRIMARY KEY,
        username TEXT NOT NULL COLLATE NOCASE,
        ip       TEXT,
        at       TEXT NOT NULL,
        success  INTEGER NOT NULL
    );
    CREATE INDEX idx_login_attempts_user_at ON login_attempts(username, at);
    CREATE TABLE audit_log (
        id      INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        action  TEXT NOT NULL,
        detail  TEXT,
        at      TEXT NOT NULL
    );
    """,
    # 2: bản nháp và phiên bản bộ mẫu (Mục 10.2, 10.4)
    """
    CREATE TABLE template_drafts (
        id           TEXT PRIMARY KEY,
        template_id  TEXT NOT NULL,
        base_version INTEGER NOT NULL,
        created_by   INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at   TEXT NOT NULL
    );
    CREATE TABLE template_versions (
        id             INTEGER PRIMARY KEY,
        template_id    TEXT NOT NULL,
        version        INTEGER NOT NULL,
        source         TEXT NOT NULL,
        note           TEXT,
        legal_basis    TEXT,
        effective_from TEXT,
        created_by     INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at     TEXT NOT NULL,
        UNIQUE (template_id, version)
    );
    """,
    # 3: cấu hình dùng chung sửa được trên trang quản trị (vd người nhận ủy quyền)
    """
    CREATE TABLE settings (
        key        TEXT PRIMARY KEY,
        value      TEXT NOT NULL,
        updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        updated_at TEXT NOT NULL
    );
    """,
    # 4: khách để lại thông tin trước khi tải hồ sơ (phễu khách). Không lưu CCCD hay dữ liệu hồ sơ.
    """
    CREATE TABLE leads (
        id            INTEGER PRIMARY KEY,
        created_at    TEXT NOT NULL,
        updated_at    TEXT NOT NULL,
        name          TEXT NOT NULL,
        phone         TEXT NOT NULL,
        role          TEXT NOT NULL DEFAULT 'chu_dn',
        delegated     INTEGER NOT NULL DEFAULT 0,
        template_id   TEXT,
        template_name TEXT,
        company_name  TEXT,
        members       INTEGER,
        score         INTEGER NOT NULL DEFAULT 0,
        package       TEXT,
        source        TEXT,
        consent_text  TEXT NOT NULL,
        status        TEXT NOT NULL DEFAULT 'moi',
        revenue       INTEGER NOT NULL DEFAULT 0,
        note          TEXT
    );
    CREATE INDEX idx_leads_created ON leads(created_at);
    CREATE INDEX idx_leads_phone ON leads(phone);
    """,
]

_init_lock = threading.Lock()
_initialized = set()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def db_path() -> Path:
    return Path(config.ADMIN_DB_PATH)


def _migrate(conn: sqlite3.Connection) -> None:
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    for version, sql in enumerate(MIGRATIONS[current:], start=current + 1):
        with conn:
            conn.executescript(sql)
            conn.execute(f"PRAGMA user_version = {version}")


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Kết nối mới (mỗi yêu cầu một kết nối); tự tạo file và bảng ở lần đầu."""
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        key = str(path.resolve())
        if key not in _initialized:
            with _init_lock:
                if key not in _initialized:
                    conn.execute("PRAGMA journal_mode = WAL")
                    _migrate(conn)
                    _initialized.add(key)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def audit(conn: sqlite3.Connection, user_id, action: str, detail: str = "") -> None:
    conn.execute("INSERT INTO audit_log(user_id, action, detail, at) VALUES (?, ?, ?, ?)",
                 (user_id, action, detail, now_iso()))


def get_setting(key: str) -> Optional[str]:
    """Giá trị đã lưu của một cấu hình, None nếu chưa có (không tạo file CSDL khi chưa tồn tại)."""
    if not db_path().exists():
        return None
    with connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_setting(key: str, value: str, user_id=None) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO settings(key, value, updated_by, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_by = excluded.updated_by, "
            "updated_at = excluded.updated_at", (key, value, user_id, now_iso()))
        audit(conn, user_id, "setting.update", key)
