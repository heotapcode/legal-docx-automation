import os
import json
import win32com.client

base_folder = r"c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word"
folders = [f for f in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, f)) and f.startswith("Mẫu ")]

possible_keys = [
    "TEN_CONG_TY_VN", "TEN_CONG_TY_EN", "TEN_CONG_TY_VIET_TAT", "MA_SO_THUE", 
    "DIA_CHI_SO_NHA", "DIA_CHI_XA_PHUONG", "DIA_CHI_QUAN_HUYEN", "DIA_CHI_TINH_THANH",
    "DDPL_HO_TEN", "DDPL_SO_CCCD", "DDPL_NGAY_SINH", "DDPL_GIOI_TINH",
    "DDPL_DIA_CHI_SO_NHA", "DDPL_DIA_CHI_XA_PHUONG", "DDPL_DIA_CHI_TINH_THANH",
    "VON_DIEU_LE_SO", "VON_DIEU_LE_CHU", "SDT_CONG_TY", "EMAIL_CONG_TY"
]

word = win32com.client.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = False

folder_keys = {}

try:
    for folder in folders:
        folder_path = os.path.join(base_folder, folder)
        files = [f for f in os.listdir(folder_path) if f.endswith(".doc") or f.endswith(".docx")]
        
        found_keys = set()
        
        for file in files:
            if file.startswith("~$"): continue
            path = os.path.join(folder_path, file)
            
            try:
                doc = word.Documents.Open(path, ReadOnly=True, Format=0)
                
                # Check each key
                for key in possible_keys:
                    if key in found_keys: continue
                    placeholder = f"[{key}]"
                    
                    found = False
                    for story in doc.StoryRanges:
                        if found: break
                        while story:
                            rng = story.Duplicate
                            rng.Find.ClearFormatting()
                            rng.Find.Text = placeholder
                            rng.Find.Forward = True
                            if rng.Find.Execute():
                                found_keys.add(key)
                                found = True
                                break
                            story = story.NextStoryRange
                doc.Close(False)
            except Exception as e:
                print(f"Error {file}: {e}")
                
        folder_name = folder.replace("Mẫu ", "")
        folder_keys[folder_name] = sorted(list(found_keys))
finally:
    word.Quit()

with open(os.path.join(base_folder, "folder_keys.json"), "w", encoding="utf-8") as f:
    json.dump(folder_keys, f, ensure_ascii=False, indent=4)
    
print("Done extracting keys via COM!")
