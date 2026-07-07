from datetime import datetime, timezone
import uuid
from typing import Optional, List, Dict, Any, Tuple
from app.db.models.course import Course
from app.db.models.user_course import UserCourse

async def create_course(
    db,
    tutor_id: str,
    title: str,
    description: str,
    category: str,
    level: str,
    thumbnail_url: Optional[str] = None,
    max_students: Optional[int] = None
) -> Course:
    course_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    course_doc = {
        "id": course_id,
        "tutor_id": tutor_id,
        "title": title,
        "description": description,
        "category": category,
        "level": level,
        "thumbnail_url": thumbnail_url,
        "max_students": max_students,
        "is_published": False,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }
    await db.db["courses"].insert_one(course_doc)
    return Course(**course_doc)

async def get_course(db, course_id: str) -> Optional[Course]:
    doc = await db.db["courses"].find_one({"id": course_id, "deleted_at": None})
    return Course(**doc) if doc else None

async def list_courses(
    db,
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    level: Optional[str] = None,
    published_only: bool = True
) -> Tuple[List[Course], int]:
    query = {"deleted_at": None}
    if published_only:
        query["is_published"] = True
    if category:
        query["category"] = {"$regex": f"^{category}$", "$options": "i"}
    if level:
        query["level"] = level
        
    total_count = await db.db["courses"].count_documents(query)
    cursor = db.db["courses"].find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    courses = [Course(**doc) for doc in docs]
    return courses, total_count

async def update_course(db, course_id: str, **fields) -> Optional[Course]:
    doc = await db.db["courses"].find_one({"id": course_id, "deleted_at": None})
    if not doc:
        return None
    fields["updated_at"] = datetime.now(timezone.utc)
    await db.db["courses"].update_one({"id": course_id}, {"$set": fields})
    updated = await db.db["courses"].find_one({"id": course_id})
    return Course(**updated) if updated else None

async def delete_course(db, course_id: str) -> bool:
    res = await db.db["courses"].update_one(
        {"id": course_id, "deleted_at": None},
        {"$set": {"deleted_at": datetime.now(timezone.utc)}}
    )
    return res.modified_count > 0

async def enroll_user_in_course(db, user_id: str, course_id: str) -> UserCourse:
    now = datetime.now(timezone.utc)
    enroll_doc = {
        "id": f"{user_id}_{course_id}",
        "user_id": user_id,
        "course_id": course_id,
        "enrolled_at": now,
        "completed_at": None
    }
    await db.db["user_courses"].update_one(
        {"user_id": user_id, "course_id": course_id},
        {"$set": enroll_doc},
        upsert=True
    )
    return UserCourse(**enroll_doc)

async def unenroll_user_from_course(db, user_id: str, course_id: str) -> bool:
    res = await db.db["user_courses"].delete_one({"user_id": user_id, "course_id": course_id})
    return res.deleted_count > 0

async def is_user_enrolled(db, user_id: str, course_id: str) -> bool:
    doc = await db.db["user_courses"].find_one({"user_id": user_id, "course_id": course_id})
    return doc is not None

async def get_user_courses(
    db,
    user_id: str,
    skip: int = 0,
    limit: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    # Find all enrolled course_ids
    enrollments_cursor = db.db["user_courses"].find({"user_id": user_id})
    enrollments = await enrollments_cursor.to_list(length=1000)
    
    course_ids = [e["course_id"] for e in enrollments]
    
    query = {"id": {"$in": course_ids}, "deleted_at": None}
    total_count = await db.db["courses"].count_documents(query)
    
    cursor = db.db["courses"].find(query).skip(skip).limit(limit)
    courses_docs = await cursor.to_list(length=limit)
    courses = [Course(**doc) for doc in courses_docs]
    
    # Map enrollment details to courses
    enrollment_map = {e["course_id"]: e for e in enrollments}
    
    items = []
    for course in courses:
        # Get total active lessons in this course
        lessons_count = await db.db["lessons"].count_documents({"course_id": course.id, "deleted_at": None})
        
        # Get completed lessons for this course and user
        # Fetch lesson_ids for this course
        lesson_ids_cursor = db.db["lessons"].find({"course_id": course.id, "deleted_at": None}, {"id": 1})
        lesson_ids_docs = await lesson_ids_cursor.to_list(length=1000)
        lesson_ids = [l["id"] for l in lesson_ids_docs]
        
        completed_lessons = 0
        if lesson_ids:
            completed_lessons = await db.db["lesson_completions"].count_documents({
                "user_id": user_id,
                "lesson_id": {"$in": lesson_ids}
            })
            
        progress_percentage = int((completed_lessons / lessons_count) * 100) if lessons_count > 0 else 0
        
        enrolled_at = enrollment_map.get(course.id, {}).get("enrolled_at") or datetime.now(timezone.utc)
        if isinstance(enrolled_at, str):
            try:
                enrolled_at = datetime.fromisoformat(enrolled_at)
            except Exception:
                pass
                
        items.append({
            "id": course.id,
            "title": course.title,
            "lessons_completed": completed_lessons,
            "lessons_total": lessons_count,
            "progress_percentage": progress_percentage,
            "enrolled_at": enrolled_at
        })
        
    return items, total_count

async def get_tutor_courses(
    db,
    tutor_id: str,
    skip: int = 0,
    limit: int = 10
) -> Tuple[List[Course], int]:
    query = {"tutor_id": tutor_id, "deleted_at": None}
    total_count = await db.db["courses"].count_documents(query)
    cursor = db.db["courses"].find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [Course(**d) for d in docs], total_count
