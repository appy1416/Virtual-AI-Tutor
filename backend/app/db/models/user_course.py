from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, PrimaryKeyConstraint
from app.core.database import Base

class UserCourse(Base):
    __tablename__ = "user_courses"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    
    enrolled_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint("user_id", "course_id"),
    )
