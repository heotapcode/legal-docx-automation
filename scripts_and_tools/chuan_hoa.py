#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chuan_hoa.py — Script chuẩn hóa template Word tự động
======================================================
Usage:
    python chuan_hoa.py
    python chuan_hoa.py "Mẫu Chuyển nhượng Công ty TNHH 2 TV"
    python chuan_hoa.py "C:\\đường\\dẫn\\đầy\\đủ"

Quy trình:
    1. Đọc toàn bộ text từ file Word trong folder
    2. Phát hiện giá trị cứng (MST, CCCD, ngày sinh, email, số điện thoại, tên người)
    3. Hiện danh sách đề xuất placeholder → người dùng xác nhận/chỉnh
    4. Backup folder gốc
    5. Tự động replace + tô vàng
    6. Cập nhật folder_keys.json
"""

import os, sys, json, re, shutil, datetime, time
import win32com.client, pythoncom

# ── Cấu hình ──────────────────────────────────────────────────────────────────
BASE_DIR         = r"c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word"
FOLDER_KEYS_JSON = os.path.join(BASE_DIR, "folder_keys.json")

# Màu terminal (ANSI)
R  = "\033[91m"; G  = "\033[92m"; Y  = "\033[93m"
B  = "\033[94m"; M  = "\033[95m"; C  = "\033[96m"
W  = "\033[97m"; DIM = "\033[2m"; RESET = "\033[0m"; BOLD = "\033[1m"

# ── Mapping từ context keyword → tên placeholder gợi ý ───────────────────────
CONTEXT_KEY_MAP = {
    # MST / Mã số thuế
    r"mã số (thuế|doanh nghiệp|dn)": "MA_SO_THUE",
    r"msdn|mst\b":                    "MA_SO_THUE",
    # CCCD / CMND
    r"định danh cá nhân":             "CCCD",
    r"số (cccd|cmnd|căn cước)":       "CCCD",
    # Ngày sinh
    r"ngày.*?sinh|sinh ngày":         "NGAY_SINH",
    r"ngày.{1,5}tháng.{1,5}năm":     "NGAY_KY",
    # Điện thoại
    r"điện thoại|phone|sdt":          "SDT",
    # Email
    r"email|e-mail":                  "EMAIL",
    # Tên người
    r"họ.{0,6}tên|ông[:\s]|bà[:\s]": "HO_TEN",
    # Tên công ty
    r"tên doanh nghiệp|tên công ty":  "TEN_CONG_TY_VN",
    # Địa chỉ
    r"địa chỉ|trụ sở":               "DIA_CHI",
    # Chức danh
    r"chức danh|chức vụ":             "CHUC_DANH",
}

# Regex pattern phát hiện giá trị cứng
DETECT_PATTERNS = [
    ("MST (10 chữ số)",        r'\b(\d{10})\b',                                 "MA_SO_THUE"),
    ("CCCD (12 chữ số)",       r'\b(\d{12})\b',                                 "CCCD"),
    ("Ngày (dd/mm/yyyy)",      r'\b(\d{2}/\d{2}/\d{4})\b',                      "NGAY_SINH"),
    ("Email",                  r'\b([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b', "EMAIL"),
    ("Số điện thoại (0x)",     r'\b(0[0-9]{8,9}(?:[.\-][0-9]{3})?)\b',          "SDT"),
    ("Số điện thoại (dấu.)",   r'\b(0\d{3}[.\-]\d{3}[.\-]\d{3})\b',            "SDT"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def clr(code, text): return f"{code}{text}{RESET}"
def header(msg): print(f"\n{BOLD}{C}{'─'*60}{RESET}\n{BOLD}{W}  {msg}{RESET}\n{BOLD}{C}{'─'*60}{RESET}")
def ok(msg):     print(f"  {G}✔{RESET}  {msg}")
def warn(msg):   print(f"  {Y}⚠{RESET}  {msg}")
def info(msg):   print(f"  {B}ℹ{RESET}  {msg}")
def sep():       print(f"  {DIM}{'·'*56}{RESET}")


def choose_folder():
    """Cho người dùng chọn folder mẫu nếu không truyền argument."""
    folders = [d for d in os.listdir(BASE_DIR)
               if os.path.isdir(os.path.join(BASE_DIR, d)) and d.startswith("Mẫu ")
               and not d.startswith("Mẫu ")]
    # Lấy tất cả folder bắt đầu bằng "Mẫu "
    folders = [d for d in os.listdir(BASE_DIR)
               if os.path.isdir(os.path.join(BASE_DIR, d)) and d.startswith("Mẫu ")]

    if not folders:
        print(clr(R, "Không tìm thấy folder mẫu nào trong: " + BASE_DIR))
        sys.exit(1)

    print(f"\n{BOLD}📁 Chọn folder mẫu cần chuẩn hóa:{RESET}\n")
    for i, f in enumerate(sorted(folders), 1):
        print(f"  {Y}{i:2}.{RESET}  {f}")
    print()
    while True:
        try:
            choice = int(input(f"  {W}Nhập số thứ tự [{Y}1-{len(folders)}{W}]: {RESET}").strip())
            if 1 <= choice <= len(folders):
                return os.path.join(BASE_DIR, sorted(folders)[choice - 1])
        except (ValueError, KeyboardInterrupt):
            pass
        warn("Vui lòng nhập số hợp lệ.")


def extract_all_texts(folder_path):
    """Đọc toàn bộ text từ tất cả file Word (không mở Word nếu có thể)."""
    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    texts = {}  # {filename: full_text}
    files = sorted([f for f in os.listdir(folder_path)
                    if (f.endswith(".doc") or f.endswith(".docx"))
                    and not f.startswith("~$")
                    and not f.startswith("_backup")])
    try:
        for fname in files:
            fpath = os.path.join(folder_path, fname)
            doc = None
            for _ in range(3):
                try:
                    doc = word.Documents.Open(fpath, ReadOnly=True, ConfirmConversions=False)
                    break
                except: time.sleep(1)
            if doc:
                texts[fname] = doc.Content.Text
                doc.Close(False)
            else:
                warn(f"Không mở được: {fname}")
    finally:
        word.Quit()
    return texts


def get_context(full_text, value, window=60):
    """Lấy đoạn text xung quanh một giá trị để hiểu ngữ cảnh."""
    idx = full_text.find(value)
    if idx == -1: return ""
    start = max(0, idx - window)
    end   = min(len(full_text), idx + len(value) + window)
    snippet = full_text[start:end].replace('\r', ' ').replace('\n', ' ').replace('\x07', ' ')
    return re.sub(r'\s{2,}', ' ', snippet).strip()


def suggest_placeholder_from_context(context_text, value, default_type):
    """Gợi ý tên placeholder dựa trên context xung quanh."""
    ctx_lower = context_text.lower()
    for pattern, key_hint in CONTEXT_KEY_MAP.items():
        if re.search(pattern, ctx_lower):
            # Áp gợi ý theo loại pattern đã phát hiện
            if key_hint == "MA_SO_THUE":
                return "MA_SO_THUE"
            elif key_hint == "CCCD":
                # Cần biết là CCCD của ai — trả về None để user chọn
                return None
            elif key_hint == "NGAY_SINH":
                return None  # user xác định là của DDPL, TV1...
            elif key_hint == "EMAIL":
                return None
            elif key_hint == "SDT":
                return None
            elif key_hint == "TEN_CONG_TY_VN":
                return "TEN_CONG_TY_VN"
    return None


def detect_candidates(texts):
    """
    Phát hiện tất cả giá trị cứng tiềm năng trong các file.
    Trả về: [(value, type_label, suggested_key, [(fname, context)...])]
    """
    # Thu thập theo value
    found = {}  # value -> {type, suggested_key, occurrences: [(fname, ctx)]}

    for fname, text in texts.items():
        for type_label, pattern, default_key in DETECT_PATTERNS:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                val = m.group(1)
                # Bỏ qua các số năm (2020-2030), số đơn giản không có nghĩa
                if re.fullmatch(r'20[0-9]{2}', val):
                    continue
                # Bỏ qua nếu đã là placeholder
                if val.startswith("[") and val.endswith("]"):
                    continue
                ctx = get_context(text, val)
                if val not in found:
                    sug = suggest_placeholder_from_context(ctx, val, default_key)
                    found[val] = {
                        "type": type_label,
                        "suggested_key": sug or default_key,
                        "occurrences": []
                    }
                found[val]["occurrences"].append((fname, ctx))

    # Loại bỏ duplicate trong occurrences
    result = []
    for val, info in sorted(found.items(), key=lambda x: x[1]["type"]):
        unique_occ = list(dict.fromkeys([(f, c) for f, c in info["occurrences"]]))
        result.append((val, info["type"], info["suggested_key"], unique_occ))

    return result


def interactive_confirm(candidates):
    """
    Hiện từng ứng cử viên, cho phép người dùng:
      - Enter: dùng gợi ý
      - Gõ key khác: dùng key tùy chỉnh
      - 's': bỏ qua (skip)
      - 'q': bỏ qua tất cả còn lại
    Trả về: [(value, placeholder_key)]
    """
    confirmed = []
    skipped   = 0
    total     = len(candidates)

    print(f"\n{BOLD}{W}  Tìm thấy {Y}{total}{W} giá trị tiềm năng. Xác nhận từng mục:{RESET}\n")

    for i, (val, type_label, sug_key, occurrences) in enumerate(candidates, 1):
        # Hiện thông tin
        files_found = list(dict.fromkeys([f for f, _ in occurrences]))
        n_occur     = len(occurrences)

        print(f"\n  {BOLD}{Y}[{i}/{total}]{RESET}  "
              f"{clr(M, type_label)}  — xuất hiện {clr(G, str(n_occur))} lần trong {len(files_found)} file")
        print(f"  Giá trị: {clr(W+BOLD, repr(val))}")
        # Ngữ cảnh (lấy 1 ví dụ)
        _, ctx = occurrences[0]
        highlighted = ctx.replace(val, clr(Y, val))
        print(f"  Ngữ cảnh: {DIM}...{RESET}{highlighted}{DIM}...{RESET}")
        print(f"  Files   : {DIM}{', '.join(files_found)}{RESET}")
        sep()

        prompt = (f"  {W}Placeholder{RESET} "
                  f"[{G}Enter{RESET}={clr(G, sug_key)} | "
                  f"{Y}gõ key khác{RESET} | "
                  f"{B}s{RESET}=bỏ qua | "
                  f"{R}q{RESET}=dừng]: ")
        try:
            ans = input(prompt).strip()
        except KeyboardInterrupt:
            print(f"\n  {R}Đã hủy.{RESET}")
            break

        if ans.lower() == 'q':
            warn("Dừng — các mục còn lại sẽ bị bỏ qua.")
            break
        elif ans.lower() == 's' or ans == '':
            if ans.lower() == 's':
                info(f"Bỏ qua: {val}")
                skipped += 1
                continue
            # Enter → dùng gợi ý
            key = sug_key

        else:
            key = ans.upper().strip().replace(" ", "_")

        if key:
            confirmed.append((val, f"[{key}]"))
            ok(f"{clr(DIM, repr(val))} → {clr(G, '['+key+']')}")
        else:
            skipped += 1

    print()
    ok(f"Xác nhận: {len(confirmed)} thay thế, bỏ qua: {skipped}")
    return confirmed


def do_backup(folder_path):
    """Backup tất cả file Word gốc vào _backup_TIMESTAMP."""
    date_str   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(folder_path, f"_backup_{date_str}")
    os.makedirs(backup_dir, exist_ok=True)
    count = 0
    for f in os.listdir(folder_path):
        src = os.path.join(folder_path, f)
        if os.path.isfile(src) and (f.endswith(".doc") or f.endswith(".docx")):
            shutil.copy2(src, os.path.join(backup_dir, f))
            count += 1
    ok(f"Đã backup {count} file → {clr(DIM, backup_dir)}")
    return backup_dir


def apply_replacements(folder_path, replacements_list):
    """Áp dụng toàn bộ replacements lên tất cả file Word trong folder."""
    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    wdYellow  = 7
    wdFindStop = 0

    files = sorted([f for f in os.listdir(folder_path)
                    if (f.endswith(".doc") or f.endswith(".docx"))
                    and not f.startswith("~$")
                    and not f.startswith("_backup")])

    total_replaced = 0
    try:
        for fname in files:
            fpath = os.path.join(folder_path, fname)
            doc = None
            for _ in range(3):
                try:
                    doc = word.Documents.Open(fpath, ReadOnly=False, ConfirmConversions=False)
                    break
                except: time.sleep(1)
            if not doc:
                warn(f"Không mở được: {fname}"); continue

            file_count = 0
            for old_val, new_placeholder in replacements_list:
                for story in doc.StoryRanges:
                    while story:
                        rng = story.Duplicate
                        while True:
                            rng.Find.ClearFormatting()
                            rng.Find.Text      = old_val
                            rng.Find.Forward   = True
                            rng.Find.Wrap      = wdFindStop
                            rng.Find.MatchCase = True
                            if not rng.Find.Execute(): break
                            rng.Text = new_placeholder
                            rng.HighlightColorIndex = wdYellow
                            rng.Collapse(0)
                            file_count += 1
                        story = story.NextStoryRange

            doc.Save()
            doc.Close(False)
            total_replaced += file_count
            if file_count > 0:
                ok(f"{fname} ({clr(G, str(file_count))} thay thế)")
            else:
                info(f"{fname} (không có thay đổi)")
    finally:
        word.Quit()

    return total_replaced


def update_folder_keys(folder_name, new_keys):
    """Thêm các key mới vào folder_keys.json."""
    data = {}
    if os.path.exists(FOLDER_KEYS_JSON):
        with open(FOLDER_KEYS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

    existing = data.get(folder_name, [])
    added = []
    for key in new_keys:
        clean_key = key.strip("[]")
        if clean_key not in existing:
            existing.append(clean_key)
            added.append(clean_key)

    data[folder_name] = existing
    with open(FOLDER_KEYS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return added


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.system("")  # Enable ANSI trên Windows

    header("SCRIPT CHUẨN HÓA TEMPLATE WORD TỰ ĐỘNG")

    # 1. Xác định folder
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if os.path.isabs(arg):
            folder_path = arg
        elif os.path.isdir(os.path.join(BASE_DIR, arg)):
            folder_path = os.path.join(BASE_DIR, arg)
        elif os.path.isdir(os.path.join(BASE_DIR, "Mẫu " + arg)):
            folder_path = os.path.join(BASE_DIR, "Mẫu " + arg)
        else:
            warn(f"Không tìm thấy folder: {arg}")
            folder_path = choose_folder()
    else:
        folder_path = choose_folder()

    folder_name = os.path.basename(folder_path)
    info(f"Folder: {clr(W+BOLD, folder_path)}")

    # 2. Đọc text
    print(f"\n{Y}⏳ Đang đọc file Word...{RESET}")
    texts = extract_all_texts(folder_path)
    if not texts:
        warn("Không tìm thấy file Word nào trong folder.")
        return
    ok(f"Đã đọc {len(texts)} file: {', '.join(texts.keys())}")

    # 3. Phát hiện candidates
    print(f"\n{Y}⏳ Đang phân tích nội dung...{RESET}")
    candidates = detect_candidates(texts)

    if not candidates:
        ok("Không phát hiện giá trị cứng nào. Folder có thể đã được chuẩn hóa!")
        return

    # 4. Người dùng xác nhận từng mục
    confirmed = interactive_confirm(candidates)

    if not confirmed:
        warn("Không có thay thế nào được xác nhận. Thoát.")
        return

    # 5. Backup
    header(f"BACKUP + ÁP DỤNG ({len(confirmed)} thay thế)")
    do_backup(folder_path)

    # 6. Apply replacements
    print(f"\n{Y}⏳ Đang áp dụng thay thế...{RESET}\n")
    total = apply_replacements(folder_path, confirmed)

    # 7. Cập nhật folder_keys.json
    new_keys   = [ph for _, ph in confirmed]
    added_keys = update_folder_keys(folder_name, new_keys)
    if added_keys:
        ok(f"Đã thêm {len(added_keys)} key mới vào folder_keys.json: "
           f"{clr(G, ', '.join(added_keys))}")
    else:
        info("Tất cả key đã tồn tại trong folder_keys.json.")

    # 8. Tóm tắt
    header("KẾT QUẢ")
    ok(f"Tổng cộng: {clr(G+BOLD, str(total))} lần thay thế, tô vàng trong {len(texts)} file.")
    ok(f"Folder    : {clr(W, folder_path)}")
    info("Kiểm tra lại các file Word để đảm bảo kết quả đúng.")
    info("Nếu cần hoàn tác, folder backup đã được tạo ở trên.")
    print()


if __name__ == "__main__":
    main()
