import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)  # page_view, quiz_attempt, lesson_complete, note_created, chat_message
    metadata_json = Column(JSON, default=dict, nullable=False, name="metadata")  # rename in table to avoid keyword conflict in postgres

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("User")


class StudentPerformance(Base):
    __tablename__ = "student_performances"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=False)  # 0-100
    accuracy = Column(Integer, nullable=False)  # 0-100
    time_spent_seconds = Column(Integer, default=0, nullable=False)
    completion_status = Column(String(50), default="completed", nullable=False)  # not_started, in_progress, completed
    mastery_level = Column(Integer, default=0, nullable=False)  # 0-100
    completed_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("User")
    lesson = relationship("Lesson")
    quiz = relationship("Quiz")
