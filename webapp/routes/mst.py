from fastapi import APIRouter
from services.mst_service import lookup_mst

router = APIRouter(prefix="/api/mst", tags=["MST Lookup"])

@router.get("/{mst_number}")
async def get_mst(mst_number: str):
    try:
        data = await lookup_mst(mst_number)
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "message": str(e)}
