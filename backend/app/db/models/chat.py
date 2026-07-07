from app.core.database import Base

class ChatHistory(Base):
    __tablename__ = "chat_histories"

    def __init__(self, **kwargs):
        kwargs.setdefault("lesson_id", None)
        kwargs.setdefault("course_id", None)
        kwargs.setdefault("messages", [])
        kwargs.setdefault("ai_model", "openai")
        kwargs.setdefault("started_at", None)
        kwargs.setdefault("ended_at", None)
        kwargs.setdefault("message_count", 0)
        super().__init__(**kwargs)
