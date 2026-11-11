"""API cấu hình dùng chung cho quản trị viên. Cần đăng nhập; thay đổi dữ liệu cần header X-Requested-With: nac-admin."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from services import uy_quyen
from services.auth import require_admin

router = APIRouter(prefix="/api/admin/settings", tags=["admin"])


@router.get("/nguoi-nhan-uy-quyen")
def get_nguoi_nhan_uy_quyen(user: dict = Depends(require_admin)):
    return {"value": uy_quyen.get(), "default": uy_quyen.defaults()}


@router.put("/nguoi-nhan-uy-quyen")
def put_nguoi_nhan_uy_quyen(body: Dict[str, Any], user: dict = Depends(require_admin)):
    try:
        return {"value": uy_quyen.save(body, user.get("id"))}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
