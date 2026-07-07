from app.core.database import Base

class Course(Base):
    __tablename__ = "courses"

    def __init__(self, **kwargs):
        kwargs.setdefault("thumbnail_url", None)
        kwargs.setdefault("max_students", None)
        kwargs.setdefault("is_published", False)
        kwargs.setdefault("deleted_at", None)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Course title={getattr(self, 'title', None)} level={getattr(self, 'level', None)}>"
