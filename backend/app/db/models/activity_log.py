from app.core.database import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
