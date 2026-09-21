from fastapi import APIRouter, UploadFile, File, Form
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
