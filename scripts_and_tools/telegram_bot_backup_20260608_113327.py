import os
import shutil
import zipfile
import tempfile
import json
import asyncio
import httpx
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import win32com.client

TOKEN = "8108649762:AAHZd6ai0KEVQfK4qOp_nKScMJGFpWm0dKQ"
BASE_DIR = r"c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word"

def get_templates():
    templates = []
    if os.path.exists(BASE_DIR):
        for f in os.listdir(BASE_DIR):
            if os.path.isdir(os.path.join(BASE_DIR, f)) and f.startswith("Mẫu "):
                templates.append(f.replace("Mẫu ", ""))
    return templates

def get_template_keys(template_name):
    json_path = os.path.join(BASE_DIR, "folder_keys.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(template_name, [])
    return []

def process_word_files(folder_path, replacements):
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    wdYellow = 7
    wdFindStop = 0

    try:
        files = [f for f in os.listdir(folder_path) if f.endswith(".doc") or f.endswith(".docx")]
        for file in files:
            if file.startswith("~$"): continue
            path = os.path.join(folder_path, file)
            doc = word.Documents.Open(path, ReadOnly=False, Format=0)
            
            # Ensure all known placeholders are processed to prevent leaking literal tags
            possible_keys = [
                "TEN_CONG_TY_VN", "TEN_CONG_TY_EN", "TEN_CONG_TY_VIET_TAT", "MA_SO_THUE", 
                "DIA_CHI_SO_NHA", "DIA_CHI_XA_PHUONG", "DIA_CHI_QUAN_HUYEN", "DIA_CHI_TINH_THANH",
                "DDPL_HO_TEN", "DDPL_SO_CCCD", "DDPL_NGAY_SINH", "DDPL_GIOI_TINH",
                "DDPL_DIA_CHI_SO_NHA", "DDPL_DIA_CHI_XA_PHUONG", "DDPL_DIA_CHI_TINH_THANH",
                "VON_DIEU_LE_SO", "VON_DIEU_LE_CHU", "SDT_CONG_TY", "EMAIL_CONG_TY",
                "DDPL_CU_HO_TEN", "DDPL_CU_NGAY_SINH", "DDPL_CU_SO_CCCD", "DDPL_CU_DIA_CHI_DAY_DU",
                "NGUOI_DUOC_UY_QUYEN_HO_TEN", "NGUOI_DUOC_UY_QUYEN_CCCD", "NGUOI_DUOC_UY_QUYEN_NGAY_SINH",
                "NGUOI_DUOC_UY_QUYEN_DIA_CHI", "NGUOI_DUOC_UY_QUYEN_SDT", "NGUOI_DUOC_UY_QUYEN_EMAIL",
                "VON_CU_SO", "VON_CU_CHU", "VON_MOI_SO", "VON_MOI_CHU",
                "DDPL_DIA_CHI_DAY_DU", "DDPL_VON_CU_SO", "DDPL_VON_CU_CHU", "DDPL_VON_MOI_SO", "DDPL_TY_LE",
                "TV2_HO_TEN", "TV2_NGAY_SINH", "TV2_SO_CCCD", "TV2_DIA_CHI_DAY_DU", "TV2_VON_CU_SO", 
                "TV2_VON_CU_CHU", "TV2_VON_MOI_SO", "TV2_VON_MOI_CHU", "TV2_TY_LE"
            ]
            for pk in possible_keys:
                if pk not in replacements:
                    replacements[pk] = ""
                    
            for key, val in replacements.items():
                placeholder = f"[{key}]"
                for story in doc.StoryRanges:
                    while story:
                        rng = story.Duplicate
                        while True:
                            rng.Find.ClearFormatting()
                            rng.Find.Text = placeholder
                            rng.Find.Forward = True
                            rng.Find.Wrap = wdFindStop
                            rng.Find.Format = False
                            rng.Find.MatchCase = False
                            rng.Find.MatchWholeWord = False
                            rng.Find.MatchWildcards = False
                            rng.Find.MatchSoundsLike = False
                            rng.Find.MatchAllWordForms = False
                            
                            found = rng.Find.Execute()
                            if not found:
                                break
                            
                            rng.Text = val
                            rng.HighlightColorIndex = wdYellow
                            rng.Collapse(0)
                        
                        story = story.NextStoryRange
            
            # Clean up redundant commas left by empty variables
            for story in doc.StoryRanges:
                while story:
                    for old, new in [(" ,", ","), (", ,", ","), (": ,", ": "), (":,", ": ")]:
                        rng = story.Duplicate
                        rng.Find.Execute(old, False, False, False, False, False, True, 1, False, new, 2)
                    story = story.NextStoryRange
                    
            doc.Save()
            doc.Close(False)
    finally:
        word.Quit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    templates = get_templates()
    
    keyboard = []
    row = []
    for t in templates:
        row.append(KeyboardButton(t))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    welcome = (
        "Xin chào! Tôi là Trợ Lý Hồ Sơ Tự Động. 🤖\n\n"
        "👇 Vui lòng chạm vào Menu bàn phím bên dưới để chọn loại mẫu hồ sơ bạn muốn tạo:"
    )
    await update.message.reply_text(welcome, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    templates = get_templates()
    
    if text in templates:
        context.user_data['selected_template'] = text
        
        # Get specific keys for this template
        keys = get_template_keys(text)
        if keys:
            key_text = "\n".join([f"{k}: " for k in keys])
        else:
            key_text = "TEN_CONG_TY_VN: \nMA_SO_THUE: \nDDPL_HO_TEN: \nDIA_CHI_TINH_THANH: "
            
        msg = (
            f"✅ Bạn đã chọn: <b>Mẫu {text}</b>\n\n"
            "Vui lòng CHẠM VÀO ĐOẠN CODE BÊN DƯỚI để copy (sao chép), sau đó dán ra điền thông tin và gửi lại cho tôi:\n\n"
            f"<pre>Mẫu: {text}\n{key_text}</pre>"
        )
        await update.message.reply_text(msg, parse_mode='HTML')
        return

    if ":" in text:
        selected_template = context.user_data.get('selected_template')
        
        lines = text.strip().split('\n')
        replacements = {}
        for line in lines:
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if key.lower() == "mẫu":
                selected_template = val
            elif val:
                replacements[key] = val
                
        if "MA_SO_THUE" in replacements and replacements["MA_SO_THUE"]:
            mst = replacements["MA_SO_THUE"].strip()
            for attempt in range(3):
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(f"https://api.vietqr.io/v2/business/{mst}")
                        if response.status_code == 200:
                            res_data = response.json()
                            if res_data.get("code") == "00":
                                company_info = res_data.get("data", {})
                                c_name = company_info.get("name")
                                c_address = company_info.get("address")
                                
                                if c_name and not replacements.get("TEN_CONG_TY_VN"):
                                    replacements["TEN_CONG_TY_VN"] = c_name
                                if c_address:
                                    parts = [p.strip() for p in c_address.split(",")]
                                    if not replacements.get("DIA_CHI_TINH_THANH"):
                                        replacements["DIA_CHI_TINH_THANH"] = parts[-1] if len(parts) >= 1 else ""
                                    if not replacements.get("DIA_CHI_QUAN_HUYEN"):
                                        replacements["DIA_CHI_QUAN_HUYEN"] = parts[-2] if len(parts) >= 2 else ""
                                    if not replacements.get("DIA_CHI_XA_PHUONG"):
                                        replacements["DIA_CHI_XA_PHUONG"] = parts[-3] if len(parts) >= 3 else ""
                                    if not replacements.get("DIA_CHI_SO_NHA"):
                                        replacements["DIA_CHI_SO_NHA"] = ", ".join(parts[:-3]) if len(parts) >= 4 else ""
                            break
                        elif response.status_code == 429:
                            await asyncio.sleep(2)
                        else:
                            break
                except Exception as e:
                    print(f"MST lookup error attempt {attempt}: {e}", flush=True)
                    await asyncio.sleep(2)
                
        if not selected_template:
            await update.message.reply_text("❌ Lỗi: Bạn chưa chọn loại mẫu nào. Vui lòng gõ /start để chọn lại.")
            return
            
        template_dir = os.path.join(BASE_DIR, f"Mẫu {selected_template}")
        if not os.path.exists(template_dir):
            if selected_template.startswith("Mẫu "):
                template_dir = os.path.join(BASE_DIR, selected_template)
            if not os.path.exists(template_dir):
                await update.message.reply_text(f"❌ Lỗi: Không tìm thấy thư mục mẫu '{selected_template}' trong máy tính của bạn.")
                return

        await update.message.reply_text("⏳ Đang tiến hành tạo hồ sơ trên máy tính của bạn, vui lòng đợi trong giây lát...")
        
        try:
            temp_dir = tempfile.mkdtemp()
            work_dir = os.path.join(temp_dir, "HoSo")
            shutil.copytree(template_dir, work_dir)
            
            company_name = replacements.get("TEN_CONG_TY_VN", "Ho_So_Moi")
            if not company_name:
                company_name = "Ho_So_Moi"
            company_name = company_name.replace("/", "-").replace(" ", "_")
            
            process_word_files(work_dir, replacements)
            
            safe_template = selected_template.replace(" ", "_").replace("Mẫu_", "")
            zip_filename = f"{company_name}_{safe_template}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(work_dir):
                    for file in files:
                        if not file.startswith("~$"):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, work_dir)
                            zipf.write(file_path, arcname)
                            
            with open(zip_path, 'rb') as f:
                await update.message.reply_document(document=f, filename=zip_filename)
                
            shutil.rmtree(temp_dir)
            
            context.user_data['selected_template'] = None
            
        except Exception as e:
            await update.message.reply_text(f"❌ Đã có lỗi xảy ra khi xử lý file: {str(e)}")
        return
        
    await update.message.reply_text("❓ Tôi không hiểu cú pháp này. Vui lòng bấm /start để mở Menu chọn mẫu lại.")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
