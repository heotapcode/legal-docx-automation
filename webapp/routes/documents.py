from fastapi import APIRouter, Response
from pydantic import BaseModel
from services.word_service import generate_documents
from services.cn2tv_service import generate_cn2tv_documents
from services.cd1tv2tv_service import generate_cd1tv2tv_documents
from typing import Dict, List, Optional, Any

router = APIRouter(prefix="/api/documents", tags=["Document Generation"])

class NganhInfo(BaseModel):
    ma: str
    ten: str
    is_main: Optional[bool] = False

class DocGenRequest(BaseModel):
    template_name: str
    data: Dict[str, str]
    ma_nganh: Optional[List[NganhInfo]] = []
    dkkd_selected: Optional[List[str]] = None
    cn2tv_data: Optional[Dict[str, Any]] = None
    cd1tv2tv_data: Optional[Dict[str, Any]] = None

@router.post("/generate")
def generate_docs(req: DocGenRequest):
    try:
        if req.template_name == "Chuyển nhượng Công ty TNHH 2 TV" and req.cn2tv_data:
            zip_bytes = generate_cn2tv_documents(req.cn2tv_data)
        elif req.template_name == "Chuyển đổi loại hình 1TV sang 2 TV" and req.cd1tv2tv_data:
            zip_bytes = generate_cd1tv2tv_documents(req.cd1tv2tv_data, req.data)
        else:
            ma_nganh_dicts = [n.model_dump() for n in req.ma_nganh] if req.ma_nganh else []
            zip_bytes = generate_documents(req.template_name, req.data, ma_nganh_dicts, req.dkkd_selected)
            
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=\"Ho_So.zip\""}
        )
    except Exception as e:
        return {"success": False, "message": str(e)}
