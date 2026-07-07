from fastapi import APIRouter, Depends, status
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.db.models.user import User
from app.modules.learning_twin import service as twin_service
from app.modules.learning_twin.schemas import LearningTwinResponse, LearningTwinUpdateRequest
from app.utils.response import send_response

router = APIRouter(tags=["Learning Twin"])

@router.get("/learning-twin")
async def get_student_twin_profile(
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    profile = await twin_service.get_twin_profile(db, current_user.id)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=LearningTwinResponse.model_validate(profile))

@router.put("/learning-twin")
async def update_student_twin_profile(
    body: LearningTwinUpdateRequest,
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    update_data = body.model_dump(exclude_unset=True)
    if "career_goals" in update_data and update_data["career_goals"] is not None:
        update_data["career_goals"] = [goal.model_dump() for goal in update_data["career_goals"]]
        
    updated = await twin_service.update_twin_profile(db, current_user.id, **update_data)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=LearningTwinResponse.model_validate(updated))

@router.get("/learning-twin/insights")
async def get_student_learning_insights(
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    data = {
        "insights": [
            "Your visual recall of diagrams is excellent.",
            "Schedule calculus reviews in the morning when your focus is highest."
        ]
    }
    return send_response(status_code=status.HTTP_200_OK, success=True, data=data)

@router.get("/learning-twin/roadmap")
async def get_personalized_learning_roadmap(
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    roadmap = await twin_service.generate_learning_roadmap(db, current_user.id)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=roadmap)

@router.get("/learning-twin/knowledge-gaps")
async def get_student_knowledge_gaps(
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    gaps = await twin_service.detect_knowledge_gaps(db, current_user.id)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=gaps)

@router.get("/learning-twin/next-review")
async def get_spaced_repetition_schedule(
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    schedule = await twin_service.get_next_items_to_review(db, current_user.id)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=schedule)
