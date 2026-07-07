from fastapi import APIRouter, Depends, status, Query
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.db.models.user import User
from app.modules.recommendations import service as rec_service
from app.modules.recommendations.schemas import RecommendationResponse
from app.utils.response import send_response

router = APIRouter(tags=["Recommendations"])

@router.get("/recommendations")
async def list_personalized_recommendations(
    limit: int = Query(10, ge=1, le=50),
    skip: int = Query(0, ge=0),
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    recs, total = await rec_service.get_recommendations(db, current_user.id, limit, skip)
    items = [RecommendationResponse.model_validate(r) for r in recs]
    
    data = {
        "items": items,
        "total_count": total
    }
    return send_response(status_code=status.HTTP_200_OK, success=True, data=data)

@router.post("/recommendations/{recId}/feedback")
async def register_recommendation_click_feedback(
    recId: str,
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    updated = await rec_service.mark_recommendation_clicked(db, recId)
    if not updated:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Recommendation not found.")
        
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=RecommendationResponse.model_validate(updated),
        message="Recommendation feedback registered."
    )
