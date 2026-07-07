from fastapi import APIRouter, Depends, status, Query
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

from app.core.database import get_db
from app.core.security import RoleChecker
from app.db.models.user import User
from app.db.models.activity_log import ActivityLog
from app.utils.response import send_response

router = APIRouter(tags=["Activity Logs"])

class ActivityLogResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_email: str
    action_type: str
    description: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

@router.get("/admin/activity-logs")
async def list_all_activity_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(RoleChecker(["admin"])),
    db = Depends(get_db)
):
    """
    Lists audit logs of user activities across the platform (Admin only).
    """
    cursor = db.db["activity_logs"].find().sort("timestamp", -1).skip(skip).limit(limit)
    logs_docs = await cursor.to_list(length=limit)
    logs = [ActivityLog(**l) for l in logs_docs]
    
    # Resolve student details
    enriched = []
    for l in logs:
        student_doc = await db.db["users"].find_one({"id": l.user_id})
        
        enriched.append({
            "id": l.id,
            "user_id": l.user_id,
            "user_name": student_doc.get("full_name") if student_doc else "Unknown",
            "user_email": student_doc.get("email") if student_doc else "",
            "action_type": l.action_type,
            "description": l.description,
            "timestamp": l.timestamp
        })
        
    return send_response(status_code=status.HTTP_200_OK, success=True, data=enriched)
