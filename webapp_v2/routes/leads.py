"""Phễu khách: cấu hình công khai (Zalo, bảng giá, câu đồng ý) và trang quản trị Khách tiềm năng."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from services import kinh_doanh, leads
from services.auth import require_admin

public = APIRouter(prefix="/api/public", tags=["public"])
admin = APIRouter(prefix="/api/admin", tags=["admin"])


@public.get("/kinh-doanh")
def get_public_kinh_doanh():
    return kinh_doanh.public_view()


@admin.get("/leads")
def list_leads(user: dict = Depends(require_admin)):
    return {"leads": leads.list_leads(), "statuses": leads.STATUSES, "roles": leads.ROLES,
            "packages": {g["ma"]: g["ten"] for g in kinh_doanh.get()["goi"]}}


@admin.patch("/leads/{lead_id}")
def patch_lead(lead_id: int, body: Dict[str, Any], user: dict = Depends(require_admin)):
    try:
        return {"lead": leads.update(lead_id, body, user.get("id"))}
    except KeyError:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@admin.delete("/leads/{lead_id}")
def delete_lead(lead_id: int, user: dict = Depends(require_admin)):
    try:
        leads.delete(lead_id, user.get("id"))
    except KeyError:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách")
    return {"ok": True}


@admin.get("/settings/kinh-doanh")
def get_kinh_doanh(user: dict = Depends(require_admin)):
    return {"value": kinh_doanh.get(), "default": kinh_doanh.defaults()}


@admin.put("/settings/kinh-doanh")
def put_kinh_doanh(body: Dict[str, Any], user: dict = Depends(require_admin)):
    try:
        return {"value": kinh_doanh.save(body, user.get("id"))}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
