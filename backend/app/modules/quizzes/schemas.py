from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class QuizOption(BaseModel):
    option_text: str
    is_correct: bool

class QuizCreateRequest(BaseModel):
    lesson_id: str
    question_text: str
    quiz_type: str = Field("mcq", description="mcq, short_answer, essay")
    options: List[QuizOption] = []
    correct_answer: Optional[str] = None
    difficulty_level: int = Field(5, ge=1, le=10)
    max_attempts: int = Field(3, ge=1)
    time_limit_seconds: Optional[int] = None
    passing_score: Optional[int] = 70
    explanation: Optional[str] = None
    is_published: Optional[bool] = True
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None

class QuizUpdateRequest(BaseModel):
    question_text: Optional[str] = None
    quiz_type: Optional[str] = None
    options: Optional[List[QuizOption]] = None
    correct_answer: Optional[str] = None
    difficulty_level: Optional[int] = None
    max_attempts: Optional[int] = None
    time_limit_seconds: Optional[int] = None
    passing_score: Optional[int] = None
    explanation: Optional[str] = None
    is_published: Optional[bool] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None

class QuizResponse(BaseModel):
    id: str
    lesson_id: str
    question_text: str
    quiz_type: str
    options: List[Any] = []  # Options returned to student should omit 'is_correct' for security!
    difficulty_level: int
    max_attempts: int
    time_limit_seconds: Optional[int]
    passing_score: int
    is_published: bool
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None

    class Config:
        from_attributes = True

class QuizResponseWithAnswers(QuizResponse):
    options: List[QuizOption] = []  # Includes correct answers
    correct_answer: Optional[str]
    explanation: Optional[str] = None

class QuizSubmissionRequest(BaseModel):
    user_answer: str
    confidence_level: Optional[int] = Field(None, ge=1, le=5)
    time_spent_seconds: int = Field(..., ge=0)

class QuizSubmissionResponse(BaseModel):
    submission_id: str
    is_correct: Optional[bool]
    score: int
    feedback: str
    correct_answer: Optional[str] = None  # only revealed if incorrect and allowed
    explanation: Optional[str] = None
    points_awarded: int = 0
    grading_in_progress: bool = False
