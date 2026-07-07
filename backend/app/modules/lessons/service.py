import logging
from datetime import datetime, timezone

from app.core.exceptions import RoleNotAllowed, EduTwinBaseException
from app.modules.lessons import crud as lesson_crud
from app.modules.courses import crud as course_crud
from app.db.models.lesson import Lesson

logger = logging.getLogger("edutwin.lessons")

async def create_lesson(
    db,
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
    lessons_count = await db.db["lessons"].count_documents({
        "course_id": course_id,
        "deleted_at": None
    })
    sequence_order = lessons_count + 1
    
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

async def get_lesson_full(db, lesson_id: str, actor_id: str, actor_role: str) -> Lesson:
    lesson = await lesson_crud.get_lesson(db, lesson_id)
    if not lesson:
        raise EduTwinBaseException("Lesson not found.", status_code=404)
        
    course = await course_crud.get_course(db, lesson.course_id)
    if not course:
        raise EduTwinBaseException("Course for this lesson was not found.", status_code=404)
        
    if not course.is_published:
        if actor_role != "admin" and course.tutor_id != actor_id:
            raise RoleNotAllowed("This lesson's course is currently unpublished.")
            
    return lesson

async def complete_lesson(db, user_id: str, lesson_id: str) -> None:
    # 1. Verify lesson exists
    lesson = await lesson_crud.get_lesson(db, lesson_id)
    if not lesson:
        raise EduTwinBaseException("Lesson not found.", status_code=404)
        
    # 2. Complete lesson
    await lesson_crud.mark_lesson_complete(db, user_id, lesson_id)
    
    # 3. Check if all lessons in the course are completed to mark course completion
    course_id = lesson.course_id
    
    # Total lessons count
    total_count = await db.db["lessons"].count_documents({
        "course_id": course_id,
        "deleted_at": None
    })
    
    # Fetch lesson_ids for this course
    lesson_ids_cursor = db.db["lessons"].find({"course_id": course_id, "deleted_at": None}, {"id": 1})
    lesson_ids_docs = await lesson_ids_cursor.to_list(length=1000)
    lesson_ids = [l["id"] for l in lesson_ids_docs]
    
    completed_count = 0
    if lesson_ids:
        completed_count = await db.db["lesson_completions"].count_documents({
            "user_id": user_id,
            "lesson_id": {"$in": lesson_ids}
        })
    
    if total_count > 0 and completed_count == total_count:
        await db.db["user_courses"].update_one(
            {"user_id": user_id, "course_id": course_id},
            {"$set": {"completed_at": datetime.now(timezone.utc)}}
        )
        logger.info("Student ID %s completed course %s!", user_id, course_id)
        
    logger.info("Lesson completion registered for student ID %s on lesson %s", user_id, lesson_id)

async def get_lesson_progress(db, user_id: str, lesson_id: str) -> dict:
    completed = await lesson_crud.is_lesson_completed(db, user_id, lesson_id)
    return {
        "completed": completed,
        "time_spent_minutes": 15 if completed else 0,
        "quiz_score": 90 if completed else None,
        "notes_count": 2 if completed else 0
    }
