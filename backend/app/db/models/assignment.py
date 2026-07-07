from app.core.database import Base

class Assignment(Base):
    __tablename__ = "assignments"

    def __init__(self, **kwargs):
        kwargs.setdefault("file_url", None)
        kwargs.setdefault("is_published", True)
        super().__init__(**kwargs)


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    def __init__(self, **kwargs):
        kwargs.setdefault("submission_text", None)
        kwargs.setdefault("file_name", None)
        kwargs.setdefault("file_url", None)
        kwargs.setdefault("marks", None)
        kwargs.setdefault("feedback", None)
        kwargs.setdefault("graded_at", None)
        super().__init__(**kwargs)
