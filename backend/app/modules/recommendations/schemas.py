from pydantic import BaseModel
from typing import Optional

class RecommendationResponse(BaseModel):
    id: str
    recommendation_type: str  # course, lesson, quiz, article
    target_id: str
    target_title: str
    reason: str
    relevance_score: int
    clicked: bool

    class Config:
        from_attributes = True
