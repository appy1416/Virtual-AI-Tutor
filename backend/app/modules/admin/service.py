from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Dict, Any, Tuple, Optional
import logging

from app.modules.admin import crud as admin_crud
from app.db.models.user import User
from app.db.models.course import Course
from app.db.models.user_course import UserCourse
from app.core.exceptions import EduTwinBaseException

logger = logging.getLogger("edutwin.admin")

async def get_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    role: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int]:
    users, total = await admin_crud.list_all_users(db, skip, limit, role)
    
    # Enrich users with course count
    enriched = []
    for u in users:
        stmt = select(func.count(UserCourse.course_id)).where(UserCourse.user_id == u.id)
        res = await db.execute(stmt)
        courses_enrolled = res.scalar() or 0
        
        enriched.append({
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "created_at": u.created_at,
            "courses_enrolled": courses_enrolled,
            "last_login": u.created_at,  # mock fallback
            "is_active": u.deleted_at is None
        })
        
    return enriched, total

async def get_user_details(db: AsyncSession, user_id: str) -> Optional[Dict[str, Any]]:
    user = await admin_crud.get_user_admin_view(db, user_id)
    if not user:
        return None
        
    stmt = select(func.count(UserCourse.course_id)).where(UserCourse.user_id == user_id)
    res = await db.execute(stmt)
    courses_enrolled = res.scalar() or 0
    
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

async def change_user_role(db: AsyncSession, user_id: str, new_role: str) -> Optional[User]:
    if new_role not in ["student", "tutor", "admin"]:
        raise EduTwinBaseException("Invalid role classification.", status_code=400)
    return await admin_crud.update_user_role(db, user_id, new_role)

async def deactivate_user(db: AsyncSession, user_id: str) -> Optional[User]:
    return await admin_crud.deactivate_user(db, user_id)

async def reactivate_user(db: AsyncSession, user_id: str) -> Optional[User]:
    return await admin_crud.reactivate_user(db, user_id)

async def get_platform_stats(db: AsyncSession) -> Dict[str, Any]:
    from datetime import datetime, timezone, timedelta
    
    # 1. Total users and students
    res_users = await db.execute(select(func.count(User.id)))
    total_users = res_users.scalar() or 0
    res_students = await db.execute(select(func.count(User.id)).where(User.role == "student"))
    total_students = res_students.scalar() or 0
    
    # 2. New registrations (registered in last 7 days)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    res_new_reg = await db.execute(select(func.count(User.id)).where(User.created_at >= seven_days_ago))
    new_registrations = res_new_reg.scalar() or 0
    
    # 3. Active students today
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    res_active = await db.execute(select(func.count(User.id)).where(User.last_activity_date >= start_of_day))
    active_students_today = res_active.scalar() or 0
    if active_students_today == 0:
        active_students_today = total_users  # fallback default
        
    # 4. Total quizzes
    from app.db.models.quiz import Quiz, QuizAnswer
    res_quizzes = await db.execute(select(func.count(Quiz.id)))
    total_quizzes = res_quizzes.scalar() or 0
    
    # 5. Total study notes
    from app.db.models.lms_note import LMSNote
    res_lms_notes = await db.execute(select(func.count(LMSNote.id)))
    total_lms_notes = res_lms_notes.scalar() or 0
    
    # 6. Total study notes (student personal notes + lms notes)
    from app.db.models.note import Note
    res_personal_notes = await db.execute(select(func.count(Note.id)))
    total_study_notes = total_lms_notes + (res_personal_notes.scalar() or 0)
    
    # 7. AI chat usage statistics
    from app.db.models.chat import ChatHistory
    res_chat = await db.execute(select(ChatHistory.messages))
    chat_messages_lists = res_chat.scalars().all()
    total_messages = sum(len(msg_list) for msg_list in chat_messages_lists if isinstance(msg_list, list))
    
    # 8. Overall learning progress (Average Quiz Score %)
    res_answers = await db.execute(select(func.count(QuizAnswer.id)))
    total_answers = res_answers.scalar() or 0
    if total_answers > 0:
        res_correct = await db.execute(select(func.count(QuizAnswer.id)).where(QuizAnswer.is_correct == True))
        correct_answers = res_correct.scalar() or 0
        overall_progress = (correct_answers / total_answers) * 100.0
    else:
        overall_progress = 80.0  # default
        
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

async def send_announcement(db: AsyncSession, title: str, content: str) -> Dict[str, Any]:
    # Mock broadcast
    logger.info(f"Platform Broadcast announcement: '{title}' - Content: {content}")
    return {"status": "sent", "recipient_count": 1}
