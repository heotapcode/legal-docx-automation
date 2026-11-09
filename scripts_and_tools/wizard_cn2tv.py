#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wizard_cn2tv.py — Wizard Chuyển nhượng Công ty TNHH 2 TV
=========================================================
State machine + file generator cho luồng chuyển nhượng phức tạp.
"""

import os, json, shutil, tempfile, zipfile, datetime, time, re, copy
import asyncio
import httpx
import pythoncom
import win32com.client
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# ── Constants ─────────────────────────────────────────────────────────────────
BASE_DIR = r"c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word"
TEMPLATE_FOLDER = os.path.join(BASE_DIR, "Mẫu Chuyển nhượng Công ty TNHH 2 TV")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Wizard steps
STEP_COMPANY     = "company"
STEP_DDPL_CU     = "ddpl_cu"
STEP_DDPL_CU_TV  = "ddpl_cu_is_tv"
STEP_TV_CU       = "tv_cu"
STEP_DDPL_MOI    = "ddpl_moi"
STEP_DDPL_MOI_TV = "ddpl_moi_is_tv"
STEP_TV_MOI      = "tv_moi"
STEP_CHUYEN_NHUONG = "chuyen_nhuong"
STEP_CONFIRM     = "confirm"
STEP_DONE        = "done"

PERSON_FIELDS = ["HO_TEN", "NGAY_SINH", "SO_CCCD", "DIA_CHI"]
MEMBER_FIELDS = PERSON_FIELDS + ["VON_GOP", "TY_LE"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def init_wizard(context):
    """Khởi tạo wizard data trong context.user_data."""
    context.user_data['wizard'] = {
        'step': STEP_COMPANY,
        'company': {},
        'ddpl_cu': {},
        'ddpl_cu_is_tv': None,    # True/False
        'ddpl_cu_tv_idx': None,   # index trong tv_cu nếu là TV
        'tv_cu': [],
        'ddpl_moi': {},
        'ddpl_moi_is_tv': None,
        'ddpl_moi_tv_idx': None,
        'tv_moi': [],
        'chuyen_nhuong': [],      # [{ben_a: idx, ben_b: idx, von, ty_le}]
        'waiting_vneid': None,    # "ddpl_cu" / "ddpl_moi" / "tv_cu" / "tv_moi"
    }
    return context.user_data['wizard']


def get_wizard(context):
    """Lấy wizard data, None nếu chưa init."""
    return context.user_data.get('wizard')


def fmt_money(s):
    """Format số tiền: 5000000000 → 5,000,000,000"""
    s = str(s).replace(",", "").replace(".", "").strip()
    if s.isdigit():
        return "{:,}".format(int(s))
    return s


def so_thanh_chu(s):
    """Chuyển số tiền thành chữ tiếng Việt. VD: 5000000000 → Năm tỷ đồng."""
    s = str(s).replace(",", "").replace(".", "").strip()
    if not s.isdigit():
        return s
    n = int(s)
    if n == 0:
        return "Không đồng"

    don_vi = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ"]
    chu_so = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

    def doc_ba_chu_so(n):
        tram = n // 100
        chuc = (n % 100) // 10
        dv = n % 10
        result = ""
        if tram > 0:
            result += chu_so[tram] + " trăm "
            if chuc == 0 and dv > 0:
                result += "lẻ "
        if chuc > 1:
            result += chu_so[chuc] + " mươi "
            if dv == 1:
                result += "mốt "
            elif dv == 5:
                result += "lăm "
            elif dv > 0:
                result += chu_so[dv] + " "
        elif chuc == 1:
            result += "mười "
            if dv == 5:
                result += "lăm "
            elif dv > 0:
                result += chu_so[dv] + " "
        elif tram > 0 and dv > 0:
            result += chu_so[dv] + " "
        elif tram == 0 and dv > 0:
            result += chu_so[dv] + " "
        return result.strip()

    parts = []
    nhom = 0
    while n > 0:
        ba = n % 1000
        if ba > 0:
            text = doc_ba_chu_so(ba)
            if don_vi[nhom]:
                text += " " + don_vi[nhom]
            parts.insert(0, text)
        n //= 1000
        nhom += 1

    result = " ".join(parts) + " đồng"
    return result[0].upper() + result[1:]


def summarize_person(p):
    """Tóm tắt 1 dòng cho 1 người."""
    name = p.get("HO_TEN", "?")
    cccd = p.get("SO_CCCD", "")
    return f"{name} (CCCD: {cccd})" if cccd else name


def summarize_member(m, idx):
    """Tóm tắt 1 TV kèm vốn."""
    name = m.get("HO_TEN", "?")
    von = m.get("VON_GOP", "?")
    ty_le = m.get("TY_LE", "?")
    return f"{idx}. {name} — {ty_le}% ({fmt_money(von)} đ)"


# ── Step Handlers ─────────────────────────────────────────────────────────────

async def handle_wizard_start(update, context):
    """Bắt đầu wizard — hiện bước 1."""
    w = init_wizard(context)
    msg = (
        "📝 <b>CHUYỂN NHƯỢNG TNHH 2TV</b> — Bước 1/7\n\n"
        "🏢 <b>Thông tin công ty</b>\n"
        "Nhập Mã số thuế (10 chữ số):"
    )
    await update.effective_message.reply_text(msg, parse_mode='HTML')


async def handle_wizard_message(update, context):
    """Xử lý message text trong wizard. Return True nếu đã xử lý."""
    w = get_wizard(context)
    if not w:
        return False

    text = update.message.text.strip()
    step = w['step']

    # ── Bước 1: Nhập MST ──
    if step == STEP_COMPANY:
        if 'mst' not in w['company']:
            # Đang chờ MST
            mst = text.replace(" ", "")
            if not (mst.isdigit() and len(mst) == 10):
                await update.message.reply_text("⚠️ MST phải là 10 chữ số. Nhập lại:")
                return True

            w['company']['mst'] = mst
            mst_msg = await update.message.reply_text(f"⏳ Đang tra cứu MST {mst}...")

            # Tra cứu VietQR
            try:
                headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(f"https://api.vietqr.io/v2/business/{mst}", headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("code") == "00":
                            info = data.get("data", {})
                            w['company']['ten'] = info.get("name", "")
                            w['company']['dia_chi'] = info.get("address", "")
                            await mst_msg.edit_text(f"✅ {info.get('name', 'OK')}")
                        else:
                            await mst_msg.edit_text(f"⚠️ Không tìm thấy MST {mst}")
                    else:
                        await mst_msg.edit_text(f"⚠️ Lỗi tra cứu MST")
            except Exception:
                await mst_msg.edit_text(f"⚠️ Không thể tra cứu MST")

            # Hỏi vốn điều lệ
            ten = w['company'].get('ten', '')
            pre = f"🏢 <b>{ten}</b>\n" if ten else ""
            msg = (
                f"{pre}"
                "Nhập vốn điều lệ:\n\n"
                "<pre>VON_DIEU_LE_SO: \n"
                "VON_DIEU_LE_CHU: </pre>"
            )
            await update.message.reply_text(msg, parse_mode='HTML')
            return True

        else:
            # Đang chờ vốn điều lệ
            lines = text.strip().split('\n')
            for line in lines:
                if ':' in line:
                    k, v = line.split(':', 1)
                    k = k.strip().upper().replace(" ", "_")
                    v = v.strip()
                    if 'SO' in k and v:
                        w['company']['von_so'] = v
                    elif 'CHU' in k and v:
                        w['company']['von_chu'] = v

            if not w['company'].get('von_so'):
                await update.message.reply_text("⚠️ Thiếu VON_DIEU_LE_SO. Nhập lại:")
                return True

            # → Sang bước 2: ĐDPL cũ
            w['step'] = STEP_DDPL_CU
            msg = (
                "✅ <b>Bước 1 hoàn tất!</b>\n\n"
                "👤 <b>Bước 2/7 — ĐDPL CŨ</b>\n"
                "📸 Gửi ảnh VNeID hoặc nhập thủ công:\n\n"
                "<pre>HO_TEN: \n"
                "NGAY_SINH: \n"
                "SO_CCCD: \n"
                "DIA_CHI: </pre>"
            )
            w['waiting_vneid'] = 'ddpl_cu'
            await update.message.reply_text(msg, parse_mode='HTML')
            return True

    # ── Bước 2: ĐDPL cũ ──
    if step == STEP_DDPL_CU:
        person = _parse_person(text)
        if not person.get('HO_TEN'):
            await update.message.reply_text("⚠️ Thiếu HO_TEN. Nhập lại:")
            return True
        w['ddpl_cu'] = person
        w['waiting_vneid'] = None

        # Hỏi ĐDPL cũ có phải TV không
        w['step'] = STEP_DDPL_CU_TV
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Có — ĐDPL cũ là thành viên", callback_data="wiz_ddplcu_yes")],
            [InlineKeyboardButton("❌ Không — ĐDPL cũ không phải TV", callback_data="wiz_ddplcu_no")],
        ])
        await update.message.reply_text(
            f"👤 ĐDPL cũ: <b>{person['HO_TEN']}</b>\n\n"
            "❓ ĐDPL cũ có phải là thành viên công ty không?",
            parse_mode='HTML', reply_markup=kb
        )
        return True

    # ── Bước 3: TV cũ ──
    if step == STEP_TV_CU:
        # Case: ĐDPL cũ là TV, đang chờ nhập vốn
        if w.get('_ddpl_cu_pending_von'):
            von_data = _parse_member(text)
            tv = dict(w['ddpl_cu'])
            tv['VON_GOP'] = von_data.get('VON_GOP', '')
            tv['TY_LE'] = von_data.get('TY_LE', '')
            if not tv.get('VON_GOP'):
                await update.message.reply_text("⚠️ Thiếu VON_GOP. Nhập lại:")
                return True
            w['tv_cu'].append(tv)
            w['ddpl_cu_tv_idx'] = len(w['tv_cu']) - 1
            del w['_ddpl_cu_pending_von']
            n = len(w['tv_cu'])
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Thêm TV cũ", callback_data="wiz_add_tvcu")],
                [InlineKeyboardButton("✅ Xong — sang ĐDPL mới", callback_data="wiz_done_tvcu")],
            ])
            await update.message.reply_text(
                f"✅ TV cũ #{n}: <b>{summarize_member(tv, n)}</b>\n\n"
                f"Đã có {n} thành viên cũ. Tiếp tục?",
                parse_mode='HTML', reply_markup=kb
            )
            return True

        # Case: VNeID đã scan cho TV cũ, đang chờ vốn
        if w.get('_pending_tv_cu_vneid'):
            von_data = _parse_member(text)
            tv = dict(w['_pending_tv_cu_vneid'])
            tv['VON_GOP'] = von_data.get('VON_GOP', '')
            tv['TY_LE'] = von_data.get('TY_LE', '')
            if not tv.get('VON_GOP'):
                await update.message.reply_text("⚠️ Thiếu VON_GOP. Nhập lại:")
                return True
            w['tv_cu'].append(tv)
            del w['_pending_tv_cu_vneid']
            n = len(w['tv_cu'])
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Thêm TV cũ", callback_data="wiz_add_tvcu")],
                [InlineKeyboardButton("✅ Xong — sang ĐDPL mới", callback_data="wiz_done_tvcu")],
            ])
            await update.message.reply_text(
                f"✅ TV cũ #{n}: <b>{summarize_member(tv, n)}</b>\n\n"
                f"Đã có {n} thành viên cũ. Tiếp tục?",
                parse_mode='HTML', reply_markup=kb
            )
            return True

        member = _parse_member(text)
        if not member.get('HO_TEN'):
            await update.message.reply_text("⚠️ Thiếu HO_TEN. Nhập lại:")
            return True
        w['tv_cu'].append(member)
        w['waiting_vneid'] = None

        n = len(w['tv_cu'])
        summary = summarize_member(member, n)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Thêm TV cũ", callback_data="wiz_add_tvcu")],
            [InlineKeyboardButton("✅ Xong — sang ĐDPL mới", callback_data="wiz_done_tvcu")],
        ])
        await update.message.reply_text(
            f"✅ TV cũ #{n}: <b>{summary}</b>\n\n"
            f"Đã có {n} thành viên cũ. Tiếp tục?",
            parse_mode='HTML', reply_markup=kb
        )
        return True

    # ── Bước 4: ĐDPL mới ──
    if step == STEP_DDPL_MOI:
        person = _parse_person(text)
        if not person.get('HO_TEN'):
            await update.message.reply_text("⚠️ Thiếu HO_TEN. Nhập lại:")
            return True
        w['ddpl_moi'] = person
        w['waiting_vneid'] = None

        w['step'] = STEP_DDPL_MOI_TV
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Có — ĐDPL mới là thành viên", callback_data="wiz_ddplmoi_yes")],
            [InlineKeyboardButton("❌ Không — ĐDPL mới không phải TV", callback_data="wiz_ddplmoi_no")],
        ])
        await update.message.reply_text(
            f"👤 ĐDPL mới: <b>{person['HO_TEN']}</b>\n\n"
            "❓ ĐDPL mới có phải là thành viên mới không?",
            parse_mode='HTML', reply_markup=kb
        )
        return True

    # ── Bước 5: TV mới ──
    if step == STEP_TV_MOI:
        # Case: ĐDPL mới là TV, đang chờ nhập vốn
        if w.get('_ddpl_moi_pending_von'):
            von_data = _parse_member(text)
            tv = dict(w['ddpl_moi'])
            tv['VON_GOP'] = von_data.get('VON_GOP', '')
            tv['TY_LE'] = von_data.get('TY_LE', '')
            if not tv.get('VON_GOP'):
                await update.message.reply_text("⚠️ Thiếu VON_GOP. Nhập lại:")
                return True
            w['tv_moi'].append(tv)
            w['ddpl_moi_tv_idx'] = len(w['tv_moi']) - 1
            del w['_ddpl_moi_pending_von']
            n = len(w['tv_moi'])
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Thêm TV mới", callback_data="wiz_add_tvmoi")],
                [InlineKeyboardButton("✅ Xong — sang phân bổ CN", callback_data="wiz_done_tvmoi")],
            ])
            await update.message.reply_text(
                f"✅ TV mới #{n}: <b>{summarize_member(tv, n)}</b>\n\n"
                f"Đã có {n} thành viên mới. Tiếp tục?",
                parse_mode='HTML', reply_markup=kb
            )
            return True

        # Case: VNeID đã scan cho TV mới, đang chờ vốn
        if w.get('_pending_tv_moi_vneid'):
            von_data = _parse_member(text)
            tv = dict(w['_pending_tv_moi_vneid'])
            tv['VON_GOP'] = von_data.get('VON_GOP', '')
            tv['TY_LE'] = von_data.get('TY_LE', '')
            if not tv.get('VON_GOP'):
                await update.message.reply_text("⚠️ Thiếu VON_GOP. Nhập lại:")
                return True
            w['tv_moi'].append(tv)
            del w['_pending_tv_moi_vneid']
            n = len(w['tv_moi'])
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Thêm TV mới", callback_data="wiz_add_tvmoi")],
                [InlineKeyboardButton("✅ Xong — sang phân bổ CN", callback_data="wiz_done_tvmoi")],
            ])
            await update.message.reply_text(
                f"✅ TV mới #{n}: <b>{summarize_member(tv, n)}</b>\n\n"
                f"Đã có {n} thành viên mới. Tiếp tục?",
                parse_mode='HTML', reply_markup=kb
            )
            return True

        member = _parse_member(text)
        if not member.get('HO_TEN'):
            await update.message.reply_text("⚠️ Thiếu HO_TEN. Nhập lại:")
            return True
        w['tv_moi'].append(member)
        w['waiting_vneid'] = None

        n = len(w['tv_moi'])
        summary = summarize_member(member, n)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Thêm TV mới", callback_data="wiz_add_tvmoi")],
            [InlineKeyboardButton("✅ Xong — sang phân bổ CN", callback_data="wiz_done_tvmoi")],
        ])
        await update.message.reply_text(
            f"✅ TV mới #{n}: <b>{summary}</b>\n\n"
            f"Đã có {n} thành viên mới. Tiếp tục?",
            parse_mode='HTML', reply_markup=kb
        )
        return True

    # ── Bước 6: Ma trận chuyển nhượng ──
    if step == STEP_CHUYEN_NHUONG:
        cn = _parse_chuyen_nhuong(text)
        if not cn:
            await update.message.reply_text(
                "⚠️ Sai format. Nhập:\n\n"
                "<pre>BEN_A: [số thứ tự TV cũ]\n"
                "BEN_B: [số thứ tự TV mới]\n"
                "VON: [số tiền]\n"
                "TY_LE: [%]</pre>",
                parse_mode='HTML'
            )
            return True

        ben_a_idx = cn['ben_a'] - 1  # convert 1-based → 0-based
        ben_b_idx = cn['ben_b'] - 1

        if ben_a_idx < 0 or ben_a_idx >= len(w['tv_cu']):
            await update.message.reply_text(f"⚠️ TV cũ #{cn['ben_a']} không tồn tại. Nhập lại:")
            return True
        if ben_b_idx < 0 or ben_b_idx >= len(w['tv_moi']):
            await update.message.reply_text(f"⚠️ TV mới #{cn['ben_b']} không tồn tại. Nhập lại:")
            return True

        cn['ben_a'] = ben_a_idx
        cn['ben_b'] = ben_b_idx
        w['chuyen_nhuong'].append(cn)

        n = len(w['chuyen_nhuong'])
        a_name = w['tv_cu'][ben_a_idx]['HO_TEN']
        b_name = w['tv_moi'][ben_b_idx]['HO_TEN']
        summary = f"{a_name} → {b_name}: {cn['ty_le']}% ({fmt_money(cn['von'])} đ)"

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Thêm giao dịch", callback_data="wiz_add_cn")],
            [InlineKeyboardButton("✅ Xong — Xem tổng hợp", callback_data="wiz_done_cn")],
        ])
        await update.message.reply_text(
            f"✅ Giao dịch #{n}: <b>{summary}</b>\n\n"
            f"Đã có {n} giao dịch chuyển nhượng.",
            parse_mode='HTML', reply_markup=kb
        )
        return True

    return False


async def handle_wizard_callback(update, context):
    """Xử lý InlineKeyboard callback trong wizard. Return True nếu đã xử lý."""
    w = get_wizard(context)
    if not w:
        return False

    query = update.callback_query
    data = query.data
    if not data.startswith("wiz_"):
        return False

    await query.answer()

    # ── ĐDPL cũ là TV? ──
    if data == "wiz_ddplcu_yes":
        w['ddpl_cu_is_tv'] = True
        # Tự thêm ĐDPL cũ vào danh sách TV cũ
        tv = dict(w['ddpl_cu'])
        w['step'] = STEP_TV_CU
        msg = (
            "✅ ĐDPL cũ sẽ được tính là thành viên cũ.\n\n"
            f"👤 Nhập thêm thông tin vốn góp cho <b>{tv['HO_TEN']}</b>:\n\n"
            "<pre>VON_GOP: \n"
            "TY_LE: </pre>"
        )
        w['_ddpl_cu_pending_von'] = True
        await query.edit_message_text(msg, parse_mode='HTML')
        return True

    if data == "wiz_ddplcu_no":
        w['ddpl_cu_is_tv'] = False
        w['step'] = STEP_TV_CU
        msg = (
            "👥 <b>Bước 3/7 — THÀNH VIÊN CŨ #1</b>\n"
            "📸 Gửi ảnh VNeID hoặc nhập:\n\n"
            "<pre>HO_TEN: \nNGAY_SINH: \nSO_CCCD: \nDIA_CHI: \n"
            "VON_GOP: \nTY_LE: </pre>"
        )
        w['waiting_vneid'] = 'tv_cu'
        await query.edit_message_text(msg, parse_mode='HTML')
        return True

    # ── Thêm TV cũ ──
    if data == "wiz_add_tvcu":
        n = len(w['tv_cu']) + 1
        msg = (
            f"👥 <b>THÀNH VIÊN CŨ #{n}</b>\n"
            "📸 Gửi ảnh VNeID hoặc nhập:\n\n"
            "<pre>HO_TEN: \nNGAY_SINH: \nSO_CCCD: \nDIA_CHI: \n"
            "VON_GOP: \nTY_LE: </pre>"
        )
        w['waiting_vneid'] = 'tv_cu'
        await query.edit_message_text(msg, parse_mode='HTML')
        return True

    if data == "wiz_done_tvcu":
        if len(w['tv_cu']) < 2:
            await query.answer("⚠️ TNHH 2TV cần ít nhất 2 thành viên cũ!", show_alert=True)
            return True
        w['step'] = STEP_DDPL_MOI
        msg = (
            f"✅ Đã nhập {len(w['tv_cu'])} thành viên cũ.\n\n"
            "👤 <b>Bước 4/7 — ĐDPL MỚI</b>\n"
            "📸 Gửi ảnh VNeID hoặc nhập:\n\n"
            "<pre>HO_TEN: \nNGAY_SINH: \nSO_CCCD: \nDIA_CHI: </pre>"
        )
        w['waiting_vneid'] = 'ddpl_moi'
        await query.edit_message_text(msg, parse_mode='HTML')
        return True

    # ── ĐDPL mới là TV? ──
    if data == "wiz_ddplmoi_yes":
        w['ddpl_moi_is_tv'] = True
        tv = dict(w['ddpl_moi'])
        w['step'] = STEP_TV_MOI
        msg = (
            "✅ ĐDPL mới sẽ được tính là thành viên mới.\n\n"
            f"👤 Nhập thêm thông tin vốn góp cho <b>{tv['HO_TEN']}</b>:\n\n"
            "<pre>VON_GOP: \n"
            "TY_LE: </pre>"
        )
        w['_ddpl_moi_pending_von'] = True
        await query.edit_message_text(msg, parse_mode='HTML')
        return True

    if data == "wiz_ddplmoi_no":
        w['ddpl_moi_is_tv'] = False
        w['step'] = STEP_TV_MOI
        n = len(w['tv_moi']) + 1
        msg = (
            f"👥 <b>Bước 5/7 — THÀNH VIÊN MỚI #{n}</b>\n"
            "📸 Gửi ảnh VNeID hoặc nhập:\n\n"
            "<pre>HO_TEN: \nNGAY_SINH: \nSO_CCCD: \nDIA_CHI: \n"
            "VON_GOP: \nTY_LE: </pre>"
        )
        w['waiting_vneid'] = 'tv_moi'
        await query.edit_message_text(msg, parse_mode='HTML')
        return True

    # ── Thêm TV mới ──
    if data == "wiz_add_tvmoi":
        n = len(w['tv_moi']) + 1
        msg = (
            f"👥 <b>THÀNH VIÊN MỚI #{n}</b>\n"
            "📸 Gửi ảnh VNeID hoặc nhập:\n\n"
            "<pre>HO_TEN: \nNGAY_SINH: \nSO_CCCD: \nDIA_CHI: \n"
            "VON_GOP: \nTY_LE: </pre>"
        )
        w['waiting_vneid'] = 'tv_moi'
        await query.edit_message_text(msg, parse_mode='HTML')
        return True

    if data == "wiz_done_tvmoi":
        if len(w['tv_moi']) < 2:
            await query.answer("⚠️ TNHH 2TV cần ít nhất 2 thành viên mới!", show_alert=True)
            return True
        w['step'] = STEP_CHUYEN_NHUONG
        await _show_cn_prompt(query, w)
        return True

    # ── Thêm giao dịch CN ──
    if data == "wiz_add_cn":
        await _show_cn_prompt(query, w)
        return True

    if data == "wiz_done_cn":
        if len(w['chuyen_nhuong']) < 1:
            await query.answer("⚠️ Cần ít nhất 1 giao dịch chuyển nhượng!", show_alert=True)
            return True
        w['step'] = STEP_CONFIRM
        await _show_summary(query, w)
        return True

    # ── Xác nhận tạo hồ sơ ──
    if data == "wiz_create":
        w['step'] = STEP_DONE
        await query.edit_message_text("⏳ Đang tạo hồ sơ chuyển nhượng, vui lòng đợi...")
        try:
            zip_path, zip_name, file_count = generate_files(w)
            with open(zip_path, 'rb') as f:
                await update.effective_message.reply_document(document=f, filename=zip_name)
            await update.effective_message.reply_text(
                f"✅ Đã tạo <b>{file_count} file</b> trong hồ sơ chuyển nhượng!",
                parse_mode='HTML'
            )
            os.unlink(zip_path)
            # Clear wizard
            context.user_data.pop('wizard', None)
        except Exception as e:
            await update.effective_message.reply_text(f"❌ Lỗi tạo file: {str(e)}")
        return True

    if data == "wiz_cancel":
        context.user_data.pop('wizard', None)
        await query.edit_message_text("❌ Đã hủy wizard. Gõ /start để bắt đầu lại.")
        return True

    return False


async def handle_wizard_vneid(update, context, vneid_info):
    """Xử lý khi nhận ảnh VNeID trong wizard. Return True nếu đã xử lý."""
    w = get_wizard(context)
    if not w or not w.get('waiting_vneid'):
        return False

    target = w['waiting_vneid']
    person = {
        'HO_TEN': vneid_info.get('ho_ten', ''),
        'NGAY_SINH': vneid_info.get('ngay_sinh', ''),
        'SO_CCCD': vneid_info.get('so_cccd', ''),
        'DIA_CHI': vneid_info.get('dia_chi', ''),
    }

    if target == 'ddpl_cu':
        w['ddpl_cu'] = person
        w['waiting_vneid'] = None
        w['step'] = STEP_DDPL_CU_TV
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Có", callback_data="wiz_ddplcu_yes")],
            [InlineKeyboardButton("❌ Không", callback_data="wiz_ddplcu_no")],
        ])
        await update.message.reply_text(
            f"📸 Đã nhận VNeID: <b>{person['HO_TEN']}</b>\n\n"
            "❓ ĐDPL cũ có phải là thành viên công ty không?",
            parse_mode='HTML', reply_markup=kb
        )
        return True

    if target == 'ddpl_moi':
        w['ddpl_moi'] = person
        w['waiting_vneid'] = None
        w['step'] = STEP_DDPL_MOI_TV
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Có", callback_data="wiz_ddplmoi_yes")],
            [InlineKeyboardButton("❌ Không", callback_data="wiz_ddplmoi_no")],
        ])
        await update.message.reply_text(
            f"📸 Đã nhận VNeID: <b>{person['HO_TEN']}</b>\n\n"
            "❓ ĐDPL mới có phải là thành viên mới không?",
            parse_mode='HTML', reply_markup=kb
        )
        return True

    if target in ('tv_cu', 'tv_moi'):
        # VNeID chỉ có info cá nhân, cần hỏi thêm vốn
        w[f'_pending_{target}_vneid'] = person
        w['waiting_vneid'] = None
        await update.message.reply_text(
            f"📸 Đã nhận VNeID: <b>{person['HO_TEN']}</b>\n\n"
            "Nhập thêm thông tin vốn góp:\n\n"
            "<pre>VON_GOP: \nTY_LE: </pre>",
            parse_mode='HTML'
        )
        return True

    return False


# ── Parsing helpers ───────────────────────────────────────────────────────────

def _parse_person(text):
    """Parse text input thành dict person."""
    result = {}
    for line in text.strip().split('\n'):
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        k = k.strip().upper().replace(" ", "_")
        v = v.strip()
        if not v:
            continue
        if 'HO_TEN' in k or 'HOTEN' in k or k == 'TEN':
            result['HO_TEN'] = v
        elif 'NGAY' in k or 'SINH' in k:
            result['NGAY_SINH'] = v
        elif 'CCCD' in k or 'CMND' in k:
            result['SO_CCCD'] = v
        elif 'DIA_CHI' in k or 'DIACHI' in k:
            result['DIA_CHI'] = v
    return result


def _parse_member(text):
    """Parse text input thành dict member (person + vốn)."""
    result = _parse_person(text)
    for line in text.strip().split('\n'):
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        k = k.strip().upper().replace(" ", "_")
        v = v.strip()
        if not v:
            continue
        if 'VON' in k or 'GOP' in k:
            result['VON_GOP'] = v
        elif 'TY_LE' in k or 'TYLE' in k or k == '%':
            result['TY_LE'] = v.replace('%', '').strip()
    return result


def _parse_chuyen_nhuong(text):
    """Parse giao dịch chuyển nhượng."""
    result = {}
    for line in text.strip().split('\n'):
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        k = k.strip().upper().replace(" ", "_")
        v = v.strip()
        if 'BEN_A' in k or 'BENA' in k:
            try: result['ben_a'] = int(v)
            except: pass
        elif 'BEN_B' in k or 'BENB' in k:
            try: result['ben_b'] = int(v)
            except: pass
        elif 'VON' in k:
            result['von'] = v
        elif 'TY_LE' in k or 'TYLE' in k:
            result['ty_le'] = v.replace('%', '').strip()

    if all(k in result for k in ['ben_a', 'ben_b', 'von', 'ty_le']):
        return result
    return None


def parse_address(addr):
    """Tách địa chỉ thành 3 phần: Số nhà, Xã/Phường/Quận/Huyện, Tỉnh/Thành"""
    if not addr:
        return "", "", ""
    parts = [p.strip() for p in addr.split(',')]
    if len(parts) >= 3:
        tinh = parts[-1]
        xa_huyen = ", ".join(parts[1:-1])
        so_nha = parts[0]
        return so_nha, xa_huyen, tinh
    elif len(parts) == 2:
        return parts[0], parts[1], ""
    else:
        return addr, "", ""

async def _show_cn_prompt(query, w):
    """Hiện prompt nhập giao dịch chuyển nhượng."""
    tv_cu_list = "\n".join([f"  {i+1}. {m['HO_TEN']} — {m.get('TY_LE','')}% ({fmt_money(m.get('VON_GOP',''))} đ)"
                           for i, m in enumerate(w['tv_cu'])])
    tv_moi_list = "\n".join([f"  {i+1}. {m['HO_TEN']} — {m.get('TY_LE','')}% ({fmt_money(m.get('VON_GOP',''))} đ)"
                            for i, m in enumerate(w['tv_moi'])])

    existing = ""
    if w['chuyen_nhuong']:
        lines = []
        for i, cn in enumerate(w['chuyen_nhuong'], 1):
            a = w['tv_cu'][cn['ben_a']]['HO_TEN']
            b = w['tv_moi'][cn['ben_b']]['HO_TEN']
            lines.append(f"  {i}. {a} → {b}: {cn['ty_le']}% ({fmt_money(cn['von'])} đ)")
        existing = "\n📋 Đã nhập:\n" + "\n".join(lines) + "\n"

    msg = (
        f"🔄 <b>Bước 6/7 — PHÂN BỔ CHUYỂN NHƯỢNG</b>\n\n"
        f"TV cũ:\n{tv_cu_list}\n\n"
        f"TV mới:\n{tv_moi_list}\n"
        f"{existing}\n"
        "Nhập giao dịch (số thứ tự TV):\n\n"
        "<pre>BEN_A: \nBEN_B: \nVON: \nTY_LE: </pre>"
    )
    await query.edit_message_text(msg, parse_mode='HTML')


async def _show_summary(query, w):
    """Hiện tóm tắt toàn bộ trước khi tạo file."""
    company = w['company']
    ddpl_cu = w['ddpl_cu']
    ddpl_moi = w['ddpl_moi']
    tv_cu = w['tv_cu']
    tv_moi = w['tv_moi']
    cn_list = w['chuyen_nhuong']

    # Đếm file sẽ tạo
    n_hd = len(cn_list)
    n_bb = n_hd
    n_xnv = len(tv_moi)
    # CSHHL: chỉ TV mới >= 25%
    n_cshhl = sum(1 for m in tv_moi if float(m.get('TY_LE', '0').replace(',','.')) >= 25)
    ddpl_changed = ddpl_cu.get('SO_CCCD') != ddpl_moi.get('SO_CCCD')
    n_static = 3 if ddpl_changed else 2  # Thông báo BS + QĐ + (Thông báo ĐDPL nếu thay đổi)
    n_static += 1  # Giấy ủy quyền
    n_static += 1  # DS thành viên
    n_static += 1  # DS CSHHL
    total_files = n_static + n_hd + n_bb + n_xnv

    cn_lines = []
    for i, cn in enumerate(cn_list, 1):
        a = tv_cu[cn['ben_a']]['HO_TEN']
        b = tv_moi[cn['ben_b']]['HO_TEN']
        cn_lines.append(f"  {i}. {a} → {b}: {cn['ty_le']}% ({fmt_money(cn['von'])} đ)")

    tv_moi_lines = []
    for i, m in enumerate(tv_moi, 1):
        cshhl = " ⭐" if float(m.get('TY_LE', '0').replace(',','.')) >= 25 else ""
        tv_moi_lines.append(f"  {i}. {m['HO_TEN']} — {m.get('TY_LE','')}%{cshhl}")

    msg = (
        f"📋 <b>TÓM TẮT HỒ SƠ CHUYỂN NHƯỢNG</b>\n\n"
        f"🏢 <b>{company.get('ten', '')}</b>\n"
        f"MST: <code>{company.get('mst', '')}</code>\n"
        f"💰 Vốn ĐL: {fmt_money(company.get('von_so', ''))}\n\n"
        f"👤 ĐDPL cũ: {ddpl_cu.get('HO_TEN', '')}\n"
        f"👤 ĐDPL mới: {ddpl_moi.get('HO_TEN', '')}"
    )
    if ddpl_changed:
        msg += " 🔄"
    msg += f"\n\n🔄 <b>{n_hd} giao dịch chuyển nhượng:</b>\n"
    msg += "\n".join(cn_lines)
    msg += f"\n\n👥 <b>TV mới (⭐=CSHHL ≥25%):</b>\n"
    msg += "\n".join(tv_moi_lines)
    msg += f"\n\n📂 Sẽ tạo <b>{total_files} file</b>"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Tạo hồ sơ", callback_data="wiz_create")],
        [InlineKeyboardButton("❌ Hủy", callback_data="wiz_cancel")],
    ])
    await query.edit_message_text(msg, parse_mode='HTML', reply_markup=kb)


# ── File Generator ────────────────────────────────────────────────────────────

def generate_files(w):
    """Tạo toàn bộ file hồ sơ chuyển nhượng, trả về (zip_path, zip_name, file_count)."""
    pythoncom.CoInitialize()
    temp_dir = tempfile.mkdtemp()
    work_dir = os.path.join(temp_dir, "HoSo_ChuyenNhuong")
    os.makedirs(work_dir)

    company = w['company']
    ddpl_cu = w['ddpl_cu']
    ddpl_moi = w['ddpl_moi']
    tv_cu = w['tv_cu']
    tv_moi = w['tv_moi']
    cn_list = w['chuyen_nhuong']
    ddpl_changed = ddpl_cu.get('SO_CCCD') != ddpl_moi.get('SO_CCCD')

    file_count = 0

    # Copy static files
    static_files = [
        "01. Thông báo bổ sung cập nhật.docx",
        "03. Danh sách thành viên.docx",
        "04. Danh sách chủ sở hữu hưởng lợi.docx",
        "05. Giấy ủy quyền.doc",
        "08. Quyết định.doc",
    ]
    if ddpl_changed:
        static_files.append("02. Thông báo thay đổi người đại diện theo pháp luật.docx")

    for fname in static_files:
        src = os.path.join(TEMPLATE_FOLDER, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(work_dir, fname))
            file_count += 1

    # Nhân bản HĐ chuyển nhượng
    hd_template = os.path.join(TEMPLATE_FOLDER, "06. Hợp đồng chuyển nhượng.docx")
    for i, cn in enumerate(cn_list):
        suffix = chr(ord('a') + i)
        fname = f"06{suffix}. Hợp đồng chuyển nhượng ({tv_cu[cn['ben_a']]['HO_TEN']} → {tv_moi[cn['ben_b']]['HO_TEN']}).docx"
        # Sanitize filename
        fname = re.sub(r'[<>:"/\\|?*]', '_', fname)
        shutil.copy2(hd_template, os.path.join(work_dir, fname))
        file_count += 1

    # Nhân bản Biên bản thanh lý
    bb_template = os.path.join(TEMPLATE_FOLDER, "07. Biên bản thanh lý.doc")
    for i, cn in enumerate(cn_list):
        suffix = chr(ord('a') + i)
        fname = f"07{suffix}. Biên bản thanh lý ({tv_cu[cn['ben_a']]['HO_TEN']} → {tv_moi[cn['ben_b']]['HO_TEN']}).doc"
        fname = re.sub(r'[<>:"/\\|?*]', '_', fname)
        shutil.copy2(bb_template, os.path.join(work_dir, fname))
        file_count += 1

    # Nhân bản Xác nhận góp vốn cho mỗi TV mới
    xnv_template = os.path.join(TEMPLATE_FOLDER, "09. Xác nhận góp vốn 1.docx")
    for i, tv in enumerate(tv_moi):
        fname = f"09_{i+1}. Xác nhận góp vốn — {tv['HO_TEN']}.docx"
        fname = re.sub(r'[<>:"/\\|?*]', '_', fname)
        shutil.copy2(xnv_template, os.path.join(work_dir, fname))
        file_count += 1

    # Xóa file mẫu gốc 09/10 nếu đã copy
    for f in ["09. Xác nhận góp vốn 1.docx", "10. Xác nhận góp vốn 2.docx"]:
        p = os.path.join(work_dir, f)
        if os.path.exists(p):
            os.remove(p)

    # ── Mở Word và thay thế ──
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    wdYellow = 7

    try:
        # Build replacement map cho từng file
        # Common replacements
        common = {
            "[TEN_CONG_TY_VN]": company.get('ten', ''),
            "[MA_SO_THUE]": company.get('mst', ''),
            "[VON_DIEU_LE_SO]": fmt_money(company.get('von_so', '')),
            "[VON_DIEU_LE_CHU]": company.get('von_chu', ''),
            # ĐDPL cũ
            "[DDPL_CU_HO_TEN]": ddpl_cu.get('HO_TEN', ''),
            "[DDPL_CU_NGAY_SINH]": ddpl_cu.get('NGAY_SINH', ''),
            "[DDPL_CU_SO_CCCD]": ddpl_cu.get('SO_CCCD', ''),
            "[DDPL_CU_DIA_CHI_DAY_DU]": ddpl_cu.get('DIA_CHI', ''),
            "[DDPL_CU_DIA_CHI_SO_NHA]": parse_address(ddpl_cu.get('DIA_CHI', ''))[0],
            "[DDPL_CU_DIA_CHI_XA_PHUONG]": parse_address(ddpl_cu.get('DIA_CHI', ''))[1],
            "[DDPL_CU_DIA_CHI_TINH_THANH]": parse_address(ddpl_cu.get('DIA_CHI', ''))[2],
            # ĐDPL mới
            "[DDPL_MOI_HO_TEN]": ddpl_moi.get('HO_TEN', ''),
            "[DDPL_MOI_NGAY_SINH]": ddpl_moi.get('NGAY_SINH', ''),
            "[DDPL_MOI_SO_CCCD]": ddpl_moi.get('SO_CCCD', ''),
            "[DDPL_MOI_DIA_CHI_DAY_DU]": ddpl_moi.get('DIA_CHI', ''),
            "[DDPL_MOI_DIA_CHI_SO_NHA]": parse_address(ddpl_moi.get('DIA_CHI', ''))[0],
            "[DDPL_MOI_DIA_CHI_XA_PHUONG]": parse_address(ddpl_moi.get('DIA_CHI', ''))[1],
            "[DDPL_MOI_DIA_CHI_TINH_THANH]": parse_address(ddpl_moi.get('DIA_CHI', ''))[2],
        }

        # Process static files
        for fname in os.listdir(work_dir):
            if fname.startswith("~$"):
                continue
            fpath = os.path.join(work_dir, fname)
            if not os.path.isfile(fpath):
                continue
            if not (fname.endswith('.doc') or fname.endswith('.docx')):
                continue

            doc = None
            for _ in range(3):
                try:
                    doc = word.Documents.Open(fpath, ReadOnly=False, ConfirmConversions=False)
                    break
                except:
                    time.sleep(1)
            if not doc:
                continue

            # Determine replacements based on file type
            replacements = dict(common)

            # HĐ chuyển nhượng — replace BÊN A/B with specific TV
            if fname.startswith("06") and "Hợp đồng" in fname:
                # Find which CN this is
                cn_idx = ord(fname[2]) - ord('a') if len(fname) > 2 and fname[2].isalpha() else 0
                if cn_idx < len(cn_list):
                    cn = cn_list[cn_idx]
                    ben_a = tv_cu[cn['ben_a']]
                    ben_b = tv_moi[cn['ben_b']]
                    replacements["[BEN_A_HO_TEN]"] = ben_a.get('HO_TEN', '')
                    replacements["[BEN_A_NGAY_SINH]"] = ben_a.get('NGAY_SINH', '')
                    replacements["[BEN_A_SO_CCCD]"] = ben_a.get('SO_CCCD', '')
                    replacements["[BEN_A_DIA_CHI_DAY_DU]"] = ben_a.get('DIA_CHI', '')
                    replacements["[BEN_A_DIA_CHI_SO_NHA]"] = parse_address(ben_a.get('DIA_CHI', ''))[0]
                    replacements["[BEN_A_DIA_CHI_XA_PHUONG]"] = parse_address(ben_a.get('DIA_CHI', ''))[1]
                    replacements["[BEN_A_DIA_CHI_TINH_THANH]"] = parse_address(ben_a.get('DIA_CHI', ''))[2]
                    
                    replacements["[BEN_B_HO_TEN]"] = ben_b.get('HO_TEN', '')
                    replacements["[BEN_B_NGAY_SINH]"] = ben_b.get('NGAY_SINH', '')
                    replacements["[BEN_B_SO_CCCD]"] = ben_b.get('SO_CCCD', '')
                    replacements["[BEN_B_DIA_CHI_DAY_DU]"] = ben_b.get('DIA_CHI', '')
                    replacements["[BEN_B_DIA_CHI_SO_NHA]"] = parse_address(ben_b.get('DIA_CHI', ''))[0]
                    replacements["[BEN_B_DIA_CHI_XA_PHUONG]"] = parse_address(ben_b.get('DIA_CHI', ''))[1]
                    replacements["[BEN_B_DIA_CHI_TINH_THANH]"] = parse_address(ben_b.get('DIA_CHI', ''))[2]
                    replacements["[GIA_TRI_CN_TY_LE]"] = cn.get('ty_le', '')
                    
                    cn_von = cn.get('von', '').replace(',', '').replace('.', '').strip()
                    replacements["[GIA_TRI_CN_SO]"] = fmt_money(cn.get('von', ''))
                    replacements["[GIA_TRI_CN_CHU]"] = so_thanh_chu(cn_von)
                    replacements["[GIA_TRI_CN_TY_LE]"] = cn.get('ty_le', '')

            # Biên bản thanh lý
            if fname.startswith("07") and "Biên bản" in fname:
                cn_idx = ord(fname[2]) - ord('a') if len(fname) > 2 and fname[2].isalpha() else 0
                if cn_idx < len(cn_list):
                    cn = cn_list[cn_idx]
                    ben_a = tv_cu[cn['ben_a']]
                    ben_b = tv_moi[cn['ben_b']]
                    replacements["[BEN_A_HO_TEN]"] = ben_a.get('HO_TEN', '')
                    replacements["[BEN_A_NGAY_SINH]"] = ben_a.get('NGAY_SINH', '')
                    replacements["[BEN_A_SO_CCCD]"] = ben_a.get('SO_CCCD', '')
                    replacements["[BEN_A_DIA_CHI_DAY_DU]"] = ben_a.get('DIA_CHI', '')
                    replacements["[BEN_A_DIA_CHI_SO_NHA]"] = parse_address(ben_a.get('DIA_CHI', ''))[0]
                    replacements["[BEN_A_DIA_CHI_XA_PHUONG]"] = parse_address(ben_a.get('DIA_CHI', ''))[1]
                    replacements["[BEN_A_DIA_CHI_TINH_THANH]"] = parse_address(ben_a.get('DIA_CHI', ''))[2]
                    
                    replacements["[BEN_B_HO_TEN]"] = ben_b.get('HO_TEN', '')
                    replacements["[BEN_B_NGAY_SINH]"] = ben_b.get('NGAY_SINH', '')
                    replacements["[BEN_B_SO_CCCD]"] = ben_b.get('SO_CCCD', '')
                    replacements["[BEN_B_DIA_CHI_DAY_DU]"] = ben_b.get('DIA_CHI', '')
                    replacements["[BEN_B_DIA_CHI_SO_NHA]"] = parse_address(ben_b.get('DIA_CHI', ''))[0]
                    replacements["[BEN_B_DIA_CHI_XA_PHUONG]"] = parse_address(ben_b.get('DIA_CHI', ''))[1]
                    replacements["[BEN_B_DIA_CHI_TINH_THANH]"] = parse_address(ben_b.get('DIA_CHI', ''))[2]
                    replacements["[GIA_TRI_CN_TY_LE]"] = cn.get('ty_le', '')

            # Xác nhận góp vốn
            if fname.startswith("09_") and "Xác nhận" in fname:
                # Extract TV index
                match = re.match(r'09_(\d+)', fname)
                if match:
                    tv_idx = int(match.group(1)) - 1
                    if tv_idx < len(tv_moi):
                        tv = tv_moi[tv_idx]
                        replacements["[TV_MOI_1_HO_TEN]"] = tv.get('HO_TEN', '')
                        replacements["[TV_MOI_1_NGAY_SINH]"] = tv.get('NGAY_SINH', '')
                        replacements["[TV_MOI_1_SO_CCCD]"] = tv.get('SO_CCCD', '')
                        replacements["[TV_MOI_1_DIA_CHI_DAY_DU]"] = tv.get('DIA_CHI', '')
                        replacements["[TV_MOI_1_VON_SO]"] = fmt_money(tv.get('VON_GOP', ''))
                        replacements["[TV_MOI_1_TY_LE]"] = tv.get('TY_LE', '')

            # Apply replacements
            for old_text, new_text in replacements.items():
                if new_text is None or new_text == '':
                    continue
                _find_replace_all(doc, old_text, new_text, wdYellow)

            # Handle dynamic tables
            if fname == "03. Danh sách thành viên.docx":
                _fill_member_table(doc, tv_moi, ddpl_moi)

            if fname == "04. Danh sách chủ sở hữu hưởng lợi.docx":
                # Chỉ TV mới >= 25%
                cshhl = [m for m in tv_moi if float(m.get('TY_LE', '0').replace(',', '.')) >= 25]
                _fill_cshhl_table(doc, cshhl)

            doc.Save()
            doc.Close(False)

    finally:
        word.Quit()

    # Zip
    mst = company.get('mst', 'NoMST')
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    zip_name = f"{mst}_ChuyenNhuong2TV_{date_str}.zip"
    zip_path = os.path.join(temp_dir, zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(work_dir):
            for f in files:
                if not f.startswith("~$"):
                    fp = os.path.join(root, f)
                    zf.write(fp, os.path.relpath(fp, work_dir))

    shutil.rmtree(work_dir)
    return zip_path, zip_name, file_count


def _find_replace_all(doc, old_text, new_text, highlight_color=None):
    """Find & replace trong toàn bộ doc (kể cả header/footer)."""
    wdFindStop = 0
    for story in doc.StoryRanges:
        while story:
            rng = story.Duplicate
            while True:
                rng.Find.ClearFormatting()
                rng.Find.Text = old_text
                rng.Find.Forward = True
                rng.Find.Wrap = wdFindStop
                rng.Find.MatchCase = True
                if not rng.Find.Execute():
                    break
                rng.Text = new_text
                if highlight_color:
                    rng.HighlightColorIndex = highlight_color
                rng.Collapse(0)
            story = story.NextStoryRange


def _fill_member_table(doc, tv_moi, ddpl_moi):
    """Điền bảng Danh sách thành viên (file 03) — fill TV mới vào bảng."""
    if doc.Tables.Count < 1:
        return
    tbl = doc.Tables(1)
    n_rows = tbl.Rows.Count
    # Bảng gồm: Row 1 = header, Row 2-3 = TV template (TV1, TV2), Row 4-5 = footer
    # Chiến lược: dùng find/replace trực tiếp trên toàn bộ doc
    # TV đầu tiên → [TV1_*], TV thứ 2 → dùng [DDPL_*] (vì template gốc dùng DDPL cho TV2)
    # Đã được xử lý ở common replacements cho DDPL

    # Fill TV1 (TV mới đầu tiên)
    if len(tv_moi) >= 1:
        tv = tv_moi[0]
        wdYellow = 7
        _find_replace_all(doc, "[TV_MOI_1_HO_TEN]", tv.get("HO_TEN", ""), wdYellow)
        _find_replace_all(doc, "[TV_MOI_1_NGAY_SINH]", tv.get("NGAY_SINH", ""), wdYellow)
        _find_replace_all(doc, "[TV_MOI_1_SO_CCCD]", tv.get("SO_CCCD", ""), wdYellow)
        _find_replace_all(doc, "[TV_MOI_1_DIA_CHI_DAY_DU]", tv.get("DIA_CHI", ""), wdYellow)
        _find_replace_all(doc, "[TV_MOI_1_VON_SO]", fmt_money(tv.get("VON_GOP", "")), wdYellow)
        _find_replace_all(doc, "[TV_MOI_1_TY_LE]", tv.get("TY_LE", ""), wdYellow)

    # Fill TV2 vốn
    if len(tv_moi) >= 2:
        tv = tv_moi[1]
        wdYellow = 7
        _find_replace_all(doc, "[TV_MOI_2_HO_TEN]", tv.get("HO_TEN", ""), wdYellow)
        _find_replace_all(doc, "[TV_MOI_2_NGAY_SINH]", tv.get("NGAY_SINH", ""), wdYellow)
        _find_replace_all(doc, "[TV_MOI_2_SO_CCCD]", tv.get("SO_CCCD", ""), wdYellow)
        _find_replace_all(doc, "[TV_MOI_2_DIA_CHI_DAY_DU]", tv.get("DIA_CHI", ""), wdYellow)
        _find_replace_all(doc, "[TV_MOI_2_VON_SO]", fmt_money(tv.get("VON_GOP", "")), wdYellow)
        _find_replace_all(doc, "[TV_MOI_2_TY_LE]", tv.get("TY_LE", ""), wdYellow)


def _fill_cshhl_table(doc, cshhl_members):
    """Điền bảng CSHHL (file 04) — chỉ TV >= 25%."""
    wdYellow = 7
    if len(cshhl_members) >= 1:
        tv = cshhl_members[0]
        _find_replace_all(doc, "[CSHHL_1_HO_TEN]", tv.get("HO_TEN", ""), wdYellow)
        _find_replace_all(doc, "[CSHHL_1_NGAY_SINH]", tv.get("NGAY_SINH", ""), wdYellow)
        _find_replace_all(doc, "[CSHHL_1_SO_CCCD]", tv.get("SO_CCCD", ""), wdYellow)
        _find_replace_all(doc, "[CSHHL_1_DIA_CHI_DAY_DU]", tv.get("DIA_CHI", ""), wdYellow)
        _find_replace_all(doc, "[CSHHL_1_TY_LE]", tv.get("TY_LE", ""), wdYellow)
    else:
        _find_replace_all(doc, "[CSHHL_1_HO_TEN]", " ", wdYellow)
        _find_replace_all(doc, "[CSHHL_1_NGAY_SINH]", " ", wdYellow)
        _find_replace_all(doc, "[CSHHL_1_SO_CCCD]", " ", wdYellow)
        _find_replace_all(doc, "[CSHHL_1_DIA_CHI_DAY_DU]", " ", wdYellow)
        _find_replace_all(doc, "[CSHHL_1_TY_LE]", " ", wdYellow)
