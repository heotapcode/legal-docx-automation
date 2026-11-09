import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.ocr_service import extract_vneid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ocr", tags=["OCR"])

@router.post("/vneid")
async def ocr_vneid(
    image: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
    target: str = Form("ddpl")
):
    upload = image or file
    if not upload:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên tệp ảnh (image hoặc file)")
    try:
        image_bytes = await upload.read()
        data = await extract_vneid(image_bytes, target)
        return {"success": True, "data": data}
    except ValueError as e:
        # Lỗi do ảnh/dữ liệu đầu vào: thông báo đã viết sẵn cho người dùng
        return {"success": False, "message": str(e)}
    except Exception:
        # Lỗi hệ thống: ghi log, không trả chi tiết kỹ thuật ra trình duyệt
        logger.exception("Lỗi khi đọc ảnh CCCD/VNeID")
        return {"success": False, "message": "Không đọc được ảnh do lỗi hệ thống. Vui lòng thử lại hoặc nhập tay."}
