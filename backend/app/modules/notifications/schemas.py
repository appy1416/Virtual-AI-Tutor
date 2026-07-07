from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class NotificationResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    title: str
    content: str
    notification_type: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
