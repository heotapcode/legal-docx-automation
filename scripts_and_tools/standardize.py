import win32com.client
import os
import json

folder = r'c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word\Mẫu Chuyển nhượng công ty TNHH 1 TV'

replacements = {
    "[ĐÃ XÓA]": "[TEN_CONG_TY_VN]",
    "[ĐÃ XÓA]": "[MA_SO_THUE]",
    "[ĐÃ XÓA]": "[MA_SO_THUE]",
    "[ĐÃ XÓA]": "[DDPL_CU_HO_TEN]",
    "[ĐÃ XÓA]": "[DDPL_CU_NGAY_SINH]",
    "[ĐÃ XÓA]": "[DDPL_CU_SO_CCCD]",
    "[ĐÃ XÓA]": "[DDPL_CU_DIA_CHI_DAY_DU]",
    "[ĐÃ XÓA]": "[DDPL_HO_TEN]",
    "[ĐÃ XÓA]": "[DDPL_NGAY_SINH]",
    "[ĐÃ XÓA]": "[DDPL_SO_CCCD]",
    "Tổ Dân Phố 16, Phường Yên Nghĩa,  Thành phố Hà Nội": "[DDPL_DIA_CHI_SO_NHA], [DDPL_DIA_CHI_XA_PHUONG], [DDPL_DIA_CHI_TINH_THANH]",
    "Tổ Dân Phố 16, Yên Nghĩa, Hà nội": "[DDPL_DIA_CHI_SO_NHA], [DDPL_DIA_CHI_XA_PHUONG], [DDPL_DIA_CHI_TINH_THANH]",
    "Tổ Dân Phố 16": "[DDPL_DIA_CHI_SO_NHA]",
    "Phường Yên Nghĩa": "[DDPL_DIA_CHI_XA_PHUONG]",
    "Thành phố Hà Nội": "[DDPL_DIA_CHI_TINH_THANH]",
    "3.500.000.000": "[VON_DIEU_LE_SO]",
    "Ba tỷ năm trăm triệu đồng": "[VON_DIEU_LE_CHU]",
    "ĐỖ QUANG HIẾU": "[NGUOI_DUOC_UY_QUYEN_HO_TEN]",
    "001089021350": "[NGUOI_DUOC_UY_QUYEN_CCCD]",
    "[ĐÃ XÓA]": "[NGUOI_DUOC_UY_QUYEN_NGAY_SINH]",
    "TK Đường, Phú Xuyên, Hà Nội.": "[NGUOI_DUOC_UY_QUYEN_DIA_CHI]",
    "0987.135.358": "[NGUOI_DUOC_UY_QUYEN_SDT]",
    "dohieu52th@gmail.com": "[NGUOI_DUOC_UY_QUYEN_EMAIL]",
}

def standardize_word_files():
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    wdFindStop = 0
    try:
        files = [f for f in os.listdir(folder) if f.endswith(".doc") or f.endswith(".docx")]
        for file in files:
            if file.startswith("~$"): continue
            path = os.path.join(folder, file)
            print("Processing:", path, flush=True)
            doc = word.Documents.Open(path, ReadOnly=False, Format=0)
            
            for old_text, new_text in replacements.items():
                for story in doc.StoryRanges:
                    while story:
                        rng = story.Duplicate
                        rng.Find.Execute(old_text, False, False, False, False, False, True, 1, False, new_text, 2)
                        story = story.NextStoryRange
            doc.Save()
            doc.Close()
            print("Saved:", file, flush=True)
    except Exception as e:
        print("Error:", e, flush=True)
    finally:
        word.Quit()

def update_folder_keys():
    json_path = r'c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word\folder_keys.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    keys = [
        "TEN_CONG_TY_VN", "MA_SO_THUE", 
        "DDPL_CU_HO_TEN", "DDPL_CU_NGAY_SINH", "DDPL_CU_SO_CCCD", "DDPL_CU_DIA_CHI_DAY_DU",
        "DDPL_HO_TEN", "DDPL_NGAY_SINH", "DDPL_SO_CCCD", 
        "DDPL_DIA_CHI_SO_NHA", "DDPL_DIA_CHI_XA_PHUONG", "DDPL_DIA_CHI_TINH_THANH",
        "VON_DIEU_LE_SO", "VON_DIEU_LE_CHU",
        "NGUOI_DUOC_UY_QUYEN_HO_TEN", "NGUOI_DUOC_UY_QUYEN_CCCD", "NGUOI_DUOC_UY_QUYEN_NGAY_SINH", 
        "NGUOI_DUOC_UY_QUYEN_DIA_CHI", "NGUOI_DUOC_UY_QUYEN_SDT", "NGUOI_DUOC_UY_QUYEN_EMAIL"
    ]
    
    data["Chuyển nhượng công ty TNHH 1 TV"] = keys
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
if __name__ == "__main__":
    standardize_word_files()
    update_folder_keys()
    print("Done standardizing and updating json.")
