import os
import win32com.client
import time

BASE_DIR = r"c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word"

def convert_doc_to_docx():
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    converted_count = 0

    try:
        for folder_name in os.listdir(BASE_DIR):
            if folder_name.startswith("Mẫu ") and os.path.isdir(os.path.join(BASE_DIR, folder_name)):
                folder_path = os.path.join(BASE_DIR, folder_name)
                for file_name in os.listdir(folder_path):
                    if file_name.endswith(".doc") and not file_name.startswith("~$"):
                        doc_path = os.path.join(folder_path, file_name)
                        docx_path = doc_path + "x"
                        
                        doc = None
                        for attempt in range(3):
                            try:
                                doc = word.Documents.Open(doc_path, ReadOnly=True, ConfirmConversions=False)
                                break
                            except Exception:
                                time.sleep(1)
                                
                        if doc:
                            try:
                                # wdFormatXMLDocument = 16
                                doc.SaveAs(docx_path, FileFormat=16)
                                doc.Close(False)
                                os.remove(doc_path)
                                print(f"Converted: {file_name} -> {file_name}x")
                                converted_count += 1
                            except Exception as e:
                                print(f"Failed to save {file_name}: {e}")
                                if doc:
                                    doc.Close(False)
    finally:
        word.Quit()
        
    print(f"Total converted files: {converted_count}")

if __name__ == '__main__':
    convert_doc_to_docx()
