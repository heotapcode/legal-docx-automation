"""Xóa thông tin cá nhân của người thật còn sót trong file mẫu (dữ liệu mẫu từ hồ sơ cũ).

Chạy từ thư mục gốc repo (chạy lại nhiều lần vẫn an toàn):
    python scripts_and_tools/scrub_sample_people.py

Các giá trị này không lọt vào hồ sơ sinh ra (backend thay cả đoạn / dựng lại bảng thành viên),
nhưng vẫn là dữ liệu cá nhân nằm trong repo. Chỉ xóa giá trị, giữ nguyên nhãn và cấu trúc bảng.
"""
import sys
from pathlib import Path

import docx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from localize_ha_noi import TEMPLATES, iter_paragraphs, replace_span  # noqa: E402

# (thư mục bộ mẫu, file) -> các chuỗi cần xóa
TARGETS = {
    ("Thành lập mới công ty Cổ Phần", "02. Điều lệ.docx"): [
        "[ĐÃ XÓA]", "[ĐÃ XÓA]", "[ĐÃ XÓA]", "[ĐÃ XÓA].",
        "[ĐÃ XÓA]", "[ĐÃ XÓA]", "[ĐÃ XÓA]",
        "[ĐÃ XÓA].",
    ],
    ("Thành lập mới công ty Cổ Phần", "03. Danh sách cổ đông sáng lập.docx"): [
        "[ĐÃ XÓA]", "[ĐÃ XÓA]", "[ĐÃ XÓA]", "[ĐÃ XÓA]",
        "[ĐÃ XÓA]", "[ĐÃ XÓA]", "[ĐÃ XÓA]",
        "[ĐÃ XÓA]",
    ],
    ("Thành lập mới công ty TNHH 2 TV", "02. Điều lệ.docx"): [
        "[ĐÃ XÓA]", "[ĐÃ XÓA]", "[ĐÃ XÓA]", "[ĐÃ XÓA]",
    ],
    ("Thành lập mới công ty TNHH 2 TV", "03. Danh sách thành viên.docx"): [
        "[ĐÃ XÓA]", "[ĐÃ XÓA]", "[ĐÃ XÓA]", "[ĐÃ XÓA]",
    ],
}


def target_paths(folder: str, fname: str):
    path = TEMPLATES / folder / fname
    if path.exists():
        yield path


def main():
    total = 0
    for (folder, fname), values in TARGETS.items():
        for path in target_paths(folder, fname):
            total += scrub(path, values)
    print(f"Tổng: {total} chỗ")


def scrub(path: Path, values) -> int:
    doc = docx.Document(str(path))
    n = 0
    for p in iter_paragraphs(doc):
        for v in values:
            while v in p.text:
                i = p.text.index(v)
                replace_span(p, i, i + len(v), "")
                n += 1
    if n:
        doc.save(str(path))
    left = [v for v in values for p in iter_paragraphs(docx.Document(str(path))) if v in p.text]
    assert not left, (str(path), left)
    print(f"{path.relative_to(REPO_ROOT)}: xóa {n} chỗ")
    return n


if __name__ == "__main__":
    main()
