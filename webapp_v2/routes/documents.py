import re
import unicodedata
from urllib.parse import quote
from fastapi import APIRouter, Response, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from services.render_service import render_documents

router = APIRouter(prefix="/api/documents", tags=["Document Generation"])

class NganhInfo(BaseModel):
    ma: str
    ten: str
    is_main: Optional[bool] = False

class DocGenRequest(BaseModel):
    template_name: str
    data: Dict[str, Any]
    ma_nganh: Optional[List[NganhInfo]] = []
    special_payload: Optional[Dict[str, Any]] = None

def make_ascii_filename(s: str) -> str:
    normalized = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    safe = re.sub(r'[^a-zA-Z0-9_]+', '_', normalized).strip('_')
    return safe or "Ho_So"

@router.post("/generate")
def generate_docs(req: DocGenRequest):
    try:
        ma_nganh_dicts = [n.model_dump() for n in req.ma_nganh] if req.ma_nganh else []
        zip_bytes = render_documents(
            template_name=req.template_name,
            raw_data=req.data,
            ma_nganh_list=ma_nganh_dicts,
            special_payload=req.special_payload
        )

        ascii_name = make_ascii_filename(req.template_name)
        utf8_encoded = quote(f"Ho_So_{req.template_name}.zip")
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="Ho_So_{ascii_name}.zip"; filename*=UTF-8\'\'{utf8_encoded}'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

