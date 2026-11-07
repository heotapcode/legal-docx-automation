"""API quản lý bộ mẫu cho quản trị viên (Mục 10.2, 10.4, 10.5). Mọi API cần đăng nhập (services/auth.py);
API thay đổi dữ liệu cần thêm header X-Requested-With: nac-admin."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services import template_store as store
from services.auth import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


class PublishRequest(BaseModel):
    note: str
    legal_basis: str = ""
    effective_from: str = ""


class RollbackRequest(BaseModel):
    version: int
    note: str = ""


def _call(fn, *args, **kwargs):
    """Đổi lỗi của template_store thành mã HTTP."""
    try:
        return fn(*args, **kwargs)
    except store.PublishBlocked as e:
        return JSONResponse(status_code=422, content={"detail": str(e), "errors": e.findings})
    except store.NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except store.Conflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    except store.StoreError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates")
def list_templates(user: dict = Depends(require_admin)):
    return {"templates": store.list_templates()}


@router.get("/templates/{template_id}/versions")
def list_versions(template_id: str, user: dict = Depends(require_admin)):
    return {"versions": _call(store.list_versions, template_id)}


@router.post("/templates/{template_id}/rollback")
def rollback(template_id: str, body: RollbackRequest, user: dict = Depends(require_admin)):
    result = _call(store.rollback, template_id, body.version, user, body.note)
    return result if isinstance(result, Response) else {"version": result}


@router.get("/templates/{template_id}/drafts")
def list_drafts(template_id: str, user: dict = Depends(require_admin)):
    return {"drafts": store.list_drafts(template_id)}


@router.post("/templates/{template_id}/drafts")
def create_draft(template_id: str, user: dict = Depends(require_admin)):
    return _call(store.create_draft, template_id, user)


@router.get("/drafts/{draft_id}")
def get_draft(draft_id: str, user: dict = Depends(require_admin)):
    return _call(store.get_draft, draft_id)


@router.delete("/drafts/{draft_id}")
def discard_draft(draft_id: str, user: dict = Depends(require_admin)):
    _call(store.discard_draft, draft_id, user)
    return {"ok": True}


@router.post("/drafts/{draft_id}/files")
async def upload_file(draft_id: str, file: UploadFile = File(...), user: dict = Depends(require_admin)):
    data = await file.read(store.MAX_DOCX_BYTES + 1)  # đọc tối đa giới hạn + 1 byte: không nạp file quá lớn vào RAM
    return _call(store.put_docx, draft_id, file.filename, data, user)


@router.delete("/drafts/{draft_id}/files/{filename}")
def delete_file(draft_id: str, filename: str, user: dict = Depends(require_admin)):
    return _call(store.delete_docx, draft_id, filename, user)


@router.put("/drafts/{draft_id}/schema")
def put_schema(draft_id: str, schema: Dict[str, Any], user: dict = Depends(require_admin)):
    return _call(store.put_schema, draft_id, schema, user)


@router.get("/drafts/{draft_id}/lint")
def lint_draft(draft_id: str, user: dict = Depends(require_admin)):
    return _call(store.lint_draft, draft_id)


@router.post("/drafts/{draft_id}/preview")
def preview_draft(draft_id: str, user: dict = Depends(require_admin)):
    result = _call(store.preview_draft, draft_id)
    if isinstance(result, Response):
        return result
    return Response(content=result, media_type="application/zip",
                    headers={"Content-Disposition": 'attachment; filename="ban_nhap_sinh_thu.zip"'})


@router.post("/drafts/{draft_id}/publish")
def publish(draft_id: str, body: PublishRequest, user: dict = Depends(require_admin)):
    result = _call(store.publish_draft, draft_id, user, body.note, body.legal_basis, body.effective_from)
    return result if isinstance(result, Response) else {"version": result}
