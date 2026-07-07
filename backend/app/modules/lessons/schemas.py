from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class LessonCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., min_length=5, max_length=500)
    content: str = Field(..., min_length=10) # large markdown
    learning_objectives: List[str] = Field(default_factory=list)
    estimated_duration_minutes: int = Field(30, ge=1, le=1440)
    difficulty_score: int = Field(5, ge=1, le=10)

class LessonUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, min_length=5, max_length=500)
    content: Optional[str] = Field(None, min_length=10)
    learning_objectives: Optional[List[str]] = None
    estimated_duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    difficulty_score: Optional[int] = Field(None, ge=1, le=10)

class LessonResponse(BaseModel):
    id: str
    course_id: str
    sequence_order: int
    title: str
    description: str
    learning_objectives: List[str] = []
    estimated_duration_minutes: int
    difficulty_score: int
    created_at: datetime

    class Config:
        from_attributes = True

class LessonDetailResponse(LessonResponse):
    content: str

    class Config:
        from_attributes = True

class LessonReorderRequest(BaseModel):
    lesson_order_list: List[str] # List of Lesson UUIDs in the desired order
