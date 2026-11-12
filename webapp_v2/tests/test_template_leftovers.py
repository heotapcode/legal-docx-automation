"""Mẫu Word không được còn dấu vết của lần xóa dữ liệu cũ hoặc năm ghi cứng ở dòng ngày tháng."""
import glob
import re
import unicodedata

import docx
import pytest
from docx.oxml.ns import qn

FILES = sorted(glob.glob("templates/*/*.docx"))


def paragraphs(path):
    for p in docx.Document(path).element.body.iter(qn("w:p")):
        yield unicodedata.normalize("NFC", "".join(t.text or "" for t in p.iter(qn("w:t"))))


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.split("templates/")[1])
def test_no_scrub_markers_or_hardcoded_year(path):
    for t in paragraphs(path):
        assert "ĐÃ XÓA" not in t, t
        # "ngày … tháng … năm 2026" phải dùng năm theo ngày lập ({{ ngay_lap_ngan[-4:] }})
        assert not re.search(r"tháng[\s.…_]*năm\s*20\d\d", t), t
