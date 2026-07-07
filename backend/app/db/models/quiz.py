from app.core.database import Base

class Quiz(Base):
    __tablename__ = "quizzes"

    def __init__(self, **kwargs):
        kwargs.setdefault("quiz_type", "mcq")
        kwargs.setdefault("options", [])
        kwargs.setdefault("correct_answer", None)
        kwargs.setdefault("difficulty_level", 5)
        kwargs.setdefault("max_attempts", 3)
        kwargs.setdefault("time_limit_seconds", None)
        kwargs.setdefault("passing_score", 70)
        kwargs.setdefault("explanation", None)
        kwargs.setdefault("is_published", True)
        kwargs.setdefault("available_from", None)
        kwargs.setdefault("available_until", None)
        kwargs.setdefault("deleted_at", None)
        super().__init__(**kwargs)


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    def __init__(self, **kwargs):
        kwargs.setdefault("is_correct", None)
        kwargs.setdefault("confidence_level", None)
        kwargs.setdefault("time_spent_seconds", 0)
        kwargs.setdefault("feedback", None)
        kwargs.setdefault("points_awarded", 0)
        super().__init__(**kwargs)
