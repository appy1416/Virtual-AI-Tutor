from fastapi import APIRouter, Depends, status
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.db.models.user import User
from app.db.models.notification import Notification
from app.modules.notifications.schemas import NotificationResponse
from app.utils.response import send_response

router = APIRouter(tags=["Notifications"])

@router.get("/notifications")
async def list_user_notifications(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Lists unread notifications targeted at the current student or general broadcast.
    """
    # Fetch notifications specifically for the user, or global ones (user_id is None)
    query = {
        "$or": [
            {"user_id": current_user.id},
            {"user_id": None}
        ]
    }
    cursor = db.db["notifications"].find(query).sort("created_at", -1)
    docs = await cursor.to_list(length=100)
    
    data = [NotificationResponse.model_validate(Notification(**n)) for n in docs]
    return send_response(status_code=status.HTTP_200_OK, success=True, data=data)

@router.post("/notifications/{notificationId}/read")
async def mark_notification_as_read(
    notificationId: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Flags a notification alert as read.
    """
    notification = await db.db["notifications"].find_one({"id": notificationId})
    if not notification:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Notification not found.")
        
    await db.db["notifications"].update_one(
        {"id": notificationId},
        {"$set": {"is_read": True}}
    )
    return send_response(status_code=status.HTTP_200_OK, success=True, message="Notification marked as read.")
