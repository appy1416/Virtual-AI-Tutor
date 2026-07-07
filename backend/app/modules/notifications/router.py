from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
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
    db: AsyncSession = Depends(get_db)
):
    """
    Lists unread notifications targeted at the current student or general broadcast.
    """
    # Fetch notifications specifically for the user, or global ones (user_id is None)
    stmt = select(Notification).where(
        or_(
            Notification.user_id == current_user.id,
            Notification.user_id == None
        )
    ).order_by(Notification.created_at.desc())
    
    res = await db.execute(stmt)
    notifications = res.scalars().all()
    
    data = [NotificationResponse.model_validate(n) for n in notifications]
    return send_response(status_code=status.HTTP_200_OK, success=True, data=data)

@router.post("/notifications/{notificationId}/read")
async def mark_notification_as_read(
    notificationId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Flags a notification alert as read.
    """
    stmt = select(Notification).where(Notification.id == notificationId)
    res = await db.execute(stmt)
    notification = res.scalars().first()
    if not notification:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Notification not found.")
        
    notification.is_read = True
    db.add(notification)
    await db.commit()
    return send_response(status_code=status.HTTP_200_OK, success=True, message="Notification marked as read.")
