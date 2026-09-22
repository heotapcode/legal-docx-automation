from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.ocr_service import extract_vneid

router = APIRouter(prefix="/api/ocr", tags=["OCR"])

@router.post("/vneid")
async def ocr_vneid(
    image: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
    target: str = Form("ddpl")
):
    try:
        upload = image or file
        if not upload:
            raise HTTPException(status_code=400, detail="Vui lòng tải lên tệp ảnh (image hoặc file)")
        image_bytes = await upload.read()
        data = await extract_vneid(image_bytes, target)
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "message": str(e)}
