from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Dict, Any

from app.db.models.analytics import StudentPerformance
from app.db.models.user_course import UserCourse
from app.db.models.course import Course
from app.db.models.lesson import Lesson

async def simple_recommendation_engine(student_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
    # 1. Get student's weak performance records (score < 70)
    stmt_weak = select(StudentPerformance).where(
        StudentPerformance.student_id == student_id,
        StudentPerformance.score < 70
    )
    res_weak = await db.execute(stmt_weak)
    weak_records = res_weak.scalars().all()
    
    # Map lesson_id -> score
    weak_lessons = {w.lesson_id: w.score for w in weak_records}
    
    # 2. Get student's active enrollments to exclude
    stmt_enrolled = select(UserCourse.course_id).where(UserCourse.user_id == student_id)
    res_enrolled = await db.execute(stmt_enrolled)
    enrolled_course_ids = set(res_enrolled.scalars().all())

    recommendations = []

    # 3. Heuristic Course Recommendation
    # Find courses that are published, that the student is NOT enrolled in.
    stmt_courses = select(Course).where(
        Course.is_published == True,
        Course.deleted_at == None
    )
    res_courses = await db.execute(stmt_courses)
    all_courses = res_courses.scalars().all()
    
    for course in all_courses:
        if course.id in enrolled_course_ids:
            continue
            
        # Score calculation: if tutor matches student's interests or course is general.
        # If student has a weakness in a topic that matches the course category, boost score.
        relevance_score = 60  # baseline
        reason = f"Explore new horizons in {course.category}."
        
        # Check category match with weak lesson categories
        if weak_lessons:
            # Join lessons for this course to see if any matches weak area
            stmt_course_lessons = select(Lesson.id).where(Lesson.course_id == course.id, Lesson.deleted_at == None)
            res_cl = await db.execute(stmt_course_lessons)
            cl_ids = res_cl.scalars().all()
            
            overlap = [cl_id for cl_id in cl_ids if cl_id in weak_lessons]
            if overlap:
                min_score = min(weak_lessons[cl_id] for cl_id in overlap)
                relevance_score = min(95, 100 - min_score)
                reason = f"Improve your understanding of topics in {course.title} where you recently scored below 70%."
                
        recommendations.append({
            "target_id": course.id,
            "recommendation_type": "course",
            "target_title": course.title,
            "reason": reason,
            "relevance_score": int(relevance_score)
        })

    # Sort by relevance score desc
    recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
    return recommendations
