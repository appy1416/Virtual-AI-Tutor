from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any

from app.db.models.learning_twin import LearningTwin
from app.db.models.analytics import StudentPerformance
from app.db.models.lesson import Lesson
from app.modules.learning_twin import crud as twin_crud

async def initialize_learning_twin(db: AsyncSession, student_id: str) -> LearningTwin:
    return await twin_crud.create_learning_twin(db, student_id)

async def update_learning_gaps_from_quizzes(student_id: str, db: AsyncSession) -> None:
    # 1. Fetch low score quiz performances
    stmt = select(StudentPerformance, Lesson.title).join(
        Lesson, StudentPerformance.lesson_id == Lesson.id
    ).where(
        StudentPerformance.student_id == student_id,
        StudentPerformance.score < 70
    )
    res = await db.execute(stmt)
    records = res.all()

    # 2. Build gap maps
    gaps = []
    for perf, lesson_title in records:
        gaps.append({
            "topic": lesson_title,
            "confidence_level": perf.score
        })

    # 3. Update twin record
    await twin_crud.update_knowledge_gaps(db, student_id, gaps)
