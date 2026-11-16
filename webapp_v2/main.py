import os
import re
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import logging

from config import HOST, PORT, BASE_DIR, CORS_ORIGINS, LOG_LEVEL

logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO),
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
from routes import templates, documents, ocr, mst, nganh, services, dia_ban, admin_auth, admin_templates, admin_settings, leads as leads_routes

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
app.include_router(leads_routes.public)
app.include_router(leads_routes.admin)

# Mount static files
static_dir = BASE_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

_ASSET_RE = re.compile(r'(src|href)="(/static/[^"?]+)(?:\?[^"]*)?"')


def _stamp(m):
    f = static_dir / m.group(2)[len("/static/"):]
    version = int(f.stat().st_mtime) if f.is_file() else 0
    return f'{m.group(1)}="{m.group(2)}?v={version}"'


def render_index() -> str:
    """index.html với mỗi file JS/CSS nội bộ gắn ?v=<thời điểm sửa file>.

    Sửa file nào thì địa chỉ file đó đổi, trình duyệt buộc tải bản mới: người dùng không bị kẹt bản JS cũ
    trong bộ nhớ đệm sau khi cập nhật máy chủ (không cần tự tăng số phiên bản trong index.html).
    """
    html = (static_dir / "index.html").read_text(encoding="utf-8")
    from services import kinh_doanh, trang_chu
    ga = trang_chu.tracking(kinh_doanh.get(), spa=True)
    if ga:
        html = html.replace("</head>", ga + "\n</head>", 1)

    return _ASSET_RE.sub(_stamp, html)


# Trang giới thiệu dựng sẵn ở máy chủ (Google đọc được); ứng dụng tạo hồ sơ / quản trị ở /app
@app.get("/")
def serve_landing(request: Request):
    from services import trang_chu
    html = _ASSET_RE.sub(_stamp, trang_chu.render(str(request.base_url)))
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


# Trang đích cho quảng cáo theo nhóm từ khóa (services/trang_chu.PAGES)
@app.get("/thanh-lap-cong-ty")
def serve_landing_thanh_lap(request: Request):
    from services import trang_chu
    html = _ASSET_RE.sub(_stamp, trang_chu.render(str(request.base_url), "thanh-lap-cong-ty"))
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


@app.get("/thay-doi-dang-ky-kinh-doanh")
def serve_landing_thay_doi(request: Request):
    from services import trang_chu
    html = _ASSET_RE.sub(_stamp, trang_chu.render(str(request.base_url), "thay-doi-dang-ky-kinh-doanh"))
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


# Ứng dụng (không lưu đệm trang khung; các file tĩnh có ?v= riêng)
@app.get("/app")
async def serve_index():
    return HTMLResponse(render_index(), headers={"Cache-Control": "no-cache"})


@app.get("/robots.txt")
def robots(request: Request):
    from services import trang_chu
    return PlainTextResponse(trang_chu.robots(str(request.base_url)))


@app.get("/sitemap.xml")
def sitemap(request: Request):
    from services import trang_chu
    return Response(trang_chu.sitemap(str(request.base_url)), media_type="application/xml")

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
