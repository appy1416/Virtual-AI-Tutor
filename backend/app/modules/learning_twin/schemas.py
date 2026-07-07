from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class KnowledgeGapItem(BaseModel):
    topic: str
    confidence_level: int

class ReviewItem(BaseModel):
    item_id: str
    review_date: str
    difficulty: str

class RecommendedCourseItem(BaseModel):
    course_id: str
    title: str
    reason: str

class CareerGoalItem(BaseModel):
    goal: str
    target_date: str

class LearningTwinResponse(BaseModel):
    student_id: str
    learning_style: str
    learning_pace: str
    knowledge_gaps: List[KnowledgeGapItem] = []
    next_review_items: List[ReviewItem] = []
    recommended_courses: List[RecommendedCourseItem] = []
    career_goals: List[CareerGoalItem] = []
    strengths: List[str] = []
    weaknesses: List[str] = []

    class Config:
        from_attributes = True

class LearningTwinUpdateRequest(BaseModel):
    learning_style: Optional[str] = None
    learning_pace: Optional[str] = None
    career_goals: Optional[List[CareerGoalItem]] = None
    preferred_study_times: Optional[Dict[str, List[str]]] = None
    preferred_study_duration_minutes: Optional[int] = None
