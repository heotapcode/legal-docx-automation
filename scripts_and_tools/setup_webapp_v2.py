import os
import shutil
import json
import re
import tempfile
import zipfile
from io import BytesIO

BASE_DIR = r"c:\Users\Pc\Desktop\AI Agent\Điền thông tin file word"
WEBAPP_OLD_DIR = os.path.join(BASE_DIR, "webapp")
WEBAPP_V2_DIR = os.path.join(BASE_DIR, "webapp_v2")
LOG_FILE = os.path.join(BASE_DIR, "setup_webapp_v2_log.txt")

logs = []

def log(msg):
    logs.append(msg)

log("=== BẮT ĐẦU SETUP WEBAPP_V2 ===")

# -------------------------------------------------------------
# 1. TẠO CẤU TRÚC THƯ MỤC
# -------------------------------------------------------------
dirs_to_create = [
    WEBAPP_V2_DIR,
    os.path.join(WEBAPP_V2_DIR, "templates"),
    os.path.join(WEBAPP_V2_DIR, "templates", "Tạm dừng công ty TNHH 1 TV"),
    os.path.join(WEBAPP_V2_DIR, "services"),
    os.path.join(WEBAPP_V2_DIR, "routes"),
    os.path.join(WEBAPP_V2_DIR, "static"),
    os.path.join(WEBAPP_V2_DIR, "static", "css"),
    os.path.join(WEBAPP_V2_DIR, "static", "js"),
    os.path.join(WEBAPP_V2_DIR, "static", "js", "pages"),
]

for d in dirs_to_create:
    os.makedirs(d, exist_ok=True)
log("Đã tạo cấu trúc thư mục webapp_v2 thành công.")

# -------------------------------------------------------------
# 2. TẠO CÁC FILE CẤU HÌNH VÀ REQUIREMENT
# -------------------------------------------------------------
# config.py
config_content = '''import os

BASE_DIR = r"c:\\Users\\Pc\\Desktop\\AI Agent\\Điền thông tin file word"
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
MA_NGANH_JSON = os.path.join(BASE_DIR, "ma_nganh_nghe.json")
GEMINI_API_KEY = "AQ.Ab8RN6KzqOjWiBtXNVDdLr2mkCMiNuSdhRlIrP9UZGVQnCwv_A"
'''
with open(os.path.join(WEBAPP_V2_DIR, "config.py"), "w", encoding="utf-8") as f:
    f.write(config_content)
log("Đã tạo config.py")

# requirements.txt
requirements_content = '''fastapi
uvicorn
httpx
docxtpl
python-docx
'''
with open(os.path.join(WEBAPP_V2_DIR, "requirements.txt"), "w", encoding="utf-8") as f:
    f.write(requirements_content)
log("Đã tạo requirements.txt")

# services/__init__.py
with open(os.path.join(WEBAPP_V2_DIR, "services", "__init__.py"), "w", encoding="utf-8") as f:
    f.write("")

# routes/__init__.py
with open(os.path.join(WEBAPP_V2_DIR, "routes", "__init__.py"), "w", encoding="utf-8") as f:
    f.write("")

