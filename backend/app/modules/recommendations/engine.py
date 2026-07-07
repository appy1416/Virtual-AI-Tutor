from typing import List, Dict, Any

from app.db.models.analytics import StudentPerformance
from app.db.models.user_course import UserCourse
from app.db.models.course import Course
from app.db.models.lesson import Lesson

async def simple_recommendation_engine(student_id: str, db) -> List[Dict[str, Any]]:
    # 1. Get student's weak performance records (score < 70)
    cursor_weak = db.db["student_performances"].find({
        "student_id": student_id,
        "score": {"$lt": 70}
    })
    weak_docs = await cursor_weak.to_list(length=1000)
    weak_records = [StudentPerformance(**w) for w in weak_docs]
    
    # Map lesson_id -> score
    weak_lessons = {w.lesson_id: w.score for w in weak_records}
    
    # 2. Get student's active enrollments to exclude
    cursor_enrolled = db.db["user_courses"].find({"user_id": student_id})
    enrolled_docs = await cursor_enrolled.to_list(length=1000)
    enrolled_course_ids = set(e["course_id"] for e in enrolled_docs)

    recommendations = []

    # 3. Heuristic Course Recommendation
    # Find courses that are published, that the student is NOT enrolled in.
    cursor_courses = db.db["courses"].find({
        "is_published": True,
        "deleted_at": None
    })
    courses_docs = await cursor_courses.to_list(length=1000)
    all_courses = [Course(**c) for c in courses_docs]
    
    for course in all_courses:
        if course.id in enrolled_course_ids:
            continue
            
        relevance_score = 60  # baseline
        reason = f"Explore new horizons in {course.category}."
        
        # Check category match with weak lesson categories
        if weak_lessons:
            # Join lessons for this course to see if any matches weak area
            cursor_cl = db.db["lessons"].find({"course_id": course.id, "deleted_at": None}, {"id": 1})
            cl_docs = await cursor_cl.to_list(length=1000)
            cl_ids = [l["id"] for l in cl_docs]
            
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
