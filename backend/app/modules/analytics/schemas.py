from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class WeeklyActivityItem(BaseModel):
    day: str
    hours: float
    quizzes: int

class DashboardResponse(BaseModel):
    total_courses: int
    courses_in_progress: int
    courses_completed: int
    total_study_hours: float
    average_quiz_score: float
    current_streak: int
    weekly_activity: List[WeeklyActivityItem] = []
    top_strengths: List[str] = []
    improvement_areas: List[str] = []

class ProgressResponse(BaseModel):
    lessons_completed: int
    lessons_total: int
    progress_percentage: float
    current_focus_area: Optional[str] = None
    estimated_completion_date: Optional[str] = None

class QuizPerformanceResponse(BaseModel):
    quiz_id: str
    title: str
    score: int
    accuracy: float
    attempts: int
    average_time: float
    feedback_summary: Optional[str] = None

class AdminPopularCourseItem(BaseModel):
    course_id: str
    title: str
    enrolled_count: int

class AdminUserGrowthItem(BaseModel):
    date: str
    new_signups: int

class AdminAnalyticsResponse(BaseModel):
    total_students: int
    daily_active_users: int
    average_session_duration: float
    quiz_completion_rate: float
    retention_7day: float
    retention_30day: float
    popular_courses: List[AdminPopularCourseItem] = []
    user_growth_chart: List[AdminUserGrowthItem] = []
