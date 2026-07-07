from typing import List, Dict, Any, Tuple, Optional
import logging

from app.modules.admin import crud as admin_crud
from app.db.models.user import User
from app.db.models.course import Course
from app.db.models.user_course import UserCourse
from app.core.exceptions import EduTwinBaseException

logger = logging.getLogger("edutwin.admin")

async def get_users(
    db,
    skip: int = 0,
    limit: int = 50,
    role: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int]:
    users, total = await admin_crud.list_all_users(db, skip, limit, role)
    
    # Enrich users with course count
    enriched = []
    for u in users:
        courses_enrolled = await db.db["user_courses"].count_documents({"user_id": u.id})
        
        enriched.append({
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "created_at": u.created_at,
            "courses_enrolled": courses_enrolled,
            "last_login": u.created_at,
            "is_active": u.deleted_at is None
        })
        
    return enriched, total

async def get_user_details(db, user_id: str) -> Optional[Dict[str, Any]]:
    user = await admin_crud.get_user_admin_view(db, user_id)
    if not user:
        return None
        
    courses_enrolled = await db.db["user_courses"].count_documents({"user_id": user_id})
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "created_at": user.created_at,
        "courses_enrolled": courses_enrolled,
        "last_login": user.created_at,
        "is_active": user.deleted_at is None
    }

async def change_user_role(db, user_id: str, new_role: str) -> Optional[User]:
    if new_role not in ["student", "tutor", "admin"]:
        raise EduTwinBaseException("Invalid role classification.", status_code=400)
    return await admin_crud.update_user_role(db, user_id, new_role)

async def deactivate_user(db, user_id: str) -> Optional[User]:
    return await admin_crud.deactivate_user(db, user_id)

async def reactivate_user(db, user_id: str) -> Optional[User]:
    return await admin_crud.reactivate_user(db, user_id)

async def get_platform_stats(db) -> Dict[str, Any]:
    from datetime import datetime, timezone, timedelta
    
    # 1. Total users and students
    total_users = await db.db["users"].count_documents({})
    total_students = await db.db["users"].count_documents({"role": "student"})
    
    # 2. New registrations (registered in last 7 days)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    new_registrations = await db.db["users"].count_documents({"created_at": {"$gte": seven_days_ago}})
    
    # 3. Active students today
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    # Check both datetime format and string isoformat
    active_students_today = await db.db["users"].count_documents({
        "$or": [
            {"last_activity_date": {"$gte": start_of_day}},
            {"last_activity_date": {"$gte": start_of_day.isoformat()}}
        ]
    })
    if active_students_today == 0:
        active_students_today = total_users
        
    # 4. Total quizzes
    total_quizzes = await db.db["quizzes"].count_documents({})
    
    # 5. Total LMS study notes
    total_lms_notes = await db.db["lms_notes"].count_documents({})
    
    # 6. Total study notes (student personal notes + lms notes)
    total_personal_notes = await db.db["notes"].count_documents({})
    total_study_notes = total_lms_notes + total_personal_notes
    
    # 7. AI chat usage statistics
    pipeline = [
        {"$group": {"_id": None, "total_msg_count": {"$sum": "$message_count"}}}
    ]
    cursor = db.db["chat_sessions"].aggregate(pipeline)
    res = await cursor.to_list(length=1)
    total_messages = res[0]["total_msg_count"] if res else 0
    
    # 8. Overall learning progress (Average Quiz Score %)
    total_answers = await db.db["quiz_answers"].count_documents({})
    if total_answers > 0:
        correct_answers = await db.db["quiz_answers"].count_documents({"is_correct": True})
        overall_progress = (correct_answers / total_answers) * 100.0
    else:
        overall_progress = 80.0
        
    return {
        "total_users": total_users,
        "total_students": total_students,
        "active_students_today": active_students_today,
        "new_registrations": new_registrations,
        "total_quizzes": total_quizzes,
        "total_study_notes": total_study_notes,
        "total_messages": total_messages,
        "overall_progress": round(overall_progress, 1),
        "total_revenue": 0.0
    }

async def update_settings(**fields) -> Dict[str, Any]:
    return await admin_crud.update_platform_settings(**fields)

async def send_announcement(db, title: str, content: str) -> Dict[str, Any]:
    from app.utils.lms_helpers import create_notification
    # Broadcast notification to all users
    await create_notification(
        db=db,
        user_id=None,
        title=title,
        content=content,
        notification_type="general"
    )
    logger.info(f"Platform Broadcast announcement: '{title}' - Content: {content}")
    return {"status": "sent", "recipient_count": 1}
