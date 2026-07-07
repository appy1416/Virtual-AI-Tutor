from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class NoteCreateRequest(BaseModel):
    lesson_id: str
    content: str

class NoteUpdateRequest(BaseModel):
    content: Optional[str] = None
    tags: Optional[List[str]] = None

class NoteResponse(BaseModel):
    id: str
    lesson_id: str
    content_preview: str
    word_count: int
    tags: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True

class NoteDetailResponse(BaseModel):
    id: str
    lesson_id: str
    content: str
    ai_summary: Optional[str]
    word_count: int
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
