import os
import re
import shutil
import zipfile
import json
from pathlib import Path
from docxtpl import DocxTemplate

ROOT = Path(r"C:\Users\Pc\Desktop\Hermes\Điền thông tin file word")
SRC_DIR = ROOT
DST_DIR = ROOT / "webapp_v2" / "templates"
DST_DIR.mkdir(parents=True, exist_ok=True)

# Mapping folder names to clean display names
FOLDER_MAP = {
    "Mẫu Cấp lại giấy đăng ký kinh doanh": "Cấp lại giấy đăng ký kinh doanh",
    "Mẫu Chấm dứt hoạt động địa điểm kinh doanh": "Chấm dứt hoạt động địa điểm kinh doanh",
    "Mẫu Hoạt động lại trước thời hạn": "Hoạt động lại trước thời hạn",
    "Mẫu Thành lập mới địa điểm kinh doanh": "Thành lập mới địa điểm kinh doanh",
    "Mẫu Tạm dừng công ty TNHH 1 TV": "Tạm dừng công ty TNHH 1 TV",
    "Mẫu Tạm dừng công ty TNHH 2 TV": "Tạm dừng công ty TNHH 2 TV",
    "Mẫu Tạm dừng công ty Cổ Phần": "Tạm dừng công ty Cổ Phần",
    "Mẫu Thay đổi nội dung ĐKKD": "Thay đổi nội dung ĐKKD",
    "Mẫu Thành lập mới công  ty TNHH 1 TV": "Thành lập mới công ty TNHH 1 TV",
    "Mẫu Thành lập mới công ty TNHH 2 TV": "Thành lập mới công ty TNHH 2 TV",
    "Mẫu Thành lập mới công ty Cổ Phần": "Thành lập mới công ty Cổ Phần",
    "Mẫu tăng vốn công ty cổ phần": "Tăng vốn công ty Cổ Phần",
    "Mẫu Giải thể công ty TNHH 1 TV": "Giải thể công ty TNHH 1 TV",
    "Mẫu Giải thể công ty TNHH 2 TV": "Giải thể công ty TNHH 2 TV",
    "Mẫu Giải thể công ty Cổ Phần": "Giải thể công ty Cổ Phần",
    "Mẫu tăng vốn công ty TNHH 2TV": "Tăng vốn công ty TNHH 2 TV",
    "Mẫu Chuyển nhượng công ty TNHH 1 TV": "Chuyển nhượng công ty TNHH 1 TV",
    "Mẫu Chuyển nhượng Công ty TNHH 2 TV": "Chuyển nhượng Công ty TNHH 2 TV",
    "Mẫu Chuyển đổi loại hình 1TV sang 2 TV": "Chuyển đổi loại hình 1TV sang 2 TV",
}

def convert_docx_xml_brackets_to_jinja(src_path: Path, dst_path: Path) -> int:
    """
    Cleans split runs inside [KEY] brackets and converts to {{ key }}
    """
    def merge_bracket_tags(xml: str) -> str:
        def clean(m):
            raw = m.group(0)
            content = re.sub(r"<[^>]+>", "", raw)
            if re.match(r"^\[[A-Za-z0-9_]+\]$", content):
                key = content[1:-1].lower()
                return f"{{{{ {key} }}}}"
            return raw
        # Matches [ ... ] with whatever tags inside
        return re.sub(r"\[(?:(?!\[).)*?\]", clean, xml, flags=re.DOTALL)

    converted_count = 0
    with zipfile.ZipFile(src_path, "r") as zin, zipfile.ZipFile(dst_path, "w") as zout:
        for item in zin.infolist():
            buf = zin.read(item.filename)
            if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                xml = buf.decode("utf-8")
                # Count matches
                matches = re.findall(r"\[[A-Za-z0-9_]+\]", re.sub(r"<[^>]+>", "", xml))
                converted_count += len(matches)
                new_xml = merge_bracket_tags(xml)
                zout.writestr(item, new_xml.encode("utf-8"))
            else:
                zout.writestr(item, buf)
    return converted_count

