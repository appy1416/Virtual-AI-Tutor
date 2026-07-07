from app.core.database import Base

class Lesson(Base):
    __tablename__ = "lessons"

    def __init__(self, **kwargs):
        kwargs.setdefault("learning_objectives", [])
        kwargs.setdefault("estimated_duration_minutes", 30)
        kwargs.setdefault("difficulty_score", 5)
        kwargs.setdefault("deleted_at", None)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Lesson title={getattr(self, 'title', None)} sequence={getattr(self, 'sequence_order', None)}>"


class LessonCompletion(Base):
    __tablename__ = "lesson_completions"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<LessonCompletion user={getattr(self, 'user_id', None)} lesson={getattr(self, 'lesson_id', None)}>"
