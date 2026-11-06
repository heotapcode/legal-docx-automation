"""Test "ảnh chụp chuẩn" (golden snapshot) cho nội dung hồ sơ sinh ra.

Với mỗi bộ mẫu, sinh hồ sơ bằng dữ liệu mẫu cố định (3 thành viên, ngày cố định) rồi so
toàn bộ chữ của từng file Word với bản đã lưu trong tests/golden/<id>.txt.
Mục đích: tái cấu trúc (bộ máy wizard, quy tắc render...) không được làm đổi nội dung hồ sơ.

Khi CỐ Ý thay đổi nội dung (sửa mẫu Word, sửa logic điền), cập nhật ảnh chụp:
    UPDATE_GOLDEN=1 pytest tests/test_golden_snapshots.py
rồi xem lại `git diff tests/golden/` trước khi commit.
"""
import datetime as _dt
import difflib
import io
import os
import re
import zipfile
from pathlib import Path

import pytest

from conftest import build_payload, list_template_names, load_schema
from services import render_service
from services.sample_data import docx_text

GOLDEN_DIR = Path(__file__).parent / "golden"
UPDATE = os.environ.get("UPDATE_GOLDEN") == "1"
FIXED_NOW = _dt.datetime(2026, 1, 15, 9, 30, 0)


class _FrozenDatetime(_dt.datetime):
    @classmethod
    def now(cls, tz=None):
        return FIXED_NOW if tz is None else FIXED_NOW.replace(tzinfo=tz)


@pytest.fixture
def frozen_time(monkeypatch):
    monkeypatch.setattr(render_service, "datetime", _FrozenDatetime)


def normalize(text: str) -> str:
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    out = "\n".join(lines).strip("\n")
    return re.sub(r"\n{3,}", "\n\n", out)


def snapshot(zip_bytes: bytes) -> str:
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    parts = []
    for name in sorted(z.namelist()):
        body = docx_text(z.read(name)) if name.endswith(".docx") else z.read(name).decode("utf-8", "replace")
        parts.append(f"===== {name} =====\n{normalize(body)}")
    return "\n\n".join(parts) + "\n"


@pytest.mark.parametrize("name", list_template_names())
def test_golden_snapshot(name, frozen_time):
    tid = load_schema(name)["id"]
    payload, _, _ = build_payload(name, 3)
    zip_bytes = render_service.render_documents(
        template_name=payload["template_name"],
        raw_data=payload["data"],
        ma_nganh_list=payload["ma_nganh"],
        special_payload=payload["special_payload"],
    )
    actual = snapshot(zip_bytes)
    path = GOLDEN_DIR / f"{tid}.txt"

    if UPDATE:
        GOLDEN_DIR.mkdir(exist_ok=True)
        path.write_text(actual, encoding="utf-8")
        return
    if not path.exists():
        pytest.fail(f"Chưa có ảnh chụp chuẩn {path.name}. Tạo bằng: UPDATE_GOLDEN=1 pytest {__file__}")

    expected = path.read_text(encoding="utf-8")
    if actual != expected:
        diff = "".join(difflib.unified_diff(
            expected.splitlines(keepends=True), actual.splitlines(keepends=True),
            fromfile=f"golden/{path.name}", tofile="hiện tại", n=2))
        pytest.fail(
            f"Nội dung hồ sơ '{name}' đã thay đổi so với ảnh chụp chuẩn.\n"
            f"Nếu thay đổi là cố ý: UPDATE_GOLDEN=1 pytest tests/test_golden_snapshots.py\n\n"
            + diff[:6000]
        )


def test_no_orphan_golden_files():
    """Mỗi file trong tests/golden/ phải ứng với một bộ mẫu còn tồn tại."""
    ids = {load_schema(n)["id"] for n in list_template_names()}
    orphans = sorted(p.name for p in GOLDEN_DIR.glob("*.txt") if p.stem not in ids)
    assert not orphans, f"Ảnh chụp không còn bộ mẫu tương ứng, hãy xóa: {orphans}"