def get_schema_for_template(template_clean_name: str) -> dict:
    tname = template_clean_name

    # 1. Cấp lại giấy đăng ký kinh doanh
    if tname == "Cấp lại giấy đăng ký kinh doanh":
        return {
            "name": tname,
            "display_name": tname,
            "category": "Cấp lại & Thay đổi",
            "description": "Bộ hồ sơ xin cấp lại Giấy chứng nhận đăng ký doanh nghiệp bị mất, cháy, rách hoặc tiêu hủy",
            "has_nganh": False,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Doanh nghiệp",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty (tiếng Việt)", "type": "text", "required": True},
                        {"key": "ma_so_thue", "label": "Mã số thuế / Mã số DN", "type": "mst_lookup", "required": True}
                    ]
                },
                {
                    "id": "ddpl",
                    "title": "Người đại diện theo pháp luật",
                    "fields": [
                        {"key": "ddpl", "label": "Thông tin người ĐDPL", "type": "person", "ocr": True, "required": True}
                    ]
                }
            ]
        }

    # 2. Chấm dứt hoạt động địa điểm kinh doanh
    if tname == "Chấm dứt hoạt động địa điểm kinh doanh":
        return {
            "name": tname,
            "display_name": tname,
            "category": "Địa điểm kinh doanh",
            "description": "Thông báo chấm dứt hoạt động địa điểm kinh doanh của doanh nghiệp",
            "has_nganh": False,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Doanh nghiệp & Địa điểm",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty (tiếng Việt)", "type": "text", "required": True},
                        {"key": "ma_so_thue", "label": "Mã số thuế", "type": "mst_lookup", "required": True},
                        {"key": "dia_chi_so_nha", "label": "Địa chỉ địa điểm kinh doanh (số nhà, đường)", "type": "text", "required": True},
                        {"key": "dia_chi_xa_phuong", "label": "Xã/Phường", "type": "text", "required": True},
                        {"key": "dia_chi_tinh_thanh", "label": "Tỉnh/Thành phố", "type": "text", "required": True}
                    ]
                },
                {
                    "id": "ddpl",
                    "title": "Người đại diện theo pháp luật",
                    "fields": [
                        {"key": "ddpl", "label": "Thông tin người ĐDPL", "type": "person", "ocr": True, "required": True}
                    ]
                }
            ]
        }

    # 3. Hoạt động lại trước thời hạn
    if tname == "Hoạt động lại trước thời hạn":
        return {
            "name": tname,
            "display_name": tname,
            "category": "Tạm dừng & Hoạt động lại",
            "description": "Thông báo đăng ký tiếp tục kinh doanh trước thời hạn đã thông báo",
            "has_nganh": False,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Doanh nghiệp",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty (tiếng Việt)", "type": "text", "required": True},
                        {"key": "ma_so_thue", "label": "Mã số thuế", "type": "mst_lookup", "required": True}
                    ]
                },
                {
                    "id": "ddpl",
                    "title": "Người đại diện theo pháp luật",
                    "fields": [
                        {"key": "ddpl", "label": "Thông tin người ĐDPL", "type": "person", "ocr": True, "required": True}
                    ]
                }
            ]
        }

    # 4. Thành lập mới địa điểm kinh doanh
    if tname == "Thành lập mới địa điểm kinh doanh":
        return {
            "name": tname,
            "display_name": tname,
            "category": "Địa điểm kinh doanh",
            "description": "Bộ hồ sơ đăng ký thành lập địa điểm kinh doanh mới",
            "has_nganh": False,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Công ty mẹ & Địa điểm mới",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty chủ quản", "type": "text", "required": True},
                        {"key": "ma_so_thue", "label": "Mã số thuế công ty", "type": "mst_lookup", "required": True},
                        {"key": "dia_chi_so_nha", "label": "Địa chỉ địa điểm mới (Số nhà, đường)", "type": "text", "required": True},
                        {"key": "dia_chi_xa_phuong", "label": "Xã/Phường địa điểm mới", "type": "text", "required": True},
                        {"key": "dia_chi_tinh_thanh", "label": "Tỉnh/Thành phố", "type": "text", "required": True}
                    ]
                },
                {
                    "id": "ddpl",
                    "title": "Người đại diện theo pháp luật",
                    "fields": [
                        {"key": "ddpl", "label": "Thông tin người ĐDPL", "type": "person", "ocr": True, "required": True}
                    ]
                }
            ]
        }

    # 5, 6, 7. Tạm dừng
    if "Tạm dừng" in tname:
        cat = "Tạm dừng & Hoạt động lại"
        return {
            "name": tname,
            "display_name": tname,
            "category": cat,
            "description": f"Hồ sơ tạm dừng kinh doanh đối với {tname.replace('Tạm dừng ', '')}",
            "has_nganh": False,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Doanh nghiệp",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty", "type": "text", "required": True},
                        {"key": "ma_so_thue", "label": "Mã số thuế", "type": "mst_lookup", "required": True}
                    ]
                },
                {
                    "id": "ddpl",
                    "title": "Người đại diện theo pháp luật",
                    "fields": [
                        {"key": "ddpl", "label": "Thông tin người ĐDPL", "type": "person", "ocr": True, "required": True}
                    ]
                }
            ]
        }

    # 8. Thay đổi nội dung ĐKKD
    if tname == "Thay đổi nội dung ĐKKD":
        return {
            "name": tname,
            "display_name": tname,
            "category": "Thay đổi ĐKKD",
            "description": "Hồ sơ thay đổi các nội dung đăng ký doanh nghiệp (Tên, Địa chỉ, Thành viên, Vốn, Ngành nghề...)",
            "has_nganh": True,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Doanh nghiệp",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty", "type": "text", "required": True},
                        {"key": "ma_so_thue", "label": "Mã số thuế", "type": "mst_lookup", "required": True}
                    ]
                },
                {
                    "id": "sections",
                    "title": "Các nội dung cần thay đổi",
                    "fields": [
                        {
                            "key": "dkkd_selected",
                            "label": "Chọn các mục thay đổi",
                            "type": "checkbox_group",
                            "options": [
                                {"value": "A1", "label": "A1: Đăng ký thay đổi tên doanh nghiệp"},
                                {"value": "A2", "label": "A2: Đăng ký thay đổi địa chỉ trụ sở chính"},
                                {"value": "A3", "label": "A3: Đăng ký thay đổi thành viên công ty TNHH"},
                                {"value": "A4", "label": "A4: Đăng ký thay đổi vốn điều lệ"},
                                {"value": "A5", "label": "A5: Thông báo thay đổi ngành, nghề kinh doanh"},
                                {"value": "A6", "label": "A6: Thông báo thay đổi thông tin đăng ký thuế"},
                                {"value": "A7", "label": "A7: Chủ sở hữu hưởng lợi của doanh nghiệp"}
                            ]
                        }
                    ]
                },
                {
                    "id": "ddpl",
                    "title": "Người đại diện theo pháp luật",
                    "fields": [
                        {"key": "ddpl", "label": "Thông tin người ĐDPL", "type": "person", "ocr": True, "required": True}
                    ]
                }
            ]
        }

    # 9. Thành lập mới công ty TNHH 1 TV
    if tname == "Thành lập mới công ty TNHH 1 TV":
        return {
            "name": tname,
            "display_name": tname,
            "category": "Thành lập mới",
            "description": "Bộ hồ sơ trọn gói thành lập mới Công ty TNHH Một thành viên",
            "has_nganh": True,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Công ty",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty (tiếng Việt)", "type": "text", "required": True},
                        {"key": "ten_cong_ty_en", "label": "Tên công ty (tiếng Anh)", "type": "text"},
                        {"key": "ten_cong_ty_viet_tat", "label": "Tên viết tắt", "type": "text"},
                        {"key": "dia_chi_so_nha", "label": "Số nhà, tên đường", "type": "text", "required": True},
                        {"key": "dia_chi_xa_phuong", "label": "Xã/Phường", "type": "text", "required": True},
                        {"key": "dia_chi_tinh_thanh", "label": "Tỉnh/Thành phố", "type": "text", "required": True},
                        {"key": "von_dieu_le_so", "label": "Vốn điều lệ (VNĐ)", "type": "money", "required": True},
                        {"key": "sdt_cong_ty", "label": "Số điện thoại liên hệ", "type": "phone", "required": True},
                        {"key": "email_cong_ty", "label": "Email công ty", "type": "email"}
                    ]
                },
                {
                    "id": "ddpl",
                    "title": "Chủ sở hữu & Người đại diện theo pháp luật",
                    "fields": [
                        {"key": "ddpl", "label": "Thông tin Chủ sở hữu kiêm ĐDPL", "type": "person", "ocr": True, "required": True}
                    ]
                }
            ]
        }

    # 10. Thành lập mới công ty TNHH 2 TV
    if tname == "Thành lập mới công ty TNHH 2 TV":
        return {
            "name": tname,
            "display_name": tname,
            "category": "Thành lập mới",
            "description": "Bộ hồ sơ trọn gói thành lập mới Công ty TNHH Hai thành viên trở lên",
            "has_nganh": True,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Công ty",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty (tiếng Việt)", "type": "text", "required": True},
                        {"key": "ten_cong_ty_en", "label": "Tên công ty (tiếng Anh)", "type": "text"},
                        {"key": "ten_cong_ty_viet_tat", "label": "Tên viết tắt", "type": "text"},
                        {"key": "dia_chi_so_nha", "label": "Số nhà, tên đường", "type": "text", "required": True},
                        {"key": "dia_chi_xa_phuong", "label": "Xã/Phường", "type": "text", "required": True},
                        {"key": "dia_chi_tinh_thanh", "label": "Tỉnh/Thành phố", "type": "text", "required": True},
                        {"key": "von_dieu_le_so", "label": "Vốn điều lệ (VNĐ)", "type": "money", "required": True},
                        {"key": "sdt_cong_ty", "label": "Số điện thoại liên hệ", "type": "phone", "required": True},
                        {"key": "email_cong_ty", "label": "Email công ty", "type": "email"}
                    ]
                },
                {
                    "id": "ddpl",
                    "title": "Người đại diện theo pháp luật",
                    "fields": [
                        {"key": "ddpl", "label": "Thông tin người ĐDPL", "type": "person", "ocr": True, "required": True}
                    ]
                },
                {
                    "id": "members",
                    "title": "Danh sách thành viên góp vốn",
                    "fields": [
                        {
                            "key": "thanh_vien",
                            "label": "Thành viên công ty",
                            "type": "person_list",
                            "min": 2,
                            "ocr": True,
                            "extra_fields": [
                                {"key": "von_gop", "label": "Vốn góp (VNĐ)", "type": "money", "required": True},
                                {"key": "ty_le", "label": "Tỷ lệ góp vốn (%)", "type": "number", "required": True}
                            ]
                        }
                    ]
                }
            ]
        }

    # 11. Thành lập mới công ty Cổ Phần
    if tname == "Thành lập mới công ty Cổ Phần":
        return {
            "name": tname,
            "display_name": tname,
            "category": "Thành lập mới",
            "description": "Bộ hồ sơ trọn gói thành lập mới Công ty Cổ Phần (tối thiểu 3 cổ đông)",
            "has_nganh": True,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Công ty",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty (tiếng Việt)", "type": "text", "required": True},
                        {"key": "ten_cong_ty_en", "label": "Tên công ty (tiếng Anh)", "type": "text"},
                        {"key": "ten_cong_ty_viet_tat", "label": "Tên viết tắt", "type": "text"},
                        {"key": "dia_chi_so_nha", "label": "Số nhà, tên đường", "type": "text", "required": True},
                        {"key": "dia_chi_xa_phuong", "label": "Xã/Phường", "type": "text", "required": True},
                        {"key": "dia_chi_quan_huyen", "label": "Quận/Huyện", "type": "text"},
                        {"key": "dia_chi_tinh_thanh", "label": "Tỉnh/Thành phố", "type": "text", "required": True},
                        {"key": "von_dieu_le_so", "label": "Vốn điều lệ (VNĐ)", "type": "money", "required": True},
                        {"key": "sdt_cong_ty", "label": "Số điện thoại liên hệ", "type": "phone", "required": True},
                        {"key": "email_cong_ty", "label": "Email công ty", "type": "email"}
                    ]
                },
                {
                    "id": "ddpl",
                    "title": "Người đại diện theo pháp luật",
                    "fields": [
                        {"key": "ddpl", "label": "Thông tin người ĐDPL", "type": "person", "ocr": True, "required": True}
                    ]
                },
                {
                    "id": "shareholders",
                    "title": "Danh sách cổ đông sáng lập",
                    "fields": [
                        {
                            "key": "thanh_vien",
                            "label": "Cổ đông sáng lập",
                            "type": "person_list",
                            "min": 3,
                            "ocr": True,
                            "extra_fields": [
                                {"key": "von_gop", "label": "Giá trị cổ phần (VNĐ)", "type": "money", "required": True},
                                {"key": "ty_le", "label": "Tỷ lệ sở hữu (%)", "type": "number", "required": True}
                            ]
                        }
                    ]
                }
            ]
        }

    # 12. Tăng vốn công ty Cổ Phần
    if tname == "Tăng vốn công ty Cổ Phần":
        return {
            "name": tname,
            "display_name": tname,
            "category": "Tăng vốn",
            "description": "Bộ hồ sơ đăng ký tăng vốn điều lệ Công ty Cổ Phần",
            "has_nganh": False,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Doanh nghiệp & Vốn",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty", "type": "text", "required": True},
                        {"key": "ma_so_thue", "label": "Mã số thuế", "type": "mst_lookup", "required": True},
                        {"key": "dia_chi_so_nha", "label": "Số nhà, đường", "type": "text"},
                        {"key": "dia_chi_xa_phuong", "label": "Xã/Phường", "type": "text"},
                        {"key": "dia_chi_tinh_thanh", "label": "Tỉnh/Thành phố", "type": "text"},
                        {"key": "von_cu_so", "label": "Vốn điều lệ cũ (VNĐ)", "type": "money", "required": True},
                        {"key": "von_dieu_le_so", "label": "Vốn điều lệ mới sau khi tăng (VNĐ)", "type": "money", "required": True}
                    ]
                },
                {
                    "id": "ddpl",
                    "title": "Người đại diện theo pháp luật",
                    "fields": [
                        {"key": "ddpl", "label": "Thông tin người ĐDPL", "type": "person", "ocr": True, "required": True}
                    ]
                }
            ]
        }

    # 13, 14, 15. Giải thể
    if "Giải thể" in tname:
        return {
            "name": tname,
            "display_name": tname,
            "category": "Giải thể",
            "description": f"Hồ sơ thủ tục giải thể doanh nghiệp đối với {tname.replace('Giải thể ', '')}",
            "has_nganh": False,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Doanh nghiệp",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty", "type": "text", "required": True},
                        {"key": "ma_so_thue", "label": "Mã số thuế", "type": "mst_lookup", "required": True},
                        {"key": "dia_chi_so_nha", "label": "Số nhà, tên đường", "type": "text"},
                        {"key": "dia_chi_xa_phuong", "label": "Xã/Phường", "type": "text"},
                        {"key": "dia_chi_tinh_thanh", "label": "Tỉnh/Thành phố", "type": "text"}
                    ]
                },
                {
                    "id": "ddpl",
                    "title": "Người đại diện theo pháp luật",
                    "fields": [
                        {"key": "ddpl", "label": "Thông tin người ĐDPL", "type": "person", "ocr": True, "required": True}
                    ]
                }
            ]
        }

    # 16. Tăng vốn công ty TNHH 2 TV
    if tname == "Tăng vốn công ty TNHH 2 TV":
        return {
            "name": tname,
            "display_name": tname,
            "category": "Tăng vốn",
            "description": "Bộ hồ sơ đăng ký tăng vốn điều lệ Công ty TNHH Hai thành viên trở lên",
            "has_nganh": False,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Doanh nghiệp & Vốn",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty", "type": "text", "required": True},
                        {"key": "ma_so_thue", "label": "Mã số thuế", "type": "mst_lookup", "required": True},
                        {"key": "dia_chi_so_nha", "label": "Số nhà, tên đường", "type": "text"},
                        {"key": "dia_chi_xa_phuong", "label": "Xã/Phường", "type": "text"},
                        {"key": "dia_chi_tinh_thanh", "label": "Tỉnh/Thành phố", "type": "text"},
                        {"key": "von_cu_so", "label": "Vốn cũ (VNĐ)", "type": "money", "required": True},
                        {"key": "von_dieu_le_so", "label": "Vốn mới sau khi tăng (VNĐ)", "type": "money", "required": True}
                    ]
                },
                {
                    "id": "ddpl",
                    "title": "Người đại diện theo pháp luật",
                    "fields": [
                        {"key": "ddpl", "label": "Thông tin người ĐDPL", "type": "person", "ocr": True, "required": True}
                    ]
                },
                {
                    "id": "members",
                    "title": "Danh sách thành viên sau khi tăng vốn",
                    "fields": [
                        {
                            "key": "thanh_vien",
                            "label": "Thành viên công ty",
                            "type": "person_list",
                            "min": 2,
                            "ocr": True,
                            "extra_fields": [
                                {"key": "von_gop", "label": "Vốn góp mới (VNĐ)", "type": "money", "required": True},
                                {"key": "ty_le", "label": "Tỷ lệ (%)", "type": "number", "required": True}
                            ]
                        }
                    ]
                }
            ]
        }

    # 17. Chuyển nhượng công ty TNHH 1 TV
    if tname == "Chuyển nhượng công ty TNHH 1 TV":
        return {
            "name": tname,
            "display_name": tname,
            "category": "Chuyển nhượng & Chuyển đổi",
            "description": "Bộ hồ sơ chuyển nhượng toàn bộ vốn chủ sở hữu Công ty TNHH Một thành viên",
            "has_nganh": False,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Doanh nghiệp",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty", "type": "text", "required": True},
                        {"key": "ma_so_thue", "label": "Mã số thuế", "type": "mst_lookup", "required": True},
                        {"key": "von_dieu_le_so", "label": "Vốn điều lệ (VNĐ)", "type": "money", "required": True}
                    ]
                },
                {
                    "id": "seller",
                    "title": "Bên Chuyển nhượng (Chủ sở hữu CŨ)",
                    "fields": [
                        {"key": "ddpl_cu", "label": "Chủ sở hữu cũ", "type": "person", "ocr": True, "required": True}
                    ]
                },
                {
                    "id": "buyer",
                    "title": "Bên Nhận chuyển nhượng (Chủ sở hữu kiêm ĐDPL MỚI)",
                    "fields": [
                        {"key": "ddpl", "label": "Chủ sở hữu / ĐDPL mới", "type": "person", "ocr": True, "required": True}
                    ]
                }
            ]
        }

    # 18. Chuyển nhượng Công ty TNHH 2 TV
    if tname == "Chuyển nhượng Công ty TNHH 2 TV":
        return {
            "name": tname,
            "display_name": tname,
            "category": "Chuyển nhượng & Chuyển đổi",
            "description": "Bộ hồ sơ chuyển nhượng phần vốn góp giữa các thành viên Công ty TNHH 2 thành viên",
            "has_nganh": False,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Doanh nghiệp",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty", "type": "text", "required": True},
                        {"key": "ma_so_thue", "label": "Mã số thuế", "type": "mst_lookup", "required": True}
                    ]
                },
                {
                    "id": "ddpl_cu",
                    "title": "Người đại diện theo pháp luật CŨ",
                    "fields": [
                        {"key": "ddpl_cu", "label": "ĐDPL cũ", "type": "person", "ocr": True, "required": True}
                    ]
                },
                {
                    "id": "ddpl_moi",
                    "title": "Người đại diện theo pháp luật MỚI",
                    "fields": [
                        {"key": "ddpl", "label": "ĐDPL mới (giữ nguyên nếu không đổi)", "type": "person", "ocr": True, "required": True}
                    ]
                },
                {
                    "id": "members",
                    "title": "Danh sách thành viên MỚI sau chuyển nhượng",
                    "fields": [
                        {
                            "key": "thanh_vien",
                            "label": "Thành viên sau chuyển nhượng",
                            "type": "person_list",
                            "min": 2,
                            "ocr": True,
                            "extra_fields": [
                                {"key": "von_gop", "label": "Vốn góp (VNĐ)", "type": "money", "required": True},
                                {"key": "ty_le", "label": "Tỷ lệ (%)", "type": "number", "required": True}
                            ]
                        }
                    ]
                },
                {
                    "id": "transfers",
                    "title": "Thông tin Hợp đồng chuyển nhượng",
                    "fields": [
                        {
                            "key": "chuyen_nhuong",
                            "label": "Các giao dịch chuyển nhượng vốn",
                            "type": "transfer_list",
                            "required": True
                        }
                    ]
                }
            ]
        }

    # 19. Chuyển đổi loại hình 1TV sang 2 TV
    if tname == "Chuyển đổi loại hình 1TV sang 2 TV":
        return {
            "name": tname,
            "display_name": tname,
            "category": "Chuyển nhượng & Chuyển đổi",
            "description": "Bộ hồ sơ chuyển đổi loại hình doanh nghiệp từ Công ty TNHH 1 TV sang Công ty TNHH 2 TV trở lên",
            "has_nganh": True,
            "steps": [
                {
                    "id": "company",
                    "title": "Thông tin Công ty Sau khi chuyển đổi",
                    "fields": [
                        {"key": "ten_cong_ty_vn", "label": "Tên công ty mới (tiếng Việt)", "type": "text", "required": True},
                        {"key": "ten_cong_ty_nn", "label": "Tên tiếng nước ngoài", "type": "text"},
                        {"key": "ten_cong_ty_viet_tat", "label": "Tên viết tắt", "type": "text"},
                        {"key": "ma_so_thue", "label": "Mã số thuế hiện tại", "type": "mst_lookup", "required": True},
                        {"key": "dia_chi_so_nha", "label": "Số nhà, tên đường", "type": "text", "required": True},
                        {"key": "dia_chi_xa_phuong", "label": "Xã/Phường", "type": "text", "required": True},
                        {"key": "dia_chi_tinh_thanh", "label": "Tỉnh/Thành phố", "type": "text", "required": True},
                        {"key": "von_dieu_le_so", "label": "Vốn điều lệ (VNĐ)", "type": "money", "required": True},
                        {"key": "sdt_cong_ty", "label": "Số điện thoại", "type": "phone"},
                        {"key": "email_cong_ty", "label": "Email", "type": "email"}
                    ]
                },
                {
                    "id": "tv1",
                    "title": "Thành viên 1 (Chủ sở hữu cũ kiêm ĐDPL)",
                    "fields": [
                        {"key": "ddpl", "label": "Thành viên 1", "type": "person", "ocr": True, "required": True}
                    ]
                },
                {
                    "id": "tv2",
                    "title": "Thành viên 2 (Thành viên mới tiếp nhận)",
                    "fields": [
                        {
                            "key": "thanh_vien",
                            "label": "Thành viên góp vốn mới",
                            "type": "person_list",
                            "min": 1,
                            "ocr": True,
                            "extra_fields": [
                                {"key": "von_gop", "label": "Vốn góp (VNĐ)", "type": "money", "required": True},
                                {"key": "ty_le", "label": "Tỷ lệ (%)", "type": "number", "required": True}
                            ]
                        }
                    ]
                }
            ]
        }

    # Fallback default schema
    return {
        "name": tname,
        "display_name": tname,
        "category": "Hồ sơ Doanh nghiệp",
        "description": f"Hồ sơ thủ tục {tname}",
        "has_nganh": False,
        "steps": [
            {
                "id": "company",
                "title": "Thông tin Doanh nghiệp",
                "fields": [
                    {"key": "ten_cong_ty_vn", "label": "Tên công ty", "type": "text", "required": True},
                    {"key": "ma_so_thue", "label": "Mã số thuế", "type": "mst_lookup"}
                ]
            },
            {
                "id": "ddpl",
                "title": "Người đại diện theo pháp luật",
                "fields": [
                    {"key": "ddpl", "label": "Thông tin người ĐDPL", "type": "person", "ocr": True}
                ]
            }
        ]
    }

