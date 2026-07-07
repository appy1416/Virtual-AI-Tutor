import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(String(5000), nullable=False)
    quiz_type = Column(String(50), default="mcq", nullable=False)  # mcq, short_answer, essay
    options = Column(JSON, default=list, nullable=False)  # For MCQ: [{"option_text": "...", "is_correct": bool}]
    correct_answer = Column(String(1000), nullable=True)  # For short_answer
    difficulty_level = Column(Integer, default=5, nullable=False)  # 1-10
    max_attempts = Column(Integer, default=3, nullable=False)
    time_limit_seconds = Column(Integer, nullable=True)
    
    # LMS extensions
    passing_score = Column(Integer, default=70, nullable=False)
    explanation = Column(String(5000), nullable=True)
    is_published = Column(Boolean, default=True, nullable=False)
    available_from = Column(DateTime(timezone=True), nullable=True)
    available_until = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    lesson = relationship("Lesson", back_populates="quizzes")
    answers = relationship("QuizAnswer", back_populates="quiz", cascade="all, delete-orphan")


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_answer = Column(String(5000), nullable=False)
    is_correct = Column(Boolean, nullable=True)
    confidence_level = Column(Integer, nullable=True)  # 1-5
    time_spent_seconds = Column(Integer, default=0, nullable=False)
    feedback = Column(String(5000), nullable=True)
    points_awarded = Column(Integer, default=0, nullable=False)
    attempted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    quiz = relationship("Quiz", back_populates="answers")
    student = relationship("User")
