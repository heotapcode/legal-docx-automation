import docx
from pathlib import Path

f = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word\webapp_v2\templates\Tăng vốn công ty TNHH 2 TV\04. Giấy ủy quyền.docx")
doc = docx.Document(f)

p9 = doc.paragraphs[8]
if p9.runs[0].text == "Ông":
    p9.runs[0].text = "{{ ddpl_danh_xung }}"

p11 = doc.paragraphs[10]
if "\tGiới tính: Nam" in p11.runs[2].text:
    p11.runs[2].text = p11.runs[2].text.replace("\tGiới tính: Nam", "\tGiới tính: {{ ddpl_gioi_tinh }}")

doc.save(f)
print("Updated 04. Giấy ủy quyền.docx successfully!")
