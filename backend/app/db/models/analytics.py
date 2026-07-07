from app.core.database import Base

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    def __init__(self, **kwargs):
        kwargs.setdefault("metadata_json", {})
        super().__init__(**kwargs)


class StudentPerformance(Base):
    __tablename__ = "student_performances"

    def __init__(self, **kwargs):
        kwargs.setdefault("score", 0)
        kwargs.setdefault("accuracy", 0)
        kwargs.setdefault("time_spent_seconds", 0)
        kwargs.setdefault("completion_status", "completed")
        kwargs.setdefault("mastery_level", 0)
        kwargs.setdefault("completed_at", None)
        super().__init__(**kwargs)
