"""Đối tác giới thiệu khách: mỗi đối tác một mã, link dạng /?ref=<mã>.

Khách vào qua link được gắn mã (static/js/track.js giữ mã 30 ngày trên máy khách), mã đi kèm thông tin khách khi tải hồ
sơ (leads.ref). Hoa hồng = tỷ lệ % của đối tác × doanh thu đã ghi ở các khách đối tác đó giới thiệu.
"""
import re
from typing import Any, Dict, List, Optional

CODE_RE = re.compile(r"[a-z0-9][a-z0-9-]{2,29}")
BOUGHT = ("da_coc", "da_mua", "ke_toan")


def normalize_code(raw: Any) -> str:
    return str(raw or "").strip().lower()


def _clean(data: Dict[str, Any], partial: bool = False) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if not partial or "code" in data:
        code = normalize_code(data.get("code"))
        if not CODE_RE.fullmatch(code):
            raise ValueError("Mã đối tác 3–30 ký tự: chữ thường không dấu, số, dấu gạch ngang (vd ketoan-an)")
        out["code"] = code
    if not partial or "name" in data:
        name = " ".join(str(data.get("name") or "").split())[:120]
        if not name:
            raise ValueError("Thiếu tên đối tác")
        out["name"] = name
    if not partial or "phone" in data:
        phone = re.sub(r"[^\d]", "", str(data.get("phone") or ""))
        if phone and not re.fullmatch(r"0\d{9}", phone):
            raise ValueError("Số điện thoại đối tác gồm 10 chữ số, bắt đầu bằng 0")
        out["phone"] = phone
    for key, label, hi in (("pct", "Tỷ lệ hoa hồng", 100), ("paid", "Số tiền đã trả", 10**12)):
        if not partial or key in data:
            try:
                val = int(re.sub(r"[^\d]", "", str(data.get(key) or "")) or 0)
            except ValueError:
                raise ValueError(f"{label} phải là số")
            if not 0 <= val <= hi:
                raise ValueError(f"{label} từ 0 đến {hi}" + ("%" if key == "pct" else ""))
            out[key] = val
    if not partial or "note" in data:
        out["note"] = str(data.get("note") or "")[:2000]
    if "active" in data:
        out["active"] = 1 if data.get("active") else 0
    return out


def create(data: Dict[str, Any], user_id=None) -> Dict[str, Any]:
    import sqlite3
    from services import admin_db
    rec = _clean(data)
    with admin_db.connect() as conn:
        try:
            cur = conn.execute("INSERT INTO partners(code, name, phone, pct, paid, note, created_at)"
                               " VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (rec["code"], rec["name"], rec["phone"], rec["pct"], rec["paid"], rec["note"],
                                admin_db.now_iso()))
        except sqlite3.IntegrityError:
            raise ValueError(f"Mã {rec['code']} đã có đối tác khác dùng")
        admin_db.audit(conn, user_id, "partner_create", rec["code"])
        return dict(conn.execute("SELECT * FROM partners WHERE id = ?", (cur.lastrowid,)).fetchone())


def update(partner_id: int, data: Dict[str, Any], user_id=None) -> Dict[str, Any]:
    from services import admin_db
    fields = _clean(data, partial=True)
    fields.pop("code", None)  # đổi mã làm mất liên kết với khách cũ: không cho đổi
    if not fields:
        raise ValueError("Không có gì để cập nhật")
    with admin_db.connect() as conn:
        sets = ", ".join(f"{k} = ?" for k in fields)
        cur = conn.execute(f"UPDATE partners SET {sets}, updated_at = ? WHERE id = ?",
                           (*fields.values(), admin_db.now_iso(), partner_id))
        if cur.rowcount == 0:
            raise KeyError(partner_id)
        admin_db.audit(conn, user_id, "partner_update", f"{partner_id}: {', '.join(fields)}")
        return dict(conn.execute("SELECT * FROM partners WHERE id = ?", (partner_id,)).fetchone())


def by_code(code: str) -> Optional[Dict[str, Any]]:
    from services import admin_db
    code = normalize_code(code)
    if not code:
        return None
    with admin_db.connect() as conn:
        row = conn.execute("SELECT * FROM partners WHERE code = ?", (code,)).fetchone()
    return dict(row) if row else None


def names() -> Dict[str, str]:
    from services import admin_db
    with admin_db.connect() as conn:
        return {r["code"]: r["name"] for r in conn.execute("SELECT code, name FROM partners")}


def report() -> Dict[str, Any]:
    """Danh sách đối tác kèm số khách, số nhờ nộp, số đã mua, doanh thu, hoa hồng, còn phải trả;
    và các mã lạ (khách có ?ref= không trùng đối tác nào)."""
    from services import admin_db
    marks = ",".join("?" * len(BOUGHT))
    with admin_db.connect() as conn:
        partners = [dict(r) for r in conn.execute("SELECT * FROM partners ORDER BY active DESC, created_at DESC")]
        stats = {r["ref"]: dict(r) for r in conn.execute(
            f"SELECT ref, COUNT(*) AS so_khach, SUM(delegated) AS nho_nop,"
            f" SUM(CASE WHEN status IN ({marks}) THEN 1 ELSE 0 END) AS da_mua,"
            f" SUM(revenue) AS doanh_thu, MAX(created_at) AS gan_nhat"
            f" FROM leads WHERE ref IS NOT NULL AND ref != '' GROUP BY ref", BOUGHT)}
    out: List[Dict[str, Any]] = []
    for p in partners:
        st = stats.pop(p["code"], {})
        doanh_thu = int(st.get("doanh_thu") or 0)
        hoa_hong = int(round(doanh_thu * p["pct"] / 100))
        out.append(dict(p, so_khach=int(st.get("so_khach") or 0), nho_nop=int(st.get("nho_nop") or 0),
                        da_mua=int(st.get("da_mua") or 0), doanh_thu=doanh_thu, hoa_hong=hoa_hong,
                        con_no=hoa_hong - p["paid"], gan_nhat=st.get("gan_nhat")))
    unknown = [{"code": k, "so_khach": int(v["so_khach"])} for k, v in sorted(stats.items())]
    return {"partners": out, "unknown": unknown}
