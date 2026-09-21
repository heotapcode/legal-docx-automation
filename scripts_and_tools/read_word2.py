import os
import win32com.client

folder_path = r'c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word\Mẫu tăng vốn công ty TNHH 2TV'
output_path = r'c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word\word_content2.txt'

word = win32com.client.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = False

try:
    with open(output_path, 'w', encoding='utf-8') as f:
        files = [file for file in os.listdir(folder_path) if file.endswith(".doc") or file.endswith(".docx")]
        for file in files:
            if file.startswith("~$"): continue
            f.write(f"\n--- {file} ---\n")
            path = os.path.join(folder_path, file)
            print(f"Opening: {path}")
            doc = word.Documents.Open(path, ReadOnly=True, Format=0)
            
            for story in doc.StoryRanges:
                while story:
                    text = story.Text
                    if text.strip():
                        # Write out all text to find what to replace
                        f.write(text.replace('\r', '\n'))
                    story = story.NextStoryRange
            doc.Close(False)
finally:
    word.Quit()
