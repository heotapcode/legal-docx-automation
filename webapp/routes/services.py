from fastapi import APIRouter
from pydantic import BaseModel
import os
import json

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
        file_path = "data/inquiries.json"
        os.makedirs("data", exist_ok=True)
        inquiries = []
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                inquiries = json.load(f)
        inquiries.append(req.model_dump())
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(inquiries, f, ensure_ascii=False, indent=4)
        return {"success": True, "message": "Inquiry submitted successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}
