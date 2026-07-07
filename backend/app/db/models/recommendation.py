from app.core.database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    def __init__(self, **kwargs):
        kwargs.setdefault("target_title", "Untitled")
        kwargs.setdefault("relevance_score", 50)
        kwargs.setdefault("clicked", False)
        super().__init__(**kwargs)