def main():
    print("Starting template conversion to Jinja2 (docxtpl)...")
    total_docs = 0
    total_tags_converted = 0

    for orig_name, clean_name in FOLDER_MAP.items():
        src_folder = SRC_DIR / orig_name
        if not src_folder.exists():
            print(f"Skipping missing source folder: {orig_name}")
            continue

        dst_folder = DST_DIR / clean_name
        dst_folder.mkdir(parents=True, exist_ok=True)

        print(f"\nProcessing [{clean_name}]...")

        # Convert docx files
        doc_count = 0
        for f in sorted(src_folder.iterdir()):
            if not f.name.endswith(".docx") or f.name.startswith("~$"):
                continue

            dst_file = dst_folder / f.name
            try:
                cnt = convert_docx_xml_brackets_to_jinja(f, dst_file)
                total_tags_converted += cnt
                doc_count += 1
                total_docs += 1
                # Quick verification with DocxTemplate
                try:
                    DocxTemplate(str(dst_file))
                except Exception as e:
                    print(f"  Warning: DocxTemplate parse warning for {f.name}: {e}")
            except Exception as e:
                print(f"  Error converting {f.name}: {e}")
                shutil.copy2(str(f), str(dst_file))

        print(f"  -> Converted {doc_count} docx files.")

        # Write _schema.json
        schema = get_schema_for_template(clean_name)
        schema_path = dst_folder / "_schema.json"
        with open(schema_path, "w", encoding="utf-8") as sf:
            json.dump(schema, sf, ensure_ascii=False, indent=2)
        print(f"  -> Generated _schema.json ({len(schema['steps'])} steps)")

    print(f"\n==========================================")
    print(f"CONVERSION COMPLETE!")
    print(f"Total templates converted: {len(FOLDER_MAP)}")
    print(f"Total docx files processed: {total_docs}")
    print(f"Total placeholders converted: {total_tags_converted}")
    print(f"Destination: {DST_DIR}")
    print(f"==========================================")

if __name__ == "__main__":
    main()
