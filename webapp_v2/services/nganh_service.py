from pathlib import Path
import json
import httpx
from config import MA_NGANH_JSON, COMBO_NGANH_JSON

_ma_nganh_data = None
_combo_nganh_data = None

def load_ma_nganh():
    global _ma_nganh_data
    if _ma_nganh_data is None:
        try:
            with open(MA_NGANH_JSON, 'r', encoding='utf-8') as f:
                _ma_nganh_data = json.load(f)
        except Exception:
            _ma_nganh_data = []
    return _ma_nganh_data

def get_all_combos():
    global _combo_nganh_data
    if _combo_nganh_data is None:
        target_path = COMBO_NGANH_JSON
        if not Path(target_path).exists():
            target_path = Path(__file__).resolve().parent.parent / "data" / "combo_nganh.json"
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                _combo_nganh_data = json.load(f)
        except Exception:
            _combo_nganh_data = []
    return _combo_nganh_data

def normalize_vi(text: str) -> str:
    VIET_MAP = {
        'à':'a','á':'a','ả':'a','ã':'a','ạ':'a',
        'ă':'a','ắ':'a','ặ':'a','ằ':'a','ẳ':'a','ẵ':'a',
        'â':'a','ấ':'a','ầ':'a','ẩ':'a','ẫ':'a','ậ':'a',
        'è':'e','é':'e','ẻ':'e','ẽ':'e','ẹ':'e',
        'ê':'e','ế':'e','ề':'e','ể':'e','ễ':'e','ệ':'e',
        'ì':'i','í':'i','ỉ':'i','ĩ':'i','ị':'i',
        'ò':'o','ó':'o','ỏ':'o','õ':'o','ọ':'o',
        'ô':'o','ố':'o','ồ':'o','ổ':'o','ỗ':'o','ộ':'o',
        'ơ':'o','ớ':'o','ờ':'o','ở':'o','ỡ':'o','ợ':'o',
        'ù':'u','ú':'u','ủ':'u','ũ':'u','ụ':'u',
        'ư':'u','ứ':'u','ừ':'u','ử':'u','ữ':'u','ự':'u',
        'ỳ':'y','ý':'y','ỷ':'y','ỹ':'y','ỵ':'y','đ':'d',
        'À':'a','Á':'a','Ả':'a','Ã':'a','Ạ':'a',
        'Ă':'a','Ắ':'a','Ặ':'a','Ằ':'a','Ẳ':'a','Ẵ':'a',
        'Â':'a','Ấ':'a','Ầ':'a','Ẩ':'a','Ẫ':'a','Ậ':'a',
        'È':'e','É':'e','Ẻ':'e','Ẽ':'e','Ẹ':'e',
        'Ê':'e','Ế':'e','Ề':'e','Ể':'e','Ễ':'e','Ệ':'e',
        'Ì':'i','Í':'i','Ỉ':'i','Ĩ':'i','Ị':'i',
        'Ò':'o','Ó':'o','Ỏ':'o','Õ':'o','Ọ':'o',
        'Ô':'o','Ố':'o','Ồ':'o','Ổ':'o','Ỗ':'o','Ộ':'o',
        'Ơ':'o','Ớ':'o','Ờ':'o','Ở':'o','Ỡ':'o','Ợ':'o',
        'Ù':'u','Ú':'u','Ủ':'u','Ũ':'u','Ụ':'u',
        'Ư':'u','Ứ':'u','Ừ':'u','Ử':'u','Ữ':'u','Ự':'u',
        'Ỳ':'y','Ý':'y','Ỷ':'y','Ỹ':'y','Ỵ':'y','Đ':'d',
    }
    return text.lower().translate(str.maketrans(VIET_MAP))

OLD_TO_NEW_2026 = {
    "6201": ["6211", "6219"],
    "6202": ["6220"],
    "6209": ["6290"],
    "4511": ["4661", "4781"],
    "4512": ["4661", "4781"],
    "4513": ["4661", "4781"],
    "4520": ["9531", "9532"],
    "4530": ["4662", "4782"],
    "4540": ["4663", "4783", "9532"],
}

async def search_ma_nganh(query: str, limit: int = 15) -> list:
    q = (query or "").strip()
    if not q:
        return []

    data = load_ma_nganh()
    q_norm = normalize_vi(q)
    is_num = q.isdigit()

    results = []
    seen_codes = set()

    # 1. Alias conversion from old VSIC 2018 codes (QĐ 27) to new VSIC 2026 (QĐ 36)
    if is_num and q in OLD_TO_NEW_2026:
        targets = OLD_TO_NEW_2026[q]
        for it in data:
            if it.get("ma") in targets and it.get("ma") not in seen_codes:
                results.append({
                    "score": 110,
                    "ma": it.get("ma"),
                    "ten": it.get("ten"),
                    "cap1": it.get("cap1", ""),
                    "sub_items": it.get("sub_items", []),
                    "match_note": f"Quy đổi từ mã cũ {q} (QĐ 27) sang mã mới (QĐ 36)"
                })
                seen_codes.add(it.get("ma"))

    # 2. Main search
    for it in data:
        code = it.get("ma", "")
        if code in seen_codes:
            continue

        name = it.get("ten", "")
        name_norm = normalize_vi(name)
        matched = False
        score = 0
        match_note = ""

        if is_num:
            if code == q:
                score = 100
                matched = True
            elif code.startswith(q):
                score = 85
                matched = True
            elif q in code:
                score = 65
                matched = True
            else:
                for sub in it.get("sub_items", []):
                    sub_code = sub.get("ma", "")
                    if sub_code == q or sub_code.startswith(q) or q in sub_code:
                        score = 70
                        matched = True
                        match_note = f"Khớp tiểu mục cấp 5: {sub_code} - {sub.get('ten')}"
                        break
        else:
            if q_norm == name_norm:
                score = 100
                matched = True
            elif q_norm in name_norm:
                pos = name_norm.find(q_norm)
                score = 85 - min(pos, 25)
                matched = True
            else:
                for sub in it.get("sub_items", []):
                    sub_norm = normalize_vi(sub.get("ten", ""))
                    if q_norm in sub_norm:
                        score = 55
                        matched = True
                        match_note = f"Khớp chi tiết: {sub.get('ten')}"
                        break

        if matched:
            results.append({
                "score": score,
                "ma": code,
                "ten": name,
                "cap1": it.get("cap1", ""),
                "sub_items": it.get("sub_items", []),
                "match_note": match_note
            })
            seen_codes.add(code)

    # Sort results by relevance score descending, then code ascending
    results.sort(key=lambda x: (-x["score"], x["ma"]))
    return results[:limit]
