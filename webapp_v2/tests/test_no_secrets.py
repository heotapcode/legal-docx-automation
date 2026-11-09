"""Chặn khóa bí mật (API key, token, private key) bị viết thẳng vào mã nguồn.

Quét mọi file được git theo dõi trong repo. Khóa phải đọc từ biến môi trường hoặc file .env (đã có trong .gitignore).
Nếu test này báo lỗi: xóa khóa khỏi file, đọc từ biến môi trường, và thu hồi/đổi khóa vì nó đã bị lộ.
"""
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

SECRET_PATTERNS = {
    "Telegram bot token": re.compile(r"\b\d{8,10}:AA[0-9A-Za-z_-]{30,}"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}"),
    "Google AI Studio key": re.compile(r"\bAQ\.[0-9A-Za-z_-]{40,}"),
    "Anthropic API key": re.compile(r"\bsk-ant-[0-9A-Za-z_-]{20,}"),
    "OpenAI API key": re.compile(r"\bsk-(?:proj-)?[0-9A-Za-z_-]{32,}"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{50,})"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Slack token": re.compile(r"\bxox[abprs]-[0-9A-Za-z-]{10,}"),
    "Private key": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
}
MAX_BYTES = 5 * 1024 * 1024


def tracked_files():
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO_ROOT, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("Không chạy được git ls-files")
    return [REPO_ROOT / p for p in out.decode("utf-8").split("\0") if p]


def find_secrets(text):
    return [(label, m.group(0)) for label, rx in SECRET_PATTERNS.items() for m in rx.finditer(text)]


def test_patterns_detect_examples():
    # Ghép chuỗi lúc chạy để chính file test không chứa mẫu khóa
    samples = {
        "Telegram bot token": "123456789" + ":AA" + "x" * 33,
        "Google API key": "AI" + "za" + "y" * 35,
        "Google AI Studio key": "AQ" + ".Ab8" + "z" * 45,
        "Anthropic API key": "sk-" + "ant-" + "a" * 30,
        "GitHub token": "gh" + "p_" + "b" * 36,
        "Private key": "-----BEGIN " + "PRIVATE KEY-----",
    }
    for label, sample in samples.items():
        assert label in {lbl for lbl, _ in find_secrets(f"KEY = '{sample}'")}, label
    assert find_secrets('TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")') == []


def test_no_secrets_in_tracked_files():
    found = []
    for path in tracked_files():
        if not path.is_file() or path.stat().st_size > MAX_BYTES:
            continue
        data = path.read_bytes()
        if b"\0" in data[:8192]:  # file nhị phân (docx, ảnh...)
            continue
        for label, value in find_secrets(data.decode("utf-8", errors="ignore")):
            found.append(f"{path.relative_to(REPO_ROOT)}: {label} {value[:12]}…")
    assert not found, "Phát hiện khóa bí mật trong mã nguồn:\n" + "\n".join(found)
