from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware

from routes import templates, documents, ocr, mst, nganh, services

app = FastAPI(title='NAC - Hồ Sơ Doanh Nghiệp')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers FIRST
app.include_router(templates.router)
app.include_router(documents.router)
app.include_router(ocr.router)
app.include_router(mst.router)
app.include_router(nganh.router)
app.include_router(services.router)

# Serve index.html for root
@app.get('/')
async def serve_index():
    return FileResponse('static/index.html', media_type='text/html')

# Mount static files AFTER API routes but handles /static/* paths
os.makedirs('static', exist_ok=True)
app.mount('/static', StaticFiles(directory='static'), name='static')

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
