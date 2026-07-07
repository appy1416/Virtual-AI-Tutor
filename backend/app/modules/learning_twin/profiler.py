from typing import List, Dict, Any

from app.db.models.learning_twin import LearningTwin
from app.db.models.analytics import StudentPerformance
from app.db.models.lesson import Lesson
from app.modules.learning_twin import crud as twin_crud

async def initialize_learning_twin(db, student_id: str) -> LearningTwin:
    return await twin_crud.create_learning_twin(db, student_id)

async def update_learning_gaps_from_quizzes(student_id: str, db) -> None:
    # 1. Fetch low score quiz performances
    cursor = db.db["student_performances"].find({
        "student_id": student_id,
        "score": {"$lt": 70}
    })
    records_docs = await cursor.to_list(length=1000)
    
    # 2. Build gap maps by fetching lesson titles
    gaps = []
    for doc in records_docs:
        lesson_doc = await db.db["lessons"].find_one({"id": doc.get("lesson_id")})
        lesson_title = lesson_doc.get("title") if lesson_doc else "Unknown Lesson"
        gaps.append({
            "topic": lesson_title,
            "confidence_level": doc.get("score")
        })

    # 3. Update twin record
    await twin_crud.update_knowledge_gaps(db, student_id, gaps)
