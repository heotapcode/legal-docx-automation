import json

with open('folder_keys.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Chuyển nhượng công ty TNHH 1 TV
if "Chuyển nhượng công ty TNHH 1 TV" in data:
    keys = data["Chuyển nhượng công ty TNHH 1 TV"]
    if "DDPL_CU_GIOI_TINH" not in keys:
        keys.insert(keys.index("DDPL_CU_NGAY_SINH") + 1, "DDPL_CU_GIOI_TINH")
    if "DDPL_GIOI_TINH" not in keys:
        keys.insert(keys.index("DDPL_NGAY_SINH") + 1, "DDPL_GIOI_TINH")
    if "NGUOI_DUOC_UY_QUYEN_GIOI_TINH" not in keys:
        keys.insert(keys.index("NGUOI_DUOC_UY_QUYEN_NGAY_SINH") + 1, "NGUOI_DUOC_UY_QUYEN_GIOI_TINH")
    if "CSHHL_GIOI_TINH" not in keys:
        keys.append("CSHHL_GIOI_TINH")

# tăng vốn công ty TNHH 2TV
if "tăng vốn công ty TNHH 2TV" in data:
    keys = data["tăng vốn công ty TNHH 2TV"]
    if "DDPL_GIOI_TINH" not in keys:
        keys.insert(keys.index("DDPL_NGAY_SINH") + 1, "DDPL_GIOI_TINH")
    if "TV2_GIOI_TINH" not in keys:
        keys.insert(keys.index("TV2_NGAY_SINH") + 1, "TV2_GIOI_TINH")

# Thay đổi nội dung ĐKKD
if "Thay đổi nội dung ĐKKD" in data:
    keys = data["Thay đổi nội dung ĐKKD"]
    if "DDPL_GIOI_TINH" not in keys:
        keys.insert(keys.index("DDPL_NGAY_SINH") + 1, "DDPL_GIOI_TINH")

with open('folder_keys.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Updated folder_keys.json")