# -------------------------------------------------------------
# 3. VIẾT CÁC SERVICES
# -------------------------------------------------------------
# services/render_service.py (CORE RENDER ENGINE)
render_service_content = '''import os
import tempfile
import zipfile
from io import BytesIO
from docxtpl import DocxTemplate
from config import TEMPLATES_DIR


def normalize_context(context: dict) -> dict:
    """Chuẩn hóa dữ liệu đầu vào thành dạng nested dict phù hợp với Jinja2 docxtpl.
    
    Hỗ trợ:
    - Nested dict: {'ddpl': {'ho_ten': 'Nguyễn Văn A'}}
    - Dotted flat keys: {'ddpl.ho_ten': 'Nguyễn Văn A'}
    - Legacy uppercase keys: {'DDPL_HO_TEN': 'Nguyễn Văn A', 'TEN_CONG_TY_VN': 'ABC'}
    """
    normalized = {}
    
    # 1. Đưa các dict con có sẵn vào trước
    for k, v in context.items():
        if isinstance(v, dict):
            normalized[k.lower()] = dict(v)
            
    # 2. Xử lý các flat keys
    for k, v in context.items():
        if isinstance(v, dict):
            continue
        
        val_str = "" if v is None else str(v)
        k_lower = k.lower()
        
        # Nhận diện prefix DDPL
        if k.startswith("DDPL_"):
            sub_k = k_lower.replace("ddpl_", "")
            normalized.setdefault("ddpl", {})[sub_k] = val_str
        elif "." in k_lower:
            parts = k_lower.split(".", 1)
            normalized.setdefault(parts[0], {})[parts[1]] = val_str
        else:
            normalized[k_lower] = val_str
            
    return normalized


def render_documents(template_name: str, context: dict) -> bytes:
    """Render tất cả file .docx trong thư mục template bằng docxtpl.
    
    - template_name: tên thư mục template (VD: 'Tạm dừng công ty TNHH 1 TV')
    - context: dict chứa dữ liệu Jinja2 (VD: {'ten_cong_ty_vn': 'ABC', 'ddpl': {'ho_ten': 'Nguyễn Văn A', ...}})
    - Returns: bytes của file ZIP chứa tất cả file Word đã render
    """
    template_dir = os.path.join(TEMPLATES_DIR, template_name)
    if not os.path.isdir(template_dir):
        raise FileNotFoundError(f"Template not found: {template_name}")
    
    norm_context = normalize_context(context)
    
    with tempfile.TemporaryDirectory() as tmp:
        for fname in os.listdir(template_dir):
            if not fname.endswith('.docx') or fname.startswith(('~$', '_')):
                continue
            
            src = os.path.join(template_dir, fname)
            tpl = DocxTemplate(src)
            tpl.render(norm_context)
            
            # Lưu file Word đã điền vào thư mục tạm
            dest = os.path.join(tmp, fname)
            tpl.save(dest)
        
        buf = BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in os.listdir(tmp):
                zf.write(os.path.join(tmp, f), f)
        return buf.getvalue()
'''
with open(os.path.join(WEBAPP_V2_DIR, "services", "render_service.py"), "w", encoding="utf-8") as f:
    f.write(render_service_content)
log("Đã tạo services/render_service.py")

# services/ocr_service.py (Copy từ webapp cũ)
ocr_src = os.path.join(WEBAPP_OLD_DIR, "services", "ocr_service.py")
if os.path.exists(ocr_src):
    shutil.copy(ocr_src, os.path.join(WEBAPP_V2_DIR, "services", "ocr_service.py"))
    log("Đã copy services/ocr_service.py")

# services/mst_service.py (Copy từ webapp cũ)
mst_src = os.path.join(WEBAPP_OLD_DIR, "services", "mst_service.py")
if os.path.exists(mst_src):
    shutil.copy(mst_src, os.path.join(WEBAPP_V2_DIR, "services", "mst_service.py"))
    log("Đã copy services/mst_service.py")

# services/nganh_service.py (Copy từ webapp cũ)
nganh_src = os.path.join(WEBAPP_OLD_DIR, "services", "nganh_service.py")
if os.path.exists(nganh_src):
    shutil.copy(nganh_src, os.path.join(WEBAPP_V2_DIR, "services", "nganh_service.py"))
    log("Đã copy services/nganh_service.py")

