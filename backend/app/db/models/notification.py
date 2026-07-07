from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    def __init__(self, **kwargs):
        kwargs.setdefault("user_id", None)
        kwargs.setdefault("is_read", False)
        super().__init__(**kwargs)
