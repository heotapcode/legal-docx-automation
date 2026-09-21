import os
import shutil
import zipfile
import tempfile
import json
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
            
            process_word_files(work_dir, replacements)
            
            company_name = replacements.get("TEN_CONG_TY_VN", "Ho_So_Moi").replace("/", "-").replace(" ", "_")
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
