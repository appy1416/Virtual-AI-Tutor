from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    def __init__(self, **kwargs):
        kwargs.setdefault("role", "student")
        kwargs.setdefault("profile_picture_url", None)
        kwargs.setdefault("bio", None)
        kwargs.setdefault("preferences", {})
        kwargs.setdefault("points", 0)
        kwargs.setdefault("badges", [])
        kwargs.setdefault("streak_days", 0)
        kwargs.setdefault("last_activity_date", None)
        kwargs.setdefault("deleted_at", None)
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<User email={getattr(self, 'email', None)} role={getattr(self, 'role', None)}>"