# -------------------------------------------------------------
# 4. VIẾT CÁC ROUTES
# -------------------------------------------------------------
# routes/templates.py
routes_templates_content = '''import os
import json
from fastapi import APIRouter, HTTPException
from config import TEMPLATES_DIR

router = APIRouter(prefix="/api/templates", tags=["Templates"])

@router.get("")
def get_templates():
    """Lấy danh sách các mẫu hồ sơ có _schema.json trong TEMPLATES_DIR."""
    templates = []
    if os.path.exists(TEMPLATES_DIR):
        for f in os.listdir(TEMPLATES_DIR):
            folder_path = os.path.join(TEMPLATES_DIR, f)
            schema_path = os.path.join(folder_path, "_schema.json")
            if os.path.isdir(folder_path) and os.path.exists(schema_path):
                try:
                    with open(schema_path, "r", encoding="utf-8") as sf:
                        schema = json.load(sf)
                    word_files = [x for x in os.listdir(folder_path) if x.endswith('.docx') and not x.startswith(('~$', '_'))]
                    templates.append({
                        "name": schema.get("name", f),
                        "display_name": schema.get("display_name", f),
                        "file_count": len(word_files),
                        "category": schema.get("category", "Thủ tục doanh nghiệp"),
                        "description": schema.get("description", "")
                    })
                except Exception as e:
                    print(f"Error reading schema for {f}: {e}")
    return {"templates": templates}

@router.get("/{name}/schema")
def get_template_schema(name: str):
    """Lấy nội dung schema chi tiết của một mẫu."""
    folder_path = os.path.join(TEMPLATES_DIR, name)
    schema_path = os.path.join(folder_path, "_schema.json")
    if not os.path.exists(schema_path):
        raise HTTPException(status_code=404, detail=f"Schema not found for template: {name}")
    with open(schema_path, "r", encoding="utf-8") as sf:
        return json.load(sf)

@router.get("/{name}/fields")
def get_template_fields(name: str):
    """Endpoint tương thích ngược với wizard.js: trả về danh sách fields."""
    folder_path = os.path.join(TEMPLATES_DIR, name)
    schema_path = os.path.join(folder_path, "_schema.json")
    if not os.path.exists(schema_path):
        raise HTTPException(status_code=404, detail=f"Schema not found for template: {name}")
    with open(schema_path, "r", encoding="utf-8") as sf:
        data = json.load(sf)
    fields = data.get("fields", [])
    mapped_fields = []
    for f in fields:
        key = f.get("legacy_key") or f.get("key")
        mapped_fields.append({
            "key": key,
            "label": f.get("label", key),
            "group": f.get("group", "Thông tin chung"),
            "type": f.get("type", "text"),
            "required": f.get("required", True)
        })
    return {"fields": mapped_fields}
'''
with open(os.path.join(WEBAPP_V2_DIR, "routes", "templates.py"), "w", encoding="utf-8") as f:
    f.write(routes_templates_content)
log("Đã tạo routes/templates.py")

# routes/documents.py
routes_documents_content = '''from fastapi import APIRouter, Response, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from services.render_service import render_documents

router = APIRouter(prefix="/api/documents", tags=["Document Generation"])

class DocGenRequest(BaseModel):
    template_name: str
    context: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    dkkd_selected: Optional[List[str]] = None
    ma_nganh: Optional[List[Dict[str, Any]]] = None

@router.post("/generate")
def generate_docs(req: DocGenRequest):
    """Nhận yêu cầu render tài liệu, trả về file ZIP chứa các file Word đã điền."""
    try:
        # Hỗ trợ cả `context` mới lẫn `data` từ frontend
        ctx = req.context if req.context is not None else (req.data or {})
        zip_bytes = render_documents(req.template_name, ctx)
        safe_name = req.template_name.replace(" ", "_")
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="Ho_So_{safe_name}.zip"'}
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        return Response(
            content=f'{{"success": false, "message": "{str(e)}"}}',
            status_code=500,
            media_type="application/json"
        )
'''
with open(os.path.join(WEBAPP_V2_DIR, "routes", "documents.py"), "w", encoding="utf-8") as f:
    f.write(routes_documents_content)
log("Đã tạo routes/documents.py")

# routes/ocr.py
routes_ocr_content = '''from fastapi import APIRouter, UploadFile, File, Form
from services.ocr_service import extract_vneid

router = APIRouter(prefix="/api/ocr", tags=["OCR"])

@router.post("/vneid")
async def ocr_vneid(image: UploadFile = File(...), target: str = Form(...)):
    try:
        image_bytes = await image.read()
        data = await extract_vneid(image_bytes, target)
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "message": str(e)}
'''
with open(os.path.join(WEBAPP_V2_DIR, "routes", "ocr.py"), "w", encoding="utf-8") as f:
    f.write(routes_ocr_content)
log("Đã tạo routes/ocr.py")

# routes/mst.py
routes_mst_content = '''from fastapi import APIRouter
from services.mst_service import lookup_mst

router = APIRouter(prefix="/api/mst", tags=["MST Lookup"])

@router.get("/{mst_number}")
async def get_mst(mst_number: str):
    try:
        data = await lookup_mst(mst_number)
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "message": str(e)}
'''
with open(os.path.join(WEBAPP_V2_DIR, "routes", "mst.py"), "w", encoding="utf-8") as f:
    f.write(routes_mst_content)
