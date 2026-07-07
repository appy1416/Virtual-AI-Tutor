import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class LMSNote(Base):
    __tablename__ = "lms_notes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    description = Column(String(2000), nullable=False)
    subject = Column(String(100), nullable=False) # e.g. Mathematics, Science, etc.
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False) # pdf, docx, ppt
    uploaded_by = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    uploader = relationship("User")
