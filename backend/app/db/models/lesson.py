import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    sequence_order = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=False)
    content = Column(String(10000), nullable=False) # Large markdown content
    learning_objectives = Column(JSON, default=list, nullable=False) # JSON array of strings
    
    estimated_duration_minutes = Column(Integer, default=30, nullable=False)
    difficulty_score = Column(Integer, default=5, nullable=False) # scale 1-10
    
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    course = relationship("Course", back_populates="lessons")
    quizzes = relationship("Quiz", back_populates="lesson", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("course_id", "sequence_order", name="uq_course_lesson_sequence"),
        Index("idx_lesson_course", "course_id"),
        Index("idx_lesson_sequence", "sequence_order"),
        Index("idx_lesson_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<Lesson title={self.title} sequence={self.sequence_order}>"

class LessonCompletion(Base):
    __tablename__ = "lesson_completions"

    id = Column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    
    completed_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_completion"),
        Index("idx_completion_user_lesson", "user_id", "lesson_id"),
    )

    def __repr__(self) -> str:
        return f"<LessonCompletion user={self.user_id} lesson={self.lesson_id}>"