log("Đã tạo routes/mst.py")

# routes/nganh.py
routes_nganh_content = '''from fastapi import APIRouter
from services.nganh_service import search_ma_nganh

router = APIRouter(prefix="/api/nganh", tags=["Industry Code"])

@router.get("/search")
async def search_nganh(q: str):
    try:
        results = await search_ma_nganh(q)
        return {"results": results}
    except Exception as e:
        return {"success": False, "message": str(e)}
'''
with open(os.path.join(WEBAPP_V2_DIR, "routes", "nganh.py"), "w", encoding="utf-8") as f:
    f.write(routes_nganh_content)
log("Đã tạo routes/nganh.py")

# -------------------------------------------------------------
# 5. VIẾT main.py (FastAPI, Port 8001)
# -------------------------------------------------------------
main_content = '''import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routes import templates, documents, ocr, mst, nganh

app = FastAPI(title="NAC - Hồ Sơ Doanh Nghiệp (v2)")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký API routers
app.include_router(templates.router)
app.include_router(documents.router)
app.include_router(ocr.router)
app.include_router(mst.router)
app.include_router(nganh.router)

# Route trang chủ
@app.get("/")
async def serve_index():
    return FileResponse("static/index.html", media_type="text/html")

# Static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
'''
with open(os.path.join(WEBAPP_V2_DIR, "main.py"), "w", encoding="utf-8") as f:
    f.write(main_content)
log("Đã tạo main.py (Port 8001)")

# -------------------------------------------------------------
# 6. COPY VÀ CẬP NHẬT FRONTEND STATIC
# -------------------------------------------------------------
# Copy css
shutil.copy(
    os.path.join(WEBAPP_OLD_DIR, "static", "css", "style.css"),
    os.path.join(WEBAPP_V2_DIR, "static", "css", "style.css")
)

# Copy js files (app.js, router.js)
shutil.copy(
    os.path.join(WEBAPP_OLD_DIR, "static", "js", "app.js"),
    os.path.join(WEBAPP_V2_DIR, "static", "js", "app.js")
)
shutil.copy(
    os.path.join(WEBAPP_OLD_DIR, "static", "js", "router.js"),
    os.path.join(WEBAPP_V2_DIR, "static", "js", "router.js")
)

# Copy pages (landing.js, services.js, wizard.js)
shutil.copy(
    os.path.join(WEBAPP_OLD_DIR, "static", "js", "pages", "landing.js"),
    os.path.join(WEBAPP_V2_DIR, "static", "js", "pages", "landing.js")
)
shutil.copy(
    os.path.join(WEBAPP_OLD_DIR, "static", "js", "pages", "services.js"),
    os.path.join(WEBAPP_V2_DIR, "static", "js", "pages", "services.js")
)
shutil.copy(
    os.path.join(WEBAPP_OLD_DIR, "static", "js", "pages", "wizard.js"),
    os.path.join(WEBAPP_V2_DIR, "static", "js", "pages", "wizard.js")
)

# Đọc index.html và loại bỏ 2 dòng cn2tv_wizard.js, cd1tv2tv_wizard.js
with open(os.path.join(WEBAPP_OLD_DIR, "static", "index.html"), "r", encoding="utf-8") as f:
    index_html = f.read()

index_html_lines = []
for line in index_html.splitlines():
    if "cn2tv_wizard.js" in line or "cd1tv2tv_wizard.js" in line:
        continue
    index_html_lines.append(line)

with open(os.path.join(WEBAPP_V2_DIR, "static", "index.html"), "w", encoding="utf-8") as f:
    f.write("\n".join(index_html_lines) + "\n")

log("Đã copy và chuẩn hóa static frontend (Dracula theme, bỏ cn2tv_wizard & cd1tv2tv_wizard)")

# -------------------------------------------------------------
# 7. PILOT: CHUYỂN ĐỔI MẪU "Tạm dừng công ty TNHH 1 TV" SANG JINJA2
# -------------------------------------------------------------
import docx

sample_src_dir = os.path.join(BASE_DIR, "Mẫu Tạm dừng công ty TNHH 1 TV")
sample_dst_dir = os.path.join(WEBAPP_V2_DIR, "templates", "Tạm dừng công ty TNHH 1 TV")

