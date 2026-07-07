from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

from app.modules.learning_twin import crud as twin_crud
from app.modules.learning_twin.profiler import initialize_learning_twin, update_learning_gaps_from_quizzes
from app.db.models.learning_twin import LearningTwin

async def get_twin_profile(db: AsyncSession, student_id: str) -> LearningTwin:
    twin = await twin_crud.get_learning_twin(db, student_id)
    if not twin:
        twin = await initialize_learning_twin(db, student_id)
    return twin

async def update_twin_profile(db: AsyncSession, student_id: str, **fields) -> Optional[LearningTwin]:
    # Ensure profile exists
    await get_twin_profile(db, student_id)
    return await twin_crud.update_learning_twin(db, student_id, **fields)

async def detect_knowledge_gaps(db: AsyncSession, student_id: str) -> List[Dict[str, Any]]:
    await update_learning_gaps_from_quizzes(student_id, db)
    twin = await get_twin_profile(db, student_id)
    return twin.knowledge_gaps or []

async def generate_learning_roadmap(db: AsyncSession, student_id: str) -> List[Dict[str, Any]]:
    twin = await get_twin_profile(db, student_id)
    gaps = twin.knowledge_gaps or []
    
    roadmap = []
    for gap in gaps:
        roadmap.append({
            "stage": f"Review {gap['topic']}",
            "recommended_action": f"Since your score was {gap['confidence_level']}%, review basic lessons first.",
            "estimated_days": 2
        })
    if not roadmap:
        roadmap.append({
            "stage": "General Mastery Path",
            "recommended_action": "Complete basic enrolled courses first.",
            "estimated_days": 7
        })
    return roadmap

async def get_next_items_to_review(db: AsyncSession, student_id: str) -> List[Dict[str, Any]]:
    # Mock spaced repetition scheduler
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    return [
        {"item_id": "review-1", "review_date": tomorrow, "difficulty": "hard", "topic": "Calculus Foundations"},
        {"item_id": "review-2", "review_date": tomorrow, "difficulty": "medium", "topic": "Mechanics Intro"}
    ]
