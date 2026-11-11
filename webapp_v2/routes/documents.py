import logging
import re
import unicodedata
from urllib.parse import quote
import json

from fastapi import APIRouter, Depends, Response, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from services.render_service import render_documents, validate_template_dir
from services import schema_engine
from services.rate_limit import limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["Document Generation"])

class NganhInfo(BaseModel):
    ma: str
    ten: str
    is_main: Optional[bool] = False

class DocGenRequest(BaseModel):
    template_name: str
    data: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    ma_nganh: Optional[List[NganhInfo]] = []
    special_payload: Optional[Dict[str, Any]] = None

def validate_request_data(template_name: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Lỗi dữ liệu theo _schema.json của bộ mẫu (trống nếu hợp lệ)."""
    schema_path = validate_template_dir(template_name) / "_schema.json"
    if not schema_path.exists():
        return []
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return schema_engine.validate(schema, data)


def make_ascii_filename(s: str) -> str:
    normalized = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    safe = re.sub(r'[^a-zA-Z0-9_]+', '_', normalized).strip('_')
    return safe or "Ho_So"

@router.post("/generate", dependencies=[Depends(limit("generate"))])
def generate_docs(req: DocGenRequest):
    try:
        raw_data = req.data if req.data is not None else (req.context if req.context is not None else {})
        errors = validate_request_data(req.template_name, raw_data)
        if errors:
            shown = "; ".join(e["message"] for e in errors[:8])
            more = f" (và {len(errors) - 8} lỗi khác)" if len(errors) > 8 else ""
            return JSONResponse(status_code=422, content={
                "detail": f"Dữ liệu chưa hợp lệ: {shown}{more}",
                "errors": errors,
            })
        ma_nganh_dicts = [n.model_dump() for n in req.ma_nganh] if req.ma_nganh else []
        zip_bytes = render_documents(
            template_name=req.template_name,
            raw_data=raw_data,
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
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        # Lỗi hệ thống: ghi log kèm tên bộ mẫu, không trả chi tiết kỹ thuật ra trình duyệt
        logger.exception("Lỗi khi sinh hồ sơ '%s'", req.template_name)
        raise HTTPException(status_code=500, detail="Không tạo được hồ sơ do lỗi hệ thống. Vui lòng thử lại; "
                                                    "nếu vẫn lỗi, báo quản trị viên kèm thời điểm xảy ra.")

