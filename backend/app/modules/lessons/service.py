import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.exceptions import RoleNotAllowed, EduTwinBaseException
from app.modules.lessons import crud as lesson_crud
from app.modules.courses import crud as course_crud
from app.db.models.lesson import Lesson, LessonCompletion

logger = logging.getLogger("edutwin.lessons")

async def create_lesson(
    db: AsyncSession,
    course_id: str,
    tutor_id: str,
    tutor_role: str,
    title: str,
    description: str,
    content: str,
    learning_objectives: list,
    estimated_duration_minutes: int = 30,
    difficulty_score: int = 5
) -> Lesson:
    # 1. Fetch course
    course = await course_crud.get_course(db, course_id)
    if not course:
        raise EduTwinBaseException("Course not found.", status_code=404)
        
    # 2. Check ownership
    if tutor_role != "admin" and course.tutor_id != tutor_id:
        raise RoleNotAllowed("You do not own this course to add lessons.")
        
    # 3. Generate sequence order (count + 1)
    res = await db.execute(
        select(func.count(Lesson.id)).where(
            Lesson.course_id == course_id,
            Lesson.deleted_at == None
        )
    )
    sequence_order = (res.scalar() or 0) + 1
    
    # 4. Save
    lesson = await lesson_crud.create_lesson(
        db=db,
        course_id=course_id,
        sequence_order=sequence_order,
        title=title,
        description=description,
        content=content,
        learning_objectives=learning_objectives,
        estimated_duration_minutes=estimated_duration_minutes,
        difficulty_score=difficulty_score
    )
    logger.info("Lesson '%s' created for course %s", title, course_id)
    return lesson

async def get_lesson_full(db: AsyncSession, lesson_id: str, actor_id: str, actor_role: str) -> Lesson:
    lesson = await lesson_crud.get_lesson(db, lesson_id)
    if not lesson:
        raise EduTwinBaseException("Lesson not found.", status_code=404)
        
    course = await course_crud.get_course(db, lesson.course_id)
    if not course:
        raise EduTwinBaseException("Course for this lesson was not found.", status_code=404)
        
    # If course is unpublished, only course owner or admin can see it
    if not course.is_published:
        if actor_role != "admin" and course.tutor_id != actor_id:
            raise RoleNotAllowed("This lesson's course is currently unpublished.")
            
    return lesson

async def complete_lesson(db: AsyncSession, user_id: str, lesson_id: str) -> None:
    # 1. Verify lesson exists
    lesson = await lesson_crud.get_lesson(db, lesson_id)
    if not lesson:
        raise EduTwinBaseException("Lesson not found.", status_code=404)
        
    # 2. Complete lesson
    await lesson_crud.mark_lesson_complete(db, user_id, lesson_id)
    
    # 3. Check if all lessons in the course are completed to mark course completion
    course_id = lesson.course_id
    
    # Total lessons count
    total_res = await db.execute(
        select(func.count(Lesson.id)).where(Lesson.course_id == course_id, Lesson.deleted_at == None)
    )
    total_count = total_res.scalar() or 0
    
    # Completed lessons count
    comp_res = await db.execute(
        select(func.count(Lesson.id)).join(
            LessonCompletion, Lesson.id == LessonCompletion.lesson_id
        ).where(
            Lesson.course_id == course_id,
            Lesson.deleted_at == None,
            LessonCompletion.user_id == user_id
        )
    )
    completed_count = comp_res.scalar() or 0
    
    if total_count > 0 and completed_count == total_count:
        # Mark Course completion in UserCourse
        from app.db.models.user_course import UserCourse
        from sqlalchemy import update
        await db.execute(
            update(UserCourse)
            .where(UserCourse.user_id == user_id, UserCourse.course_id == course_id)
            .values(completed_at=datetime.now(timezone.utc) if hasattr(datetime, 'now') else datetime.utcnow()) # fallback import safety
        )
        logger.info("Student ID %s completed course %s!", user_id, course_id)
        
    logger.info("Lesson completion registered for student ID %s on lesson %s", user_id, lesson_id)

async def get_lesson_progress(db: AsyncSession, user_id: str, lesson_id: str) -> dict:
    completed = await lesson_crud.is_lesson_completed(db, user_id, lesson_id)
    return {
        "completed": completed,
        "time_spent_minutes": 15 if completed else 0, # mock statistics
        "quiz_score": 90 if completed else None,
        "notes_count": 2 if completed else 0
    }
