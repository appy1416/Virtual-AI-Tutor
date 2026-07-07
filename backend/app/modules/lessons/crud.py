from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func

from app.db.models.lesson import Lesson, LessonCompletion

async def create_lesson(
    db: AsyncSession,
    course_id: str,
    sequence_order: int,
    title: str,
    description: str,
    content: str,
    learning_objectives: List[str],
    estimated_duration_minutes: int = 30,
    difficulty_score: int = 5
) -> Lesson:
    lesson = Lesson(
        course_id=course_id,
        sequence_order=sequence_order,
        title=title,
        description=description,
        content=content,
        learning_objectives=learning_objectives,
        estimated_duration_minutes=estimated_duration_minutes,
        difficulty_score=difficulty_score
    )
    db.add(lesson)
    await db.flush()
    return lesson

async def get_lesson(db: AsyncSession, lesson_id: str) -> Optional[Lesson]:
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.deleted_at == None)
    )
    return result.scalars().first()

async def list_lessons(
    db: AsyncSession,
    course_id: str,
    skip: int = 0,
    limit: int = 50
) -> Tuple[List[Lesson], int]:
    query = select(Lesson).where(
        Lesson.course_id == course_id,
        Lesson.deleted_at == None
    )
    
    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0
    
    # Paginate and order by sequence_order
    query = query.order_by(Lesson.sequence_order.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    lessons = list(result.scalars().all())
    
    return lessons, total_count

async def update_lesson(db: AsyncSession, lesson_id: str, **fields) -> Optional[Lesson]:
    lesson = await get_lesson(db, lesson_id)
    if not lesson:
        return None
        
    for key, val in fields.items():
        if hasattr(lesson, key):
            setattr(lesson, key, val)
            
    lesson.updated_at = datetime.now(timezone.utc)
    db.add(lesson)
    await db.flush()
    return lesson

async def delete_lesson(db: AsyncSession, lesson_id: str) -> bool:
    lesson = await get_lesson(db, lesson_id)
    if not lesson:
        return False
        
    lesson.deleted_at = datetime.now(timezone.utc)
    db.add(lesson)
    
    # Delete dependent completions (standard cascade or soft delete cascade)
    # Since completions are tracking, we can keep them or remove them. We will remove them.
    # The requirement says: 'delete_lesson(db, lesson_id) -> soft delete & cascade to quizzes, notes'
    # Since quizzes/notes are not in this phase, we just soft-delete the lesson.
    await db.flush()
    return True

async def reorder_lessons(db: AsyncSession, course_id: str, lesson_order_list: List[str]) -> None:
    """
    Sets sequence_order of lessons based on the supplied list order (1-indexed).
    Temporarily uses negative numbers to prevent immediate unique constraint violations.
    """
    # 1. Temporarily move sequence orders to negative domain
    for index, lesson_id in enumerate(lesson_order_list):
        await db.execute(
            update(Lesson)
            .where(Lesson.id == lesson_id, Lesson.course_id == course_id)
            .values(sequence_order=-(index + 1))
        )
    await db.flush()
    
    # 2. Assign final positive sequence orders
    for index, lesson_id in enumerate(lesson_order_list):
        await db.execute(
            update(Lesson)
            .where(Lesson.id == lesson_id, Lesson.course_id == course_id)
            .values(sequence_order=index + 1)
        )
    await db.flush()

async def mark_lesson_complete(db: AsyncSession, user_id: str, lesson_id: str) -> LessonCompletion:
    # Check if already completed
    stmt = select(LessonCompletion).where(
        LessonCompletion.user_id == user_id,
        LessonCompletion.lesson_id == lesson_id
    )
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if existing:
        return existing
        
    completion = LessonCompletion(user_id=user_id, lesson_id=lesson_id)
    db.add(completion)
    await db.flush()
    return completion

async def is_lesson_completed(db: AsyncSession, user_id: str, lesson_id: str) -> bool:
    stmt = select(LessonCompletion).where(
        LessonCompletion.user_id == user_id,
        LessonCompletion.lesson_id == lesson_id
    )
    res = await db.execute(stmt)
    return res.scalars().first() is not None
