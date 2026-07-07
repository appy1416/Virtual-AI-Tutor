from app.core.database import Base

class Note(Base):
    __tablename__ = "notes"

    def __init__(self, **kwargs):
        kwargs.setdefault("ai_summary", None)
        kwargs.setdefault("word_count", 0)
        kwargs.setdefault("tags", [])
        kwargs.setdefault("deleted_at", None)
        super().__init__(**kwargs)
