import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import logging

from config import HOST, PORT, BASE_DIR, CORS_ORIGINS, LOG_LEVEL

logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO),
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
from routes import templates, documents, ocr, mst, nganh, services, dia_ban, admin_auth, admin_templates, admin_settings

app = FastAPI(title="NAC v2 - Hệ thống Soạn thảo Hồ sơ Doanh nghiệp (Jinja2 / docxtpl)")

# Không bao giờ kết hợp origin "*" với allow_credentials=True:
# khi đó mọi website đều gọi được API thay mặt người dùng.
_allow_all = "*" in CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all else CORS_ORIGINS,
    allow_credentials=not _allow_all,
    allow_methods=["GET", "POST", "OPTIONS"],  # PUT/DELETE chỉ dùng cho API quản trị, cùng origin
    allow_headers=["Content-Type"],
)

# Báo ngay khi khởi động nếu phần đọc CCCD thiếu thành phần (kiểm tra chi tiết: python -m tools.setup_ocr --check)
def _log_ocr_status() -> None:
    from services import ocr_service
    st = ocr_service.status()
    if not st["qr_ready"] or not st["ocr_ready"]:
        logging.getLogger("ocr").warning(
            "Đọc CCCD chưa đầy đủ (đọc QR: %s, đọc chữ: %s). Chạy: python -m tools.setup_ocr --check",
            "sẵn sàng" if st["qr_ready"] else "THIẾU", "sẵn sàng" if st["ocr_ready"] else "THIẾU")


_log_ocr_status()

# Include API routers
app.include_router(templates.router)
app.include_router(documents.router)
app.include_router(ocr.router)
app.include_router(mst.router)
app.include_router(nganh.router)
app.include_router(services.router)
app.include_router(dia_ban.router)
app.include_router(admin_auth.router)
app.include_router(admin_templates.router)
app.include_router(admin_settings.router)

# Mount static files
static_dir = BASE_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Serve index.html
@app.get("/")
async def serve_index():
    index_path = static_dir / "index.html"
    return FileResponse(str(index_path), media_type="text/html")

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