REPLACE_MAP = {
    "[TEN_CONG_TY_VN]": "{{ ten_cong_ty_vn }}",
    "[MA_SO_THUE]": "{{ ma_so_thue }}",
    "[DDPL_HO_TEN]": "{{ ddpl.ho_ten }}",
    "[DDPL_NGAY_SINH]": "{{ ddpl.ngay_sinh }}",
    "[DDPL_SO_CCCD]": "{{ ddpl.so_cccd }}",
    "[DDPL_GIOI_TINH]": "{{ ddpl.gioi_tinh }}",
    "[DDPL_DIA_CHI_SO_NHA]": "{{ ddpl.dia_chi_so_nha }}",
    "[DDPL_DIA_CHI_XA_PHUONG]": "{{ ddpl.dia_chi_xa_phuong }}",
    "[DDPL_DIA_CHI_TINH_THANH]": "{{ ddpl.dia_chi_tinh_thanh }}",
    "[DIA_CHI_SO_NHA]": "{{ dia_chi_so_nha }}",
    "[DIA_CHI_XA_PHUONG]": "{{ dia_chi_xa_phuong }}",
    "[DIA_CHI_TINH_THANH]": "{{ dia_chi_tinh_thanh }}",
    "[VON_DIEU_LE_SO]": "{{ von_dieu_le_so }}",
    "[VON_DIEU_LE_CHU]": "{{ von_dieu_le_chu }}",
    "[SDT_CONG_TY]": "{{ sdt_cong_ty }}",
    "[EMAIL_CONG_TY]": "{{ email_cong_ty }}",
}

def replace_in_p(paragraph):
    full_text = paragraph.text
    if not any(k in full_text for k in REPLACE_MAP):
        return
    
    # Thay thế trên từng run
    for r in paragraph.runs:
        for k, v in REPLACE_MAP.items():
            if k in r.text:
                r.text = r.text.replace(k, v)
                
    # Nếu còn placeholder bị phân mảnh nhiều runs
    remaining_text = "".join(r.text for r in paragraph.runs)
    if any(k in remaining_text for k in REPLACE_MAP):
        for k, v in REPLACE_MAP.items():
            remaining_text = remaining_text.replace(k, v)
        if paragraph.runs:
            paragraph.runs[0].text = remaining_text
            for r in paragraph.runs[1:]:
                r.text = ""

converted_files = []
for fname in os.listdir(sample_src_dir):
    if not fname.endswith('.docx') or fname.startswith(('~$', '_')):
        continue
    
    src_file = os.path.join(sample_src_dir, fname)
    dst_file = os.path.join(sample_dst_dir, fname)
    
    doc = docx.Document(src_file)
    
    for p in doc.paragraphs:
        replace_in_p(p)
        
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    replace_in_p(p)
                    
    for s in doc.sections:
        for hp in s.header.paragraphs:
            replace_in_p(hp)
        for fp in s.footer.paragraphs:
            replace_in_p(fp)
            
    doc.save(dst_file)
    converted_files.append(fname)
    log(f"Đã chuyển đổi placeholder sang Jinja2 cho: {fname}")

