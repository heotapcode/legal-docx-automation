import re
from typing import Any

def so_thanh_chu(s: Any) -> str:
    if s is None:
        return ""
    # Validate input: reject negative numbers or decimal numbers if needed, or extract integer digits
    s_str = str(s).strip()
    if not s_str:
        return ""
    
    # Clean money string: remove separators '.' and ',' and spaces
    digits = re.sub(r"[^\d]", "", s_str)
    if not digits:
        return s_str
    
    n = int(digits)
    if n == 0:
        return "Không đồng"

    don_vi = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ"]
    chu_so = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

    def doc_ba_chu_so(val: int, co_nhom_cao: bool) -> str:
        tram = val // 100
        chuc = (val % 100) // 10
        dv = val % 10
        res = ""

        if tram > 0:
            res += chu_so[tram] + " trăm "
            if chuc == 0 and dv > 0:
                res += "lẻ "
        elif co_nhom_cao:
            res += "không trăm "
            if chuc == 0 and dv > 0:
                res += "lẻ "

        if chuc > 1:
            res += chu_so[chuc] + " mươi "
            if dv == 1:
                res += "mốt "
            elif dv == 5:
                res += "lăm "
            elif dv > 0:
                res += chu_so[dv] + " "
        elif chuc == 1:
            res += "mười "
            if dv == 1:
                res += "một "
            elif dv == 5:
                res += "lăm "
            elif dv > 0:
                res += chu_so[dv] + " "
        else:
            if dv > 0:
                res += chu_so[dv] + " "

        return res.strip()

    chuoi_kq = ""
    i = 0
    temp_n = n
    while temp_n > 0:
        phan_ba = temp_n % 1000
        co_nhom_cao = (temp_n // 1000) > 0
        if phan_ba > 0:
            doc_phan_ba = doc_ba_chu_so(phan_ba, co_nhom_cao)
            if doc_phan_ba:
                prefix = don_vi[i] + " " if don_vi[i] else ""
                chuoi_kq = doc_phan_ba + " " + prefix + chuoi_kq
        temp_n = temp_n // 1000
        i += 1

    chuoi_kq = chuoi_kq.strip().capitalize()
    return chuoi_kq + " đồng"

test_cases = [
    (1005000, "Một triệu không trăm lẻ năm nghìn đồng"),
    (2000001, "Hai triệu không trăm lẻ một đồng"),
    (1050000, "Một triệu không trăm năm mươi nghìn đồng"),
    (5000000000, "Năm tỷ đồng"),
    (1500000, "Một triệu năm trăm nghìn đồng"),
    (105000, "Một trăm lẻ năm nghìn đồng"),
    (1000000, "Một triệu đồng"),
    (15, "Mười lăm đồng"),
    (21, "Hai mươi mốt đồng"),
    (101, "Một trăm lẻ một đồng"),
    (110, "Một trăm mười đồng"),
    (111, "Một trăm mười một đồng"),
    (125, "Một trăm hai mươi lăm đồng"),
    (1000000000, "Một tỷ đồng"),
    (2500000000, "Hai tỷ năm trăm triệu đồng"),
    (1000005, "Một triệu không trăm lẻ năm đồng"),
]

passed = 0
for val, expected in test_cases:
    res = so_thanh_chu(val)
    if res == expected:
        print(f"PASS: {val} -> {res}")
        passed += 1
    else:
        print(f"FAIL: {val}\n  Got:      {res}\n  Expected: {expected}")

print(f"\n{passed}/{len(test_cases)} tests passed!")
assert passed == len(test_cases)
