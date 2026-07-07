from datetime import datetime, timezone
import uuid
from typing import Optional, List, Dict, Any
from app.db.models.learning_twin import LearningTwin

async def create_learning_twin(db, student_id: str) -> LearningTwin:
    twin = await get_learning_twin(db, student_id)
    if twin:
        return twin
        
    now = datetime.now(timezone.utc)
    twin_doc = {
        "id": str(uuid.uuid4()),
        "student_id": student_id,
        "learning_style": "mixed",
        "knowledge_gaps": [],
        "next_review_items": [],
        "recommended_courses": [],
        "career_goals": [],
        "learning_pace": "normal",
        "preferred_study_times": {},
        "preferred_study_duration_minutes": 45,
        "strengths": [],
        "weaknesses": [],
        "created_at": now,
        "updated_at": now
    }
    try:
        await db.db["learning_twins"].insert_one(twin_doc)
        return LearningTwin(**twin_doc)
    except Exception:
        # Fetch if duplicate key / race condition occurred
        twin = await get_learning_twin(db, student_id)
        if not twin:
            raise
        return twin

async def get_learning_twin(db, student_id: str) -> Optional[LearningTwin]:
    doc = await db.db["learning_twins"].find_one({"student_id": student_id})
    return LearningTwin(**doc) if doc else None

async def update_learning_twin(db, student_id: str, **fields) -> Optional[LearningTwin]:
    twin = await get_learning_twin(db, student_id)
    if not twin:
        return None
    fields["updated_at"] = datetime.now(timezone.utc)
    await db.db["learning_twins"].update_one({"student_id": student_id}, {"$set": fields})
    updated = await db.db["learning_twins"].find_one({"student_id": student_id})
    return LearningTwin(**updated) if updated else None

async def update_knowledge_gaps(db, student_id: str, gaps: List[Dict[str, Any]]) -> Optional[LearningTwin]:
    return await update_learning_twin(db, student_id, knowledge_gaps=gaps)

async def update_next_review_items(db, student_id: str, items: List[Dict[str, Any]]) -> Optional[LearningTwin]:
    return await update_learning_twin(db, student_id, next_review_items=items)
