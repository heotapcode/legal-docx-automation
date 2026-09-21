import json
import httpx
from config import MA_NGANH_JSON, GEMINI_API_KEY

_ma_nganh_data = None

def load_ma_nganh():
    global _ma_nganh_data
    if _ma_nganh_data is None:
        try:
            with open(MA_NGANH_JSON, 'r', encoding='utf-8') as f:
                _ma_nganh_data = json.load(f)
        except Exception:
            _ma_nganh_data = []
    return _ma_nganh_data

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

async def search_ma_nganh(mo_ta: str) -> list:
    all_nganh = load_ma_nganh()
    nganh_cap5 = [n for n in all_nganh if len(n.get("ma", "")) == 5]
    
    mo_ta_norm = normalize_vi(mo_ta)
    keywords = [kw for kw in mo_ta_norm.split() if len(kw) >= 2]

    scored = []
    for n in nganh_cap5:
        ten_norm = normalize_vi(n["ten"])
        score = 0
        for kw in keywords:
            if kw in ten_norm:
                score += len(kw)
        if mo_ta_norm in ten_norm:
            score += 20
        words = ten_norm.split()
        if words and keywords and any(k in words[:3] for k in keywords):
            score += 5
        if score > 0:
            scored.append((score, n))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"ma": n["ma"], "ten": n["ten"]} for score, n in scored[:5]]
