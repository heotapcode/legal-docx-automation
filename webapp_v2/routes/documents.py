import logging
import re
import unicodedata
from urllib.parse import quote
import json

from fastapi import APIRouter, BackgroundTasks, Depends, Response, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from services.render_service import render_documents, validate_template_dir
from services import schema_engine
from services.rate_limit import limit
from services import leads
import config

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
    # Khách để lại thông tin trước khi tải (services/leads.py): name, phone, role, delegated, consent, source
    lead: Optional[Dict[str, Any]] = None

def load_schema(template_name: str) -> Dict[str, Any]:
    schema_path = validate_template_dir(template_name) / "_schema.json"
    if not schema_path.exists():
        return {}
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_request_data(template_name: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Lỗi dữ liệu theo _schema.json của bộ mẫu (trống nếu hợp lệ)."""
    schema = load_schema(template_name)
    return schema_engine.validate(schema, data) if schema else []


def make_ascii_filename(s: str) -> str:
    normalized = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    safe = re.sub(r'[^a-zA-Z0-9_]+', '_', normalized).strip('_')
    return safe or "Ho_So"

@router.post("/generate", dependencies=[Depends(limit("generate"))])
def generate_docs(req: DocGenRequest, background: BackgroundTasks):
    try:
        raw_data = req.data if req.data is not None else (req.context if req.context is not None else {})
        lead = None
        if req.lead is not None or config.LEAD_REQUIRED:
            try:
                lead = leads.parse_lead(req.lead)
            except ValueError as e:
                return JSONResponse(status_code=422, content={"detail": str(e), "lead_error": True})
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

        if lead is not None:
            schema = load_schema(req.template_name)
            rec = leads.build(lead, schema.get("id", ""), schema.get("display_name") or req.template_name, raw_data)
            try:
                leads.record(rec)
            except Exception:  # không lưu được khách vẫn cho tải hồ sơ
                logger.exception("Không lưu được thông tin khách")
            zip_bytes = leads.add_cover(zip_bytes, rec)
            background.add_task(leads.notify, rec)

        ascii_name = make_ascii_filename(req.template_name)
        utf8_encoded = quote(f"Ho_So_{req.template_name}.zip")
        headers = {
            "Content-Disposition": f'attachment; filename="Ho_So_{ascii_name}.zip"; filename*=UTF-8\'\'{utf8_encoded}'
        }
        if lead is not None:
            headers["X-Lead-Package"] = rec["package"]  # gói nên chào / khách chọn: màn hình sau khi tải đưa lên đầu
            if rec.get("pay_code"):
                headers["X-Lead-Code"] = rec["pay_code"]  # mã hồ sơ: lấy mã QR đặt cọc
        return Response(content=zip_bytes, media_type="application/zip", headers=headers)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        # Lỗi hệ thống: ghi log kèm tên bộ mẫu, không trả chi tiết kỹ thuật ra trình duyệt
        logger.exception("Lỗi khi sinh hồ sơ '%s'", req.template_name)
        raise HTTPException(status_code=500, detail="Không tạo được hồ sơ do lỗi hệ thống. Vui lòng thử lại; "
                                                    "nếu vẫn lỗi, báo quản trị viên kèm thời điểm xảy ra.")

