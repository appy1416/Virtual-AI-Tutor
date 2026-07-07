from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func, and_

from app.db.models.course import Course
from app.db.models.lesson import Lesson, LessonCompletion
from app.db.models.user_course import UserCourse
from app.db.models.user import User

async def create_course(
    db: AsyncSession,
    tutor_id: str,
    title: str,
    description: str,
    category: str,
    level: str,
    thumbnail_url: Optional[str] = None,
    max_students: Optional[int] = None
) -> Course:
    course = Course(
        tutor_id=tutor_id,
        title=title,
        description=description,
        category=category,
        level=level,
        thumbnail_url=thumbnail_url,
        max_students=max_students
    )
    db.add(course)
    await db.flush()
    return course

async def get_course(db: AsyncSession, course_id: str) -> Optional[Course]:
    result = await db.execute(
        select(Course).where(Course.id == course_id, Course.deleted_at == None)
    )
    return result.scalars().first()

async def list_courses(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    level: Optional[str] = None,
    published_only: bool = True
) -> Tuple[List[Course], int]:
    query = select(Course).where(Course.deleted_at == None)
    
    if published_only:
        query = query.where(Course.is_published == True)
    if category:
        query = query.where(Course.category.ilike(category))
    if level:
        query = query.where(Course.level == level)
        
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0
    
    # Paginate
    query = query.order_by(Course.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    courses = list(result.scalars().all())
    
    return courses, total_count

async def update_course(db: AsyncSession, course_id: str, **fields) -> Optional[Course]:
    course = await get_course(db, course_id)
    if not course:
        return None
        
    for key, val in fields.items():
        if hasattr(course, key):
            setattr(course, key, val)
            
    course.updated_at = datetime.now(timezone.utc)
    db.add(course)
    await db.flush()
    return course

async def delete_course(db: AsyncSession, course_id: str) -> bool:
    course = await get_course(db, course_id)
    if not course:
        return False
        
    course.deleted_at = datetime.now(timezone.utc)
    db.add(course)
    await db.flush()
    return True

async def enroll_user_in_course(db: AsyncSession, user_id: str, course_id: str) -> UserCourse:
    enrollment = UserCourse(user_id=user_id, course_id=course_id)
    db.add(enrollment)
    await db.flush()
    return enrollment

async def unenroll_user_from_course(db: AsyncSession, user_id: str, course_id: str) -> bool:
    result = await db.execute(
        select(UserCourse).where(UserCourse.user_id == user_id, UserCourse.course_id == course_id)
    )
    enrollment = result.scalars().first()
    if not enrollment:
        return False
        
    await db.delete(enrollment)
    await db.flush()
    return True

async def is_user_enrolled(db: AsyncSession, user_id: str, course_id: str) -> bool:
    result = await db.execute(
        select(UserCourse).where(UserCourse.user_id == user_id, UserCourse.course_id == course_id)
    )
    return result.scalars().first() is not None

async def get_user_courses(
    db: AsyncSession,
    user_id: str,
    skip: int = 0,
    limit: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    # Select courses user is enrolled in
    query = select(Course).join(UserCourse, Course.id == UserCourse.course_id).where(
        UserCourse.user_id == user_id,
        Course.deleted_at == None
    )
    
    # Total count of enrolled courses
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0
    
    # Paginated courses
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    courses = result.scalars().all()
    
    items = []
    for course in courses:
        # Get total active lessons in this course
        total_lessons_query = select(func.count(Lesson.id)).where(
            Lesson.course_id == course.id,
            Lesson.deleted_at == None
        )
        total_lessons_res = await db.execute(total_lessons_query)
        lessons_total = total_lessons_res.scalar() or 0
        
        # Get completed lessons in this course for this user
        completed_lessons_query = select(func.count(LessonCompletion.id)).join(
            Lesson, Lesson.id == LessonCompletion.lesson_id
        ).where(
            Lesson.course_id == course.id,
            Lesson.deleted_at == None,
            LessonCompletion.user_id == user_id
        )
        completed_res = await db.execute(completed_lessons_query)
        lessons_completed = completed_res.scalar() or 0
        
        # Enrolled timestamp
        enrolled_res = await db.execute(
            select(UserCourse.enrolled_at).where(
                UserCourse.user_id == user_id,
                UserCourse.course_id == course.id
            )
        )
        enrolled_at = enrolled_res.scalar() or datetime.now(timezone.utc)
        
        progress_percentage = int((lessons_completed / lessons_total) * 100) if lessons_total > 0 else 0
        
        items.append({
            "id": course.id,
            "title": course.title,
            "lessons_completed": lessons_completed,
            "lessons_total": lessons_total,
            "progress_percentage": progress_percentage,
            "enrolled_at": enrolled_at
        })
        
    return items, total_count

async def get_tutor_courses(
    db: AsyncSession,
    tutor_id: str,
    skip: int = 0,
    limit: int = 10
) -> Tuple[List[Course], int]:
    query = select(Course).where(Course.tutor_id == tutor_id, Course.deleted_at == None)
    
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0
    
    query = query.order_by(Course.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    courses = list(result.scalars().all())
    
    return courses, total_count