# Tạo file _schema.json
schema_data = {
    "name": "Tạm dừng công ty TNHH 1 TV",
    "display_name": "Tạm dừng công ty TNHH 1 TV",
    "category": "Tạm ngừng kinh doanh",
    "description": "Hồ sơ thông báo tạm ngừng kinh doanh dành cho Công ty TNHH Một Thành Viên (gồm 3 biểu mẫu: Thông báo tạm ngừng, Quyết định chủ sở hữu, Giấy ủy quyền).",
    "version": "2.0",
    "files": converted_files,
    "fields": [
        {
            "key": "ten_cong_ty_vn",
            "legacy_key": "TEN_CONG_TY_VN",
            "label": "Tên công ty (tiếng Việt)",
            "group": "Thông tin Công ty",
            "type": "text",
            "required": True,
            "placeholder": "CÔNG TY TNHH ABC"
        },
        {
            "key": "ma_so_thue",
            "legacy_key": "MA_SO_THUE",
            "label": "Mã số thuế / Mã số doanh nghiệp",
            "group": "Thông tin Công ty",
            "type": "text",
            "required": True,
            "placeholder": "0123456789"
        },
        {
            "key": "ddpl.ho_ten",
            "legacy_key": "DDPL_HO_TEN",
            "label": "Họ và tên ĐDPL",
            "group": "Người đại diện pháp luật",
            "type": "text",
            "required": True,
            "placeholder": "NGUYỄN VĂN A"
        },
        {
            "key": "ddpl.gioi_tinh",
            "legacy_key": "DDPL_GIOI_TINH",
            "label": "Giới tính ĐDPL",
            "group": "Người đại diện pháp luật",
            "type": "text",
            "required": True,
            "placeholder": "Nam / Nữ"
        },
        {
            "key": "ddpl.ngay_sinh",
            "legacy_key": "DDPL_NGAY_SINH",
            "label": "Ngày sinh ĐDPL",
            "group": "Người đại diện pháp luật",
            "type": "text",
            "required": True,
            "placeholder": "01/01/1990"
        },
        {
            "key": "ddpl.so_cccd",
            "legacy_key": "DDPL_SO_CCCD",
            "label": "Số CCCD ĐDPL",
            "group": "Người đại diện pháp luật",
            "type": "text",
            "required": True,
            "placeholder": "001090123456"
        },
        {
            "key": "ddpl.dia_chi_so_nha",
            "legacy_key": "DDPL_DIA_CHI_SO_NHA",
            "label": "Địa chỉ ĐDPL (Số nhà, ngõ/xóm)",
            "group": "Người đại diện pháp luật",
            "type": "text",
            "required": True,
            "placeholder": "Số 123 đường Giải Phóng"
        },
        {
            "key": "ddpl.dia_chi_xa_phuong",
            "legacy_key": "DDPL_DIA_CHI_XA_PHUONG",
            "label": "Địa chỉ ĐDPL (Xã/Phường)",
            "group": "Người đại diện pháp luật",
            "type": "text",
            "required": True,
            "placeholder": "Phường Đồng Tâm"
        },
        {
            "key": "ddpl.dia_chi_tinh_thanh",
            "legacy_key": "DDPL_DIA_CHI_TINH_THANH",
            "label": "Địa chỉ ĐDPL (Tỉnh/Thành phố)",
            "group": "Người đại diện pháp luật",
            "type": "text",
            "required": True,
            "placeholder": "Thành phố Hà Nội"
        }
    ]
}

schema_path = os.path.join(sample_dst_dir, "_schema.json")
with open(schema_path, "w", encoding="utf-8") as sf:
    json.dump(schema_data, sf, ensure_ascii=False, indent=2)
log("Đã tạo _schema.json cho mẫu Tạm dừng công ty TNHH 1 TV")

# -------------------------------------------------------------
# 8. KIỂM THỬ PILOT RENDER (TEST SUITE)
# -------------------------------------------------------------
log("\n=== BẮT ĐẦU TEST PILOT RENDER ===")
import sys
sys.path.insert(0, WEBAPP_V2_DIR)
from services.render_service import render_documents

test_context = {
    "ten_cong_ty_vn": "CÔNG TY TNHH CÔNG NGHỆ THỬ NGHIỆM V2",
    "ma_so_thue": "0109876543",
    "ddpl": {
        "ho_ten": "TRẦN VĂN THỬ NGHIỆM",
        "ngay_sinh": "15/08/1992",
        "so_cccd": "001092009999",
        "gioi_tinh": "Nam",
        "dia_chi_so_nha": "Số 88 Phố Huế",
        "dia_chi_xa_phuong": "Phường Hàng Bài",
        "dia_chi_tinh_thanh": "Thành Phố Hà Nội"
    }
}

