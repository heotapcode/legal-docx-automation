from fastapi import APIRouter
from pydantic import BaseModel
import os
import json
from config import DATA_DIR

router = APIRouter(prefix="/api/services", tags=["Service Inquiry"])

class InquiryRequest(BaseModel):
    name: str
    phone: str
    email: str
    service_type: str
    company_name: str
    message: str

@router.post("/inquiry")
def post_inquiry(req: InquiryRequest):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        file_path = DATA_DIR / "inquiries.json"
        inquiries = []
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                inquiries = json.load(f)
        inquiries.append(req.model_dump())
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(inquiries, f, ensure_ascii=False, indent=4)
        return {"success": True, "message": "Yêu cầu đã được gửi thành công!"}
    except Exception as e:
        return {"success": False, "message": str(e)}
