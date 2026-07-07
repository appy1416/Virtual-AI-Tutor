from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

class AssignmentCreate(BaseModel):
    title: str
    description: str
    deadline: datetime
    file_url: Optional[str] = None
    is_published: Optional[bool] = True

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    file_url: Optional[str] = None
    is_published: Optional[bool] = None

class AssignmentResponse(BaseModel):
    id: str
    title: str
    description: str
    deadline: datetime
    file_url: Optional[str] = None
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SubmissionCreate(BaseModel):
    submission_text: Optional[str] = None
    file_name: Optional[str] = None
    file_url: Optional[str] = None

class SubmissionResponse(BaseModel):
    id: str
    assignment_id: str
    student_id: str
    submission_text: Optional[str] = None
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    submitted_at: datetime
    marks: Optional[int] = None
    feedback: Optional[str] = None
    graded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class SubmissionGradeRequest(BaseModel):
    marks: int
    feedback: str
