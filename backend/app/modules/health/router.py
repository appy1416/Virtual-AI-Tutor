from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("")
@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
