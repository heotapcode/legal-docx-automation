from fastapi import APIRouter
from services.nganh_service import search_ma_nganh, get_all_combos

router = APIRouter(prefix="/api/nganh", tags=["Industry Code"])

@router.get("/combos")
async def get_combos():
    try:
        combos = get_all_combos()
        return {"combos": combos}
    except Exception as e:
        return {"combos": [], "success": False, "message": str(e)}

@router.get("/search")
async def search_nganh(q: str):
    try:
        results = await search_ma_nganh(q)
        return {"results": results}
    except Exception as e:
        return {"success": False, "message": str(e)}
