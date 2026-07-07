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
    
    data = []
    for n in docs:
        notif_obj = Notification(**n)
        res_data = NotificationResponse.model_validate(notif_obj)
        # Populate is_read dynamically based on read_by list or is_read attribute
        res_data.is_read = n.get("is_read") is True or current_user.id in (n.get("read_by") or [])
        data.append(res_data)
        
    return send_response(status_code=status.HTTP_200_OK, success=True, data=data)

@router.get("/notifications/unread-count")
async def get_unread_notification_count(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Returns total unread count for current user (targeted unread and unread global notifs).
    """
    query = {
        "$or": [
            {"user_id": current_user.id},
            {"user_id": None}
        ]
    }
    cursor = db.db["notifications"].find(query)
    docs = await cursor.to_list(length=1000)
    
    unread_count = 0
    for n in docs:
        is_read = n.get("is_read") is True or current_user.id in (n.get("read_by") or [])
        if not is_read:
            unread_count += 1
            
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data={"unread_count": unread_count}
    )

@router.post("/notifications/read-all")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Marks all notifications (targeted and global ones) as read.
    """
    # For targeted notifications, update is_read = True
    await db.db["notifications"].update_many(
        {"user_id": current_user.id, "is_read": False},
        {"$set": {"is_read": True}}
    )
    # For global notifications, add current_user.id to read_by list
    await db.db["notifications"].update_many(
        {"user_id": None, "read_by": {"$ne": current_user.id}},
        {"$addToSet": {"read_by": current_user.id}}
    )
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        message="All notifications marked as read."
    )

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
        
    if notification.get("user_id") is None:
        # global notification
        await db.db["notifications"].update_one(
            {"id": notificationId},
            {"$addToSet": {"read_by": current_user.id}}
        )
    else:
        # targeted notification
        await db.db["notifications"].update_one(
            {"id": notificationId},
            {"$set": {"is_read": True}}
        )
    return send_response(status_code=status.HTTP_200_OK, success=True, message="Notification marked as read.")
