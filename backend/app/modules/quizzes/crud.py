from datetime import datetime, timezone
import uuid
from typing import List, Tuple, Dict, Any, Optional
from app.db.models.quiz import Quiz, QuizAnswer

async def create_quiz(
    db,
    lesson_id: str,
    question_text: str,
    quiz_type: str,
    options: List[Dict[str, Any]],
    correct_answer: Optional[str] = None,
    difficulty_level: int = 5,
    max_attempts: int = 3,
    time_limit_seconds: Optional[int] = None,
    passing_score: int = 70,
    explanation: Optional[str] = None,
    is_published: bool = True,
    available_from: Optional[datetime] = None,
    available_until: Optional[datetime] = None,
    negative_marking: float = 0.0
) -> Quiz:
    quiz_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    # Process datetimes
    from_time = available_from.isoformat() if isinstance(available_from, datetime) else available_from
    until_time = available_until.isoformat() if isinstance(available_until, datetime) else available_until
    
    quiz_doc = {
        "id": quiz_id,
        "lesson_id": lesson_id,
        "question_text": question_text,
        "quiz_type": quiz_type,
        "options": options,
        "correct_answer": correct_answer,
        "difficulty_level": difficulty_level,
        "max_attempts": max_attempts,
        "time_limit_seconds": time_limit_seconds,
        "passing_score": passing_score,
        "explanation": explanation,
        "is_published": is_published,
        "available_from": from_time,
        "available_until": until_time,
        "negative_marking": negative_marking,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }
    await db.db["quizzes"].insert_one(quiz_doc)
    return Quiz(**quiz_doc)

async def get_quiz(db, quiz_id: str) -> Optional[Quiz]:
    doc = await db.db["quizzes"].find_one({"id": quiz_id, "deleted_at": None})
    return Quiz(**doc) if doc else None

async def list_quizzes(db, lesson_id: str, skip: int = 0, limit: int = 50) -> Tuple[List[Quiz], int]:
    query = {"lesson_id": lesson_id, "deleted_at": None}
    total = await db.db["quizzes"].count_documents(query)
    cursor = db.db["quizzes"].find(query).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [Quiz(**d) for d in docs], total

async def update_quiz(db, quiz_id: str, **fields) -> Optional[Quiz]:
    doc = await db.db["quizzes"].find_one({"id": quiz_id, "deleted_at": None})
    if not doc:
        return None
    fields["updated_at"] = datetime.now(timezone.utc)
    
    # Handle datetime serialization in fields if present
    for k, v in fields.items():
        if isinstance(v, datetime):
            fields[k] = v.isoformat()
            
    await db.db["quizzes"].update_one({"id": quiz_id}, {"$set": fields})
    updated = await db.db["quizzes"].find_one({"id": quiz_id})
    return Quiz(**updated) if updated else None

async def delete_quiz(db, quiz_id: str) -> bool:
    res = await db.db["quizzes"].update_one(
        {"id": quiz_id, "deleted_at": None},
        {"$set": {"deleted_at": datetime.now(timezone.utc)}}
    )
    return res.modified_count > 0

# QuizAnswer CRUD
async def create_quiz_answer(
    db,
    quiz_id: str,
    student_id: str,
    user_answer: str,
    is_correct: Optional[bool] = None,
    confidence_level: Optional[int] = None,
    time_spent_seconds: int = 0,
    feedback: Optional[str] = None,
    points_awarded: int = 0
) -> QuizAnswer:
    ans_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    ans_doc = {
        "id": ans_id,
        "quiz_id": quiz_id,
        "student_id": student_id,
        "user_answer": user_answer,
        "is_correct": is_correct,
        "confidence_level": confidence_level,
        "time_spent_seconds": time_spent_seconds,
        "feedback": feedback,
        "points_awarded": points_awarded,
        "attempted_at": now
    }
    await db.db["quiz_answers"].insert_one(ans_doc)
    return QuizAnswer(**ans_doc)

async def get_quiz_answers_by_student(
    db,
    student_id: str,
    skip: int = 0,
    limit: int = 50
) -> Tuple[List[QuizAnswer], int]:
    query = {"student_id": student_id}
    total = await db.db["quiz_answers"].count_documents(query)
    cursor = db.db["quiz_answers"].find(query).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [QuizAnswer(**d) for d in docs], total

async def get_quiz_performance(db, student_id: str, quiz_id: str) -> Dict[str, Any]:
    cursor = db.db["quiz_answers"].find({"student_id": student_id, "quiz_id": quiz_id})
    attempts = await cursor.to_list(length=1000)

    if not attempts:
        return {"accuracy": 0.0, "avg_score": 0.0, "attempts_count": 0, "avg_time_spent": 0.0}

    correct_count = sum(1 for a in attempts if a.get("is_correct") is True)
    total_attempts = len(attempts)
    avg_time = sum(a.get("time_spent_seconds", 0) for a in attempts) / total_attempts
    accuracy = (correct_count / total_attempts) * 100.0 if total_attempts > 0 else 0.0

    return {
        "accuracy": accuracy,
        "avg_score": accuracy,
        "attempts_count": total_attempts,
        "avg_time_spent": avg_time
    }

async def list_attempts(db, quiz_id: str, student_id: str) -> List[QuizAnswer]:
    cursor = db.db["quiz_answers"].find({"quiz_id": quiz_id, "student_id": student_id}).sort("attempted_at", 1)
    docs = await cursor.to_list(length=100)
    return [QuizAnswer(**d) for d in docs]
