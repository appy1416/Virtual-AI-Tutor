from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatSessionStartRequest(BaseModel):
    lesson_id: Optional[str] = None
    course_id: Optional[str] = None

class ChatMessageRequest(BaseModel):
    message: str

class ChatMessageResponse(BaseModel):
    role: str  # user, assistant
    content: str
    timestamp: str

class ChatSessionResponse(BaseModel):
    id: str
    student_id: str
    lesson_id: Optional[str]
    course_id: Optional[str]
    ai_model: str
    started_at: datetime
    ended_at: Optional[datetime]
    message_count: int

    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    id: str
    messages: List[ChatMessageResponse] = []
    started_at: datetime
    ended_at: Optional[datetime]
    message_count: int

    class Config:
        from_attributes = True
