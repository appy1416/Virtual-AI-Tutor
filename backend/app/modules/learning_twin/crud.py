from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Dict, Any

from app.db.models.learning_twin import LearningTwin

async def create_learning_twin(db: AsyncSession, student_id: str) -> LearningTwin:
    # Double check if twin already exists
    twin = await get_learning_twin(db, student_id)
    if twin:
        return twin
        
    twin = LearningTwin(
        student_id=student_id,
        learning_style="mixed",
        learning_pace="normal",
        knowledge_gaps=[],
        next_review_items=[],
        recommended_courses=[],
        career_goals=[],
        strengths=[],
        weaknesses=[]
    )
    try:
        async with db.begin_nested():
            db.add(twin)
            await db.flush()
    except Exception:
        db.expunge(twin)
        twin = await get_learning_twin(db, student_id)
        if not twin:
            raise
    return twin

async def get_learning_twin(db: AsyncSession, student_id: str) -> Optional[LearningTwin]:
    stmt = select(LearningTwin).where(LearningTwin.student_id == student_id)
    res = await db.execute(stmt)
    return res.scalars().first()

async def update_learning_twin(db: AsyncSession, student_id: str, **fields) -> Optional[LearningTwin]:
    twin = await get_learning_twin(db, student_id)
    if not twin:
        return None
    for k, v in fields.items():
        if hasattr(twin, k):
            setattr(twin, k, v)
    db.add(twin)
    await db.flush()
    return twin

async def update_knowledge_gaps(db: AsyncSession, student_id: str, gaps: List[Dict[str, Any]]) -> Optional[LearningTwin]:
    twin = await get_learning_twin(db, student_id)
    if not twin:
        return None
    twin.knowledge_gaps = gaps
    db.add(twin)
    await db.flush()
    return twin

async def update_next_review_items(db: AsyncSession, student_id: str, items: List[Dict[str, Any]]) -> Optional[LearningTwin]:
    twin = await get_learning_twin(db, student_id)
    if not twin:
        return None
    twin.next_review_items = items
    db.add(twin)
    await db.flush()
    return twin
