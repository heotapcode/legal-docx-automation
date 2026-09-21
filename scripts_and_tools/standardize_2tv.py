import os
import win32com.client
import json

BASE_DIR = r"c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word"
folder_path = os.path.join(BASE_DIR, "Mẫu tăng vốn công ty TNHH 2TV")

replacements = [
    ("[ĐÃ XÓA]", "[TEN_CONG_TY_VN]"),
    ("[ĐÃ XÓA]", "[MA_SO_THUE]"),
    ("[ĐÃ XÓA]", "[MA_SO_THUE]"),
    ("Tầng 2 số NO-27, LK 10, khu đất dịch vụ Hà Trì, Phường Hà Đông, TP Hà Nội", "[DIA_CHI_SO_NHA], [DIA_CHI_XA_PHUONG], [DIA_CHI_QUAN_HUYEN], [DIA_CHI_TINH_THANH]"),
    
    ("100.000.000", "[VON_CU_SO]"),
    ("Một trăm triệu đồng", "[VON_CU_CHU]"),
    ("6.000.000.000", "[VON_MOI_SO]"),
    ("Sáu tỷ đồng", "[VON_MOI_CHU]"),
    
    ("[ĐÃ XÓA]", "[DDPL_HO_TEN]"),
    ("[ĐÃ XÓA]", "[DDPL_NGAY_SINH]"),
    ("[ĐÃ XÓA]", "[DDPL_SO_CCCD]"),
    ("[ĐÃ XÓA]", "[DDPL_DIA_CHI_DAY_DU]"),
    ("65.000.000", "[DDPL_VON_CU_SO]"),
    ("Sáu mươi lăm triệu đồng", "[DDPL_VON_CU_CHU]"),
    ("3.900.000.000", "[DDPL_VON_MOI_SO]"),
    
    ("[ĐÃ XÓA]", "[TV2_HO_TEN]"),
    ("[ĐÃ XÓA]", "[TV2_NGAY_SINH]"),
    ("[ĐÃ XÓA]", "[TV2_SO_CCCD]"),
    ("[ĐÃ XÓA]", "[TV2_DIA_CHI_DAY_DU]"),
    ("35.000.000", "[TV2_VON_CU_SO]"),
    ("Ba mươi lăm triệu đồng", "[TV2_VON_CU_CHU]"),
    ("2.100.000.000", "[TV2_VON_MOI_SO]"),
    ("Hai tỷ một trăm triệu đồng", "[TV2_VON_MOI_CHU]"),
    
    ("65", "[DDPL_TY_LE]"),
    ("35", "[TV2_TY_LE]"),
]

def standardize_word_files():
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    try:
        files = [f for f in os.listdir(folder_path) if f.endswith(".doc") or f.endswith(".docx")]
        for file in files:
            if file.startswith("~$"): continue
            path = os.path.join(folder_path, file)
            print(f"Processing: {path}")
            
            doc = word.Documents.Open(path, ReadOnly=False, Format=0)
            
            for old_text, new_text in replacements:
                for story in doc.StoryRanges:
                    while story:
                        rng = story.Duplicate
                        # Execute(FindText, MatchCase, MatchWholeWord, MatchWildcards, MatchSoundsLike, MatchAllWordForms, Forward, Wrap, Format, ReplaceWith, Replace)
                        rng.Find.Execute(old_text, False, False, False, False, False, True, 1, False, new_text, 2)
                        story = story.NextStoryRange
            doc.Save()
            doc.Close()
            print(f"Saved: {file}")
            
        # Update folder_keys.json
        keys_set = []
        for old, new in replacements:
            key = new.strip("[]")
            if "," in new: # Address part logic
                for part in new.split(","):
                    k = part.strip(" []")
                    if k and k not in keys_set:
                        keys_set.append(k)
            else:
                if key not in keys_set:
                    keys_set.append(key)
        
        json_path = os.path.join(BASE_DIR, "folder_keys.json")
        data = {}
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        
        data["tăng vốn công ty TNHH 2TV"] = keys_set
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print("Done standardizing and updating json.")
    except Exception as e:
        print("Error:", e)
        import traceback
        traceback.print_exc()
    finally:
        word.Quit()

if __name__ == "__main__":
    standardize_word_files()
