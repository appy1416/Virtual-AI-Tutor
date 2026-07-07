from app.core.database import Base

class UserCourse(Base):
    __tablename__ = "user_courses"

    def __init__(self, **kwargs):
        kwargs.setdefault("completed_at", None)
        super().__init__(**kwargs)
