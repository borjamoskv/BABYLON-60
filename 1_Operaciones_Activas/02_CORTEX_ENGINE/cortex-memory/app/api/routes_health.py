# C5-REAL EXERGY CERTIFIED
from fastapi import APIRouter
router = APIRouter()
@router.get("/")
def health():
    return {"status": "ok"}
