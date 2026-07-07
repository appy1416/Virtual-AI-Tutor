import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class LearningTwin(Base):
    __tablename__ = "learning_twins"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    learning_style = Column(String(50), default="mixed", nullable=False)  # visual, auditory, kinesthetic, mixed
    knowledge_gaps = Column(JSON, default=list, nullable=False)  # [{"topic": str, "confidence_level": int}]
    next_review_items = Column(JSON, default=list, nullable=False)  # [{"item_id": str, "review_date": str, "difficulty": str}]
    recommended_courses = Column(JSON, default=list, nullable=False)  # [{"course_id": str, "reason": str}]
    career_goals = Column(JSON, default=list, nullable=False)  # [{"goal": str, "target_date": str}]
    learning_pace = Column(String(50), default="normal", nullable=False)  # slow, normal, fast
    preferred_study_times = Column(JSON, default=dict, nullable=False)  # {"monday": [...]}
    preferred_study_duration_minutes = Column(Integer, default=45, nullable=False)
    strengths = Column(JSON, default=list, nullable=False)
    weaknesses = Column(JSON, default=list, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("User")
