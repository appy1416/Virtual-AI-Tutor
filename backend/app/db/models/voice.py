from app.core.database import Base

class VoiceSession(Base):
    __tablename__ = "voice_sessions"

    def __init__(self, **kwargs):
        kwargs.setdefault("tutor_type", "ai_voice")
        kwargs.setdefault("lesson_id", None)
        kwargs.setdefault("audio_url", None)
        kwargs.setdefault("transcription", None)
        kwargs.setdefault("ai_response_audio", None)
        kwargs.setdefault("duration_seconds", 0)
        kwargs.setdefault("audio_quality", "medium")
        kwargs.setdefault("ended_at", None)
        super().__init__(**kwargs)
