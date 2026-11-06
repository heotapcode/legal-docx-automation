from fastapi import APIRouter

from services.dia_ban import default_tinh, list_tinh_thanh

router = APIRouter(prefix="/api/dia-ban", tags=["Địa bàn"])


@router.get("/tinh-thanh")
def get_tinh_thanh():
    return {"mac_dinh": default_tinh(), "tinh_thanh": list_tinh_thanh()}
