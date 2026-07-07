from app.core.database import Base

class LearningTwin(Base):
    __tablename__ = "learning_twins"

    def __init__(self, **kwargs):
        kwargs.setdefault("learning_style", "mixed")
        kwargs.setdefault("knowledge_gaps", [])
        kwargs.setdefault("next_review_items", [])
        kwargs.setdefault("recommended_courses", [])
        kwargs.setdefault("career_goals", [])
        kwargs.setdefault("learning_pace", "normal")
        kwargs.setdefault("preferred_study_times", {})
        kwargs.setdefault("preferred_study_duration_minutes", 45)
        kwargs.setdefault("strengths", [])
        kwargs.setdefault("weaknesses", [])
        super().__init__(**kwargs)
