import os
import re
import json

base_folder = r"c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word"
folders = [f for f in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, f)) and f.startswith("Mẫu ")]

folder_keys = {}

for folder in folders:
    folder_path = os.path.join(base_folder, folder)
    files = [f for f in os.listdir(folder_path) if f.endswith(".doc") or f.endswith(".docx")]
    
    keys_in_folder = set()
    
    for file in files:
        if file.startswith("~$"): continue
        path = os.path.join(folder_path, file)
        
        try:
            with open(path, 'rb') as f:
                content = f.read()
                
            # Convert to string ignoring errors to find ASCII placeholders
            # .doc files might have utf-16-le, so we try decoding as utf-16-le as well
            text_ascii = content.decode('ascii', errors='ignore')
            text_utf16 = content.decode('utf-16-le', errors='ignore')
            
            matches_ascii = re.findall(r'\[([A_Z_]{5,})\]', text_ascii)
            matches_utf16 = re.findall(r'\[([A_Z_]{5,})\]', text_utf16)
            
            keys_in_folder.update(matches_ascii)
            keys_in_folder.update(matches_utf16)
        except Exception as e:
            print(f"Error {file}: {e}")
            
    folder_name = folder.replace("Mẫu ", "")
    # Sort for consistent output
    folder_keys[folder_name] = sorted(list(keys_in_folder))

with open(os.path.join(base_folder, "folder_keys.json"), "w", encoding="utf-8") as f:
    json.dump(folder_keys, f, ensure_ascii=False, indent=4)
    
print("Done extracting keys!")
