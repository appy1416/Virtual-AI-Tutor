from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.db.models.user import User
from app.modules.analytics import service as analytics_service
from app.modules.analytics import crud as analytics_crud
from app.modules.analytics.schemas import DashboardResponse, ProgressResponse
from app.utils.response import send_response

router = APIRouter(tags=["Analytics"])

@router.get("/analytics/dashboard")
async def get_student_dashboard_metrics(
    current_user: User = Depends(RoleChecker(["student"])),
    db: AsyncSession = Depends(get_db)
):
    dashboard = await analytics_service.get_dashboard(db, current_user.id)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=dashboard)

@router.get("/analytics/progress")
async def get_student_learning_progress(
    courseId: str,
    current_user: User = Depends(RoleChecker(["student"])),
    db: AsyncSession = Depends(get_db)
):
    progress = await analytics_service.get_progress(db, current_user.id, courseId)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=progress)

@router.get("/analytics/performance")
async def get_student_quiz_performance_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(RoleChecker(["student"])),
    db: AsyncSession = Depends(get_db)
):
    records, total = analytics_crud.get_student_performance(db, current_user.id, skip, limit)
    # Since it is a coroutine:
    records, total = await analytics_crud.get_student_performance(db, current_user.id, skip, limit)
    
    # Format list
    items = []
    for r in records:
        items.append({
            "id": r.id,
            "lesson_id": r.lesson_id,
            "quiz_id": r.quiz_id,
            "score": r.score,
            "accuracy": r.accuracy,
            "time_spent_seconds": r.time_spent_seconds,
            "mastery_level": r.mastery_level,
            "completed_at": r.completed_at
        })
        
    data = {
        "items": items,
        "total_count": total
    }
    return send_response(status_code=status.HTTP_200_OK, success=True, data=data)

@router.get("/analytics/export")
async def export_student_data_csv(
    current_user: User = Depends(RoleChecker(["student"])),
    db: AsyncSession = Depends(get_db)
):
    csv_data = await analytics_service.export_learning_data(db, current_user.id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=learning_data_{current_user.id}.csv"}
    )
