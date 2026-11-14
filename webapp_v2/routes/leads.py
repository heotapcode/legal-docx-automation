"""Phễu khách: cấu hình công khai (Zalo, bảng giá, câu đồng ý) và trang quản trị Khách tiềm năng."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from services import doi_tac, kinh_doanh, leads
from services.auth import require_admin
from services.rate_limit import limit

public = APIRouter(prefix="/api/public", tags=["public"])
admin = APIRouter(prefix="/api/admin", tags=["admin"])


@public.get("/kinh-doanh")
def get_public_kinh_doanh(template_id: str = ""):
    return kinh_doanh.public_view(template_id)


@public.get("/thanh-toan/{pay_code}", dependencies=[Depends(limit("inquiry"))])
def get_payment(pay_code: str, phone: str):
    """Thông tin đặt cọc + mã QR cho khách nhờ nộp. Cần đúng mã hồ sơ và số Zalo đã để lại."""
    info = leads.payment_info(pay_code, phone)
    if not info:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ")
    return info


@admin.get("/leads")
def list_leads(user: dict = Depends(require_admin)):
    return {"leads": leads.list_leads(), "statuses": leads.STATUSES, "roles": leads.ROLES,
            "packages": {g["ma"]: g["ten"] for g in kinh_doanh.get()["goi"]}, "delivery": leads.DELIVERY,
            "partners": doi_tac.names()}


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
    from services import vietqr
    return {"value": kinh_doanh.get(), "default": kinh_doanh.defaults(), "banks": vietqr.BANKS}


@admin.put("/settings/kinh-doanh")
def put_kinh_doanh(body: Dict[str, Any], user: dict = Depends(require_admin)):
    try:
        return {"value": kinh_doanh.save(body, user.get("id"))}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- Đối tác giới thiệu ----------

@admin.get("/partners")
def list_partners(user: dict = Depends(require_admin)):
    return doi_tac.report()


@admin.post("/partners")
def create_partner(body: Dict[str, Any], user: dict = Depends(require_admin)):
    try:
        return {"partner": doi_tac.create(body, user.get("id"))}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@admin.patch("/partners/{partner_id}")
def patch_partner(partner_id: int, body: Dict[str, Any], user: dict = Depends(require_admin)):
    try:
        return {"partner": doi_tac.update(partner_id, body, user.get("id"))}
    except KeyError:
        raise HTTPException(status_code=404, detail="Không tìm thấy đối tác")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
