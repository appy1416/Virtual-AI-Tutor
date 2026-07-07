from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VoiceSessionRequest(BaseModel):
    lesson_id: Optional[str] = None
    tutor_type: str = "ai_voice"  # ai_voice, live_tutor

class VoiceSessionResponse(BaseModel):
    id: str
    tutor_type: str
    lesson_id: Optional[str]
    duration_seconds: int
    transcription: Optional[str]
    started_at: datetime

    class Config:
        from_attributes = True

class VoiceSessionDetailResponse(BaseModel):
    id: str
    tutor_type: str
    lesson_id: Optional[str]
    audio_url: Optional[str]
    transcription: Optional[str]
    ai_response_audio: Optional[str]
    duration_seconds: int
    audio_quality: str
    started_at: datetime
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True
