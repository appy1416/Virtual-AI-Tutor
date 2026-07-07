import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone

from app.core.exceptions import RoleNotAllowed, UserNotFound, EduTwinBaseException
from app.modules.courses import crud as course_crud
from app.modules.lessons import crud as lesson_crud
from app.modules.users import crud as user_crud
from app.utils.validators import validate_course_title, validate_category, validate_level
from app.db.models.user_course import UserCourse
from app.db.models.course import Course
from app.db.models.lesson import Lesson

logger = logging.getLogger("edutwin.courses")

async def create_course(
    db,
    tutor_id: str,
    title: str,
    description: str,
    category: str,
    level: str,
    thumbnail_url: Optional[str] = None,
    max_students: Optional[int] = None
) -> Dict[str, Any]:
    # 1. Verify tutor role
    tutor = await user_crud.get_user_by_id(db, tutor_id)
    if not tutor:
        raise UserNotFound("Tutor profile not found.")
    if tutor.role not in ["tutor", "admin"]:
        raise RoleNotAllowed("Only instructors and admins are allowed to create courses.")
        
    # 2. Validate parameters
    validate_course_title(title)
    validate_category(category)
    validate_level(level)
    
    # 3. Create course
    course = await course_crud.create_course(
        db=db,
        tutor_id=tutor_id,
        title=title,
        description=description,
        category=category,
        level=level,
        thumbnail_url=thumbnail_url,
        max_students=max_students
    )
    logger.info("Course created: '%s' by tutor ID %s", title, tutor_id)
    return course

async def publish_course(db, course_id: str, actor_id: str, actor_role: str) -> Dict[str, Any]:
    course = await course_crud.get_course(db, course_id)
    if not course:
        raise EduTwinBaseException("Course not found.", status_code=404)
        
    # Ownership authorization check
    if actor_role != "admin" and course.tutor_id != actor_id:
        logger.warning("Unauthorized attempt by user %s to publish course %s", actor_id, course_id)
        raise RoleNotAllowed("You do not own this course.")
        
    updated = await course_crud.update_course(db, course_id, is_published=True)
    logger.info("Published course: %s by actor %s", course_id, actor_id)
    return updated

async def get_course_with_lessons(db, course_id: str, actor_role: Optional[str] = None, actor_id: Optional[str] = None) -> Dict[str, Any]:
    course = await course_crud.get_course(db, course_id)
    if not course:
        raise EduTwinBaseException("Course not found.", status_code=404)
        
    # If course is not published, only owner or admin can view
    if not course.is_published:
        if not actor_role or (actor_role != "admin" and course.tutor_id != actor_id):
            raise RoleNotAllowed("This course is currently unpublished.")
            
    # Fetch lessons in sequence order
    lessons, _ = await lesson_crud.list_lessons(db, course_id, limit=200)
    
    from app.modules.courses.schemas import CourseResponse
    from app.modules.lessons.schemas import LessonResponse
    
    course_data = CourseResponse.model_validate(course)
    course_detail = course_data.model_dump()
    course_detail["lessons"] = [LessonResponse.model_validate(l).model_dump() for l in lessons]
    
    return course_detail

async def enroll_student(db, user_id: str, course_id: str) -> None:
    # 1. Verify student role
    student = await user_crud.get_user_by_id(db, user_id)
    if not student:
        raise UserNotFound()
    if student.role != "student":
        raise RoleNotAllowed("Only students can enroll in courses.")
        
    # 2. Verify course exists and is published
    course = await course_crud.get_course(db, course_id)
    if not course:
        raise EduTwinBaseException("Course not found.", status_code=404)
    if not course.is_published:
        raise EduTwinBaseException("Cannot enroll in an unpublished course.", status_code=400)
        
    # 3. Check duplicate enrollment
    enrolled = await course_crud.is_user_enrolled(db, user_id, course_id)
    if enrolled:
        raise EduTwinBaseException("Student is already enrolled in this course.", status_code=400)
        
    # 4. Enroll
    await course_crud.enroll_user_in_course(db, user_id, course_id)
    logger.info("Student ID %s enrolled in course %s", user_id, course_id)

async def unenroll_student(db, user_id: str, course_id: str) -> None:
    enrolled = await course_crud.is_user_enrolled(db, user_id, course_id)
    if not enrolled:
        raise EduTwinBaseException("Student is not enrolled in this course.", status_code=400)
        
    await course_crud.unenroll_user_from_course(db, user_id, course_id)
    logger.info("Student ID %s unenrolled from course %s", user_id, course_id)

async def get_student_courses(db, user_id: str, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
    items, total = await course_crud.get_user_courses(db, user_id, skip, limit)
    return {
        "items": items,
        "total_count": total,
        "page_count": (total + limit - 1) // limit if limit > 0 else 0,
        "current_page": (skip // limit) + 1 if limit > 0 else 1
    }

async def get_instructor_dashboard(db, tutor_id: str) -> Dict[str, Any]:
    # 1. Total courses created by tutor
    cursor_courses = db.db["courses"].find({"tutor_id": tutor_id, "deleted_at": None}, {"id": 1})
    courses_docs = await cursor_courses.to_list(length=1000)
    course_ids = [c["id"] for c in courses_docs]
    
    if not course_ids:
        return {
            "total_students": 0,
            "total_enrollments": 0,
            "avg_rating": 5.0
        }
        
    # 2. Total student enrollments
    total_enrollments = await db.db["user_courses"].count_documents({"course_id": {"$in": course_ids}})
    
    # 3. Unique students count
    pipeline = [
        {"$match": {"course_id": {"$in": course_ids}}},
        {"$group": {"_id": "$user_id"}},
        {"$count": "count"}
    ]
    cursor = db.db["user_courses"].aggregate(pipeline)
    res = await cursor.to_list(length=1)
    total_students = res[0]["count"] if res else 0
    
    return {
        "total_students": total_students,
        "total_enrollments": total_enrollments,
        "avg_rating": 4.8
    }
