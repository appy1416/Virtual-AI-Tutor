from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.activity_log import ActivityLog
from app.db.models.notification import Notification

async def log_activity(db: AsyncSession, user_id: str, action_type: str, description: str) -> None:
    """
    Saves an audit activity event log into the database.
    """
    log = ActivityLog(user_id=user_id, action_type=action_type, description=description)
    db.add(log)
    await db.flush()

async def create_notification(db: AsyncSession, user_id: str | None, title: str, content: str, notification_type: str) -> None:
    """
    Dispatches a student notification or global platform announcement.
    """
    notification = Notification(
        user_id=user_id,
        title=title,
        content=content,
        notification_type=notification_type
    )
    db.add(notification)
    await db.flush()
