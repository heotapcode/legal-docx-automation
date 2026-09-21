import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import HOST, PORT, BASE_DIR
from routes import templates, documents, ocr, mst, nganh, services

app = FastAPI(title="NAC v2 - Hệ thống Soạn thảo Hồ sơ Doanh nghiệp (Jinja2 / docxtpl)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(templates.router)
app.include_router(documents.router)
app.include_router(ocr.router)
app.include_router(mst.router)
app.include_router(nganh.router)
app.include_router(services.router)

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
