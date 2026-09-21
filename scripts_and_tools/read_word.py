import win32com.client
import os

word = win32com.client.DispatchEx('Word.Application')
word.DisplayAlerts = False
folder = r'c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word\Mẫu Chuyển nhượng công ty TNHH 1 TV'
files = [f for f in os.listdir(folder) if f.endswith('.doc') or f.endswith('.docx')]

with open('word_content.txt', 'w', encoding='utf-8') as f_out:
    for file in files:
        if file.startswith('~$'): continue
        path = os.path.join(folder, file)
        print("Opening:", path)
        try:
            doc = word.Documents.Open(path, ReadOnly=True, Format=0)
            text = doc.Content.Text
            f_out.write(f"\n--- {file} ---\n")
            f_out.write(text[:2000]) # First 2000 chars
            doc.Close(False)
        except Exception as e:
            print("Error opening:", path, "-", str(e))

word.Quit()
