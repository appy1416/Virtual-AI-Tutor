import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    # UUID Primary Key support for both SQLite and PostgreSQL
    id = Column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(50), default="student", nullable=False) # e.g. student, admin
    
    profile_picture_url = Column(String(512), nullable=True)
    bio = Column(String(500), nullable=True)
    preferences = Column(JSON, default=dict, nullable=False)
    
    # Gamification and streaks
    points = Column(Integer, default=0, nullable=False)
    badges = Column(JSON, default=list, nullable=False)
    streak_days = Column(Integer, default=0, nullable=False)
    last_activity_date = Column(DateTime(timezone=True), nullable=True)
    
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

    # Indexes
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_role", "role"),
        Index("idx_user_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<User email={self.email} role={self.role}>"
