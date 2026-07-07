import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    tutor_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=False)
    category = Column(String(100), nullable=False) # e.g. STEM, Humanity
    level = Column(String(50), nullable=False)      # beginner, intermediate, advanced
    
    thumbnail_url = Column(String(512), nullable=True)
    max_students = Column(Integer, nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)
    
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
    tutor = relationship("User", foreign_keys=[tutor_id])
    lessons = relationship(
        "Lesson", 
        back_populates="course", 
        cascade="all, delete-orphan",
        order_by="Lesson.sequence_order"
    )

    __table_args__ = (
        Index("idx_course_tutor_published", "tutor_id", "is_published"),
        Index("idx_course_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<Course title={self.title} level={self.level}>"
