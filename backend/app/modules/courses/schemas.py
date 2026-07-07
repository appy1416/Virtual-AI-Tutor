from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.modules.lessons.schemas import LessonResponse

class CourseCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., min_length=5, max_length=1000)
    category: str = Field(..., min_length=2, max_length=100)
    level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    thumbnail_url: Optional[str] = None
    max_students: Optional[int] = None

class CourseUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, min_length=5, max_length=1000)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    thumbnail_url: Optional[str] = None
    max_students: Optional[int] = None
    is_published: Optional[bool] = None

class CourseResponse(BaseModel):
    id: str
    tutor_id: str
    title: str
    description: str
    category: str
    level: str
    thumbnail_url: Optional[str]
    max_students: Optional[int]
    is_published: bool
    created_at: datetime
    lesson_count: Optional[int] = 0

    class Config:
        from_attributes = True

class CourseDetailResponse(CourseResponse):
    lessons: List[LessonResponse] = []

    class Config:
        from_attributes = True

class PaginatedCourseResponse(BaseModel):
    items: List[CourseResponse]
    total_count: int
    page_count: int
    current_page: int

class UserEnrollmentProgressResponse(BaseModel):
    id: str
    title: str
    lessons_completed: int
    lessons_total: int
    progress_percentage: int
    enrolled_at: datetime

class InstructorDashboardResponse(BaseModel):
    total_students: int
    total_enrollments: int
    avg_rating: float
