import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class VoiceSession(Base):
    __tablename__ = "voice_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tutor_type = Column(String(50), default="ai_voice", nullable=False)  # ai_voice, live_tutor
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    audio_url = Column(String(512), nullable=True)
    transcription = Column(String(10000), nullable=True)
    ai_response_audio = Column(String(512), nullable=True)
    duration_seconds = Column(Integer, default=0, nullable=False)
    audio_quality = Column(String(50), default="medium", nullable=False)  # low, medium, high
    
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("User")
    lesson = relationship("Lesson")
