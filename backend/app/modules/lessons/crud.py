from datetime import datetime, timezone
import uuid
from typing import Optional, List, Tuple
from app.db.models.lesson import Lesson, LessonCompletion

async def create_lesson(
    db,
    course_id: str,
    sequence_order: int,
    title: str,
    description: str,
    content: str,
    learning_objectives: List[str],
    estimated_duration_minutes: int = 30,
    difficulty_score: int = 5
) -> Lesson:
    lesson_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    doc = {
        "id": lesson_id,
        "course_id": course_id,
        "sequence_order": sequence_order,
        "title": title,
        "description": description,
        "content": content,
        "learning_objectives": learning_objectives,
        "estimated_duration_minutes": estimated_duration_minutes,
        "difficulty_score": difficulty_score,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }
    await db.db["lessons"].insert_one(doc)
    return Lesson(**doc)

async def get_lesson(db, lesson_id: str) -> Optional[Lesson]:
    doc = await db.db["lessons"].find_one({"id": lesson_id, "deleted_at": None})
    return Lesson(**doc) if doc else None

async def list_lessons(
    db,
    course_id: str,
    skip: int = 0,
    limit: int = 50
) -> Tuple[List[Lesson], int]:
    query = {"course_id": course_id, "deleted_at": None}
    total_count = await db.db["lessons"].count_documents(query)
    cursor = db.db["lessons"].find(query).sort("sequence_order", 1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [Lesson(**doc) for doc in docs], total_count

async def update_lesson(db, lesson_id: str, **fields) -> Optional[Lesson]:
    doc = await db.db["lessons"].find_one({"id": lesson_id, "deleted_at": None})
    if not doc:
        return None
    fields["updated_at"] = datetime.now(timezone.utc)
    await db.db["lessons"].update_one({"id": lesson_id}, {"$set": fields})
    updated = await db.db["lessons"].find_one({"id": lesson_id})
    return Lesson(**updated) if updated else None

async def delete_lesson(db, lesson_id: str) -> bool:
    res = await db.db["lessons"].update_one(
        {"id": lesson_id, "deleted_at": None},
        {"$set": {"deleted_at": datetime.now(timezone.utc)}}
    )
    return res.modified_count > 0

async def reorder_lessons(db, course_id: str, lesson_order_list: List[str]) -> None:
    for index, lesson_id in enumerate(lesson_order_list):
        await db.db["lessons"].update_one(
            {"id": lesson_id, "course_id": course_id},
            {"$set": {"sequence_order": index + 1}}
        )

async def mark_lesson_complete(db, user_id: str, lesson_id: str) -> LessonCompletion:
    now = datetime.now(timezone.utc)
    query = {"user_id": user_id, "lesson_id": lesson_id}
    doc = await db.db["lesson_completions"].find_one(query)
    if doc:
        return LessonCompletion(**doc)
    
    completion_id = str(uuid.uuid4())
    new_doc = {
        "id": completion_id,
        "user_id": user_id,
        "lesson_id": lesson_id,
        "completed_at": now
    }
    await db.db["lesson_completions"].insert_one(new_doc)
    return LessonCompletion(**new_doc)

async def is_lesson_completed(db, user_id: str, lesson_id: str) -> bool:
    doc = await db.db["lesson_completions"].find_one({"user_id": user_id, "lesson_id": lesson_id})
    return doc is not None
