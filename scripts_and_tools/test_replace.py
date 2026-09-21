import win32com.client
import os

folder = r'c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word\Mẫu Chuyển nhượng công ty TNHH 1 TV'
path = os.path.join(folder, '02. Thông báo thay đổi chủ sở hữu.docx')

word = win32com.client.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = False

try:
    doc = word.Documents.Open(path, ReadOnly=False)
    old_text = "[ĐÃ XÓA]"
    new_text = "[TEN_CONG_TY_VN]"
    
    for story in doc.StoryRanges:
        while story:
            rng = story.Duplicate
            # Execute(FindText, MatchCase, MatchWholeWord, MatchWildcards, MatchSoundsLike, MatchAllWordForms, Forward, Wrap, Format, ReplaceWith, Replace)
            rng.Find.Execute(old_text, False, False, False, False, False, True, 1, False, new_text, 2)
            story = story.NextStoryRange
            
    doc.Save()
    doc.Close()
    print("Replaced and saved successfully.")
except Exception as e:
    print("Error:", e)
finally:
    word.Quit()
