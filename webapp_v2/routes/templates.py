import os
import json
import re
from fastapi import APIRouter, HTTPException
from config import TEMPLATES_DIR
from services.render_service import validate_template_dir

router = APIRouter(prefix="/api/templates", tags=["Templates"])

@router.get("")
def get_templates():
    templates = []
    if TEMPLATES_DIR.exists():
        for d in sorted(TEMPLATES_DIR.iterdir()):
            if d.is_dir():
                schema_path = d / "_schema.json"
                docx_files = [f for f in d.glob("*.docx") if not f.name.startswith(("~$", "_"))]

                if schema_path.exists():
                    try:
                        with open(schema_path, "r", encoding="utf-8") as f:
                            s = json.load(f)
                            templates.append({
                                "id": s.get("id", ""),
                                "name": d.name,
                                "display_name": s.get("display_name", d.name),
                                "category": s.get("category", "Khác"),
                                "description": s.get("description", ""),
                                "file_count": len(docx_files),
                                "has_schema": True,
                                "has_nganh": s.get("has_nganh", False)
                            })
                            continue
                    except Exception:
                        pass

                # Fallback if no schema or parse error
                cat = "Thành lập mới" if "Thành lập mới" in d.name else "Thay đổi"
                templates.append({
                    "id": "",
                    "name": d.name,
                    "display_name": d.name,
                    "category": cat,
                    "description": "",
                    "file_count": len(docx_files),
                    "has_schema": False,
                    "has_nganh": "Thành lập mới" in d.name
                })

    return {"templates": templates}

@router.get("/{template_name}/schema")
def get_template_schema(template_name: str):
    try:
        target_dir = validate_template_dir(template_name)
    except (ValueError, FileNotFoundError):
        raise HTTPException(status_code=404, detail=f"Không tìm thấy schema cho mẫu: {template_name}")

    schema_path = target_dir / "_schema.json"
    if not schema_path.exists():
        raise HTTPException(status_code=404, detail=f"Không tìm thấy schema cho mẫu: {template_name}")

    with open(schema_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Lấy danh sách các file docx thực tế trong bộ mẫu
    docx_files = sorted([f.name for f in target_dir.glob("*.docx") if not f.name.startswith(("~$", "_"))])
    data["doc_files"] = docx_files
    data["file_count"] = len(docx_files)

    return data
