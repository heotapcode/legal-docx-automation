"""Danh sách chủ sở hữu hưởng lợi (Mẫu số 10): chỉ ghi người sở hữu từ 25%, tỷ lệ vào đúng nhóm cột."""
import io
import zipfile

import docx
import pytest

from conftest import build_payload
from services import render_service


def cshhl_rows(name, ty_le):
    payload, _, _ = build_payload(name, len(ty_le))
    for m, t in zip(payload["data"]["thanh_vien"], ty_le):
        m["ty_le"] = t
    z = zipfile.ZipFile(io.BytesIO(render_service.render_documents(
        template_name=name, raw_data=payload["data"], ma_nganh_list=payload["ma_nganh"],
        special_payload=payload["special_payload"])))
    blob = next(z.read(n) for n in z.namelist() if "hưởng lợi" in n)
    table = docx.Document(io.BytesIO(blob)).tables[0]
    num = next(k for k, r in enumerate(table.rows) if [c.text for c in r.cells[:2]] == ["1", "2"])
    return [[c.text for c in r.cells] for r in table.rows[num + 1:]]


def test_only_owners_from_25_percent_tnhh():
    rows = cshhl_rows("Thành lập mới công ty TNHH 2 TV", ["60", "30", "10"])
    assert [r[0] for r in rows] == ["1", "2"]
    assert rows[0][8] == "60%" and rows[0][10] == "60%"      # vốn điều lệ: trực tiếp, tổng
    assert rows[0][9] == "" and rows[0][11] == "" and rows[0][13] == ""  # gián tiếp, cổ phần: trống
    assert rows[1][8] == "30%"


def test_co_phan_uses_voting_share_columns():
    rows = cshhl_rows("Thành lập mới công ty Cổ Phần", ["50", "25", "25"])
    assert len(rows) == 3
    assert rows[0][8] == "" and rows[0][11] == "50%" and rows[0][13] == "50%"


def test_nobody_reaches_threshold_leaves_blank_row():
    rows = cshhl_rows("Thành lập mới công ty TNHH 2 TV", ["20", "20", "20"])
    assert len(rows) == 1 and not any(rows[0])