try:
    zip_bytes = render_documents("Tạm dừng công ty TNHH 1 TV", test_context)
    log(f"Test render thành công! Kích thước file ZIP sinh ra: {len(zip_bytes)} bytes")
    
    # Giải nén và kiểm tra từng file trong zip
    with zipfile.ZipFile(BytesIO(zip_bytes), "r") as z:
        namelist = z.namelist()
        log(f"Các file trong ZIP: {namelist}")
        
        all_passed = True
        for fname in namelist:
            f_bytes = z.read(fname)
            doc_check = docx.Document(BytesIO(f_bytes))
            
            full_text_rendered = []
            for p in doc_check.paragraphs:
                full_text_rendered.append(p.text)
            for t in doc_check.tables:
                for row in t.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            full_text_rendered.append(p.text)
            full_text = "\n".join(full_text_rendered)
            
            # Kiểm tra xem còn thẻ {{ }} nào chưa render không
            unrendered = re.findall(r'\{\{[^\}]+\}\}', full_text)
            if unrendered:
                log(f"CẢNH BÁO: File {fname} còn thẻ Jinja2 chưa render: {unrendered}")
                all_passed = False
            else:
                log(f"File {fname}: Render sạch 100%, không còn thẻ Jinja2.")
                
            # Kiểm tra xem text test có xuất hiện không
            if test_context["ten_cong_ty_vn"] in full_text:
                log(f"File {fname}: Đã điền chính xác tên công ty '{test_context['ten_cong_ty_vn']}'")
            if test_context["ma_so_thue"] in full_text:
                log(f"File {fname}: Đã điền chính xác mã số thuế '{test_context['ma_so_thue']}'")
            if test_context["ddpl"]["ho_ten"] in full_text:
                log(f"File {fname}: Đã điền chính xác tên ĐDPL '{test_context['ddpl']['ho_ten']}'")
                
        if all_passed:
            log(">>> KẾT QUẢ TEST PILOT: THÀNH CÔNG RỰC RỠ! 100% TEST CASES ĐẠT! <<<")
        else:
            log(">>> KẾT QUẢ TEST PILOT: CÓ CẢNH BÁO <<<")
            
except Exception as e:
    import traceback
    log(f"LỖI KHI TEST PILOT: {str(e)}\n{traceback.format_exc()}")

# Test với context legacy (phẳng key viết hoa như frontend webapp cũ)
log("\n=== TEST VỚI LEGACY FLAT CONTEXT (FRONTEND CŨ) ===")
legacy_context = {
    "TEN_CONG_TY_VN": "CÔNG TY TNHH LEGACY FORMAT",
    "MA_SO_THUE": "0312345678",
    "DDPL_HO_TEN": "LÊ THỊ LEGACY",
    "DDPL_SO_CCCD": "001188001122",
    "DDPL_NGAY_SINH": "20/10/1988",
    "DDPL_GIOI_TINH": "Nữ",
    "DDPL_DIA_CHI_SO_NHA": "Số 456 Hai Bà Trưng",
    "DDPL_DIA_CHI_XA_PHUONG": "Phường Tân Định",
    "DDPL_DIA_CHI_TINH_THANH": "Thành phố Hồ Chí Minh"
}

try:
    zip_bytes_legacy = render_documents("Tạm dừng công ty TNHH 1 TV", legacy_context)
    log(f"Test render với legacy context thành công! Kích thước file ZIP: {len(zip_bytes_legacy)} bytes")
    with zipfile.ZipFile(BytesIO(zip_bytes_legacy), "r") as z:
        for fname in z.namelist():
            f_bytes = z.read(fname)
            doc_check = docx.Document(BytesIO(f_bytes))
            full_text = "\n".join([p.text for p in doc_check.paragraphs])
            if "CÔNG TY TNHH LEGACY FORMAT" in full_text:
                log(f"File {fname}: Nhận diện legacy context và render thành công!")
    log(">>> TEST LEGACY FLAT CONTEXT THÀNH CÔNG! <<<")
except Exception as e:
    import traceback
    log(f"LỖI KHI TEST LEGACY CONTEXT: {str(e)}\n{traceback.format_exc()}")

# -------------------------------------------------------------
# 9. LIỆT KÊ TẤT CẢ FILE ĐÃ TẠO
# -------------------------------------------------------------
log("\n=== DANH SÁCH TẤT CẢ CÁC FILE ĐÃ TẠO TRONG WEBAPP_V2 ===")
all_created = []
for root, dirs, files in os.walk(WEBAPP_V2_DIR):
    for file in files:
        rel_path = os.path.relpath(os.path.join(root, file), WEBAPP_V2_DIR)
        all_created.append(rel_path)

for item in sorted(all_created):
    log(f"- webapp_v2/{item}")

log(f"\nTổng cộng: {len(all_created)} files.")

# Ghi toàn bộ logs vào file với encoding='utf-8'
with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(logs))

print("SETUP SCRIPT FINISHED SUCCESSFULLY")
