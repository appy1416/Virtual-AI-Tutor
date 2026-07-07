from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, update, delete
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any, Optional

from app.db.models.quiz import Quiz, QuizAnswer

async def create_quiz(
    db: AsyncSession,
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
    available_until: Optional[datetime] = None
) -> Quiz:
    quiz = Quiz(
        lesson_id=lesson_id,
        question_text=question_text,
        quiz_type=quiz_type,
        options=options,
        correct_answer=correct_answer,
        difficulty_level=difficulty_level,
        max_attempts=max_attempts,
        time_limit_seconds=time_limit_seconds,
        passing_score=passing_score,
        explanation=explanation,
        is_published=is_published,
        available_from=available_from,
        available_until=available_until
    )
    db.add(quiz)
    await db.flush()
    return quiz

async def get_quiz(db: AsyncSession, quiz_id: str) -> Optional[Quiz]:
    stmt = select(Quiz).where(Quiz.id == quiz_id, Quiz.deleted_at == None)
    res = await db.execute(stmt)
    return res.scalars().first()

async def list_quizzes(db: AsyncSession, lesson_id: str, skip: int = 0, limit: int = 50) -> Tuple[List[Quiz], int]:
    stmt_count = select(func.count(Quiz.id)).where(Quiz.lesson_id == lesson_id, Quiz.deleted_at == None)
    res_count = await db.execute(stmt_count)
    total = res_count.scalar() or 0

    stmt = select(Quiz).where(Quiz.lesson_id == lesson_id, Quiz.deleted_at == None).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all()), total

async def update_quiz(db: AsyncSession, quiz_id: str, **fields) -> Optional[Quiz]:
    quiz = await get_quiz(db, quiz_id)
    if not quiz:
        return None
    for k, v in fields.items():
        if hasattr(quiz, k):
            setattr(quiz, k, v)
    db.add(quiz)
    await db.flush()
    return quiz

async def delete_quiz(db: AsyncSession, quiz_id: str) -> bool:
    quiz = await get_quiz(db, quiz_id)
    if not quiz:
        return False
    quiz.deleted_at = datetime.now(timezone.utc)
    db.add(quiz)
    await db.flush()
    return True

# QuizAnswer CRUD
async def create_quiz_answer(
    db: AsyncSession,
    quiz_id: str,
    student_id: str,
    user_answer: str,
    is_correct: Optional[bool] = None,
    confidence_level: Optional[int] = None,
    time_spent_seconds: int = 0,
    feedback: Optional[str] = None,
    points_awarded: int = 0
) -> QuizAnswer:
    ans = QuizAnswer(
        quiz_id=quiz_id,
        student_id=student_id,
        user_answer=user_answer,
        is_correct=is_correct,
        confidence_level=confidence_level,
        time_spent_seconds=time_spent_seconds,
        feedback=feedback,
        points_awarded=points_awarded
    )
    db.add(ans)
    await db.flush()
    return ans

async def get_quiz_answers_by_student(
    db: AsyncSession,
    student_id: str,
    skip: int = 0,
    limit: int = 50
) -> Tuple[List[QuizAnswer], int]:
    stmt_count = select(func.count(QuizAnswer.id)).where(QuizAnswer.student_id == student_id)
    res_count = await db.execute(stmt_count)
    total = res_count.scalar() or 0

    stmt = select(QuizAnswer).where(QuizAnswer.student_id == student_id).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all()), total

async def get_quiz_performance(db: AsyncSession, student_id: str, quiz_id: str) -> Dict[str, Any]:
    stmt = select(QuizAnswer).where(QuizAnswer.student_id == student_id, QuizAnswer.quiz_id == quiz_id)
    res = await db.execute(stmt)
    attempts = list(res.scalars().all())

    if not attempts:
        return {"accuracy": 0.0, "avg_score": 0.0, "attempts_count": 0, "avg_time_spent": 0.0}

    correct_count = sum(1 for a in attempts if a.is_correct is True)
    total_attempts = len(attempts)
    avg_time = sum(a.time_spent_seconds for a in attempts) / total_attempts

    # Score calculation
    # MCQ is binary, average accuracy * 100 is score
    accuracy = (correct_count / total_attempts) * 100.0 if total_attempts > 0 else 0.0

    return {
        "accuracy": accuracy,
        "avg_score": accuracy,
        "attempts_count": total_attempts,
        "avg_time_spent": avg_time
    }

async def list_attempts(db: AsyncSession, quiz_id: str, student_id: str) -> List[QuizAnswer]:
    stmt = select(QuizAnswer).where(QuizAnswer.quiz_id == quiz_id, QuizAnswer.student_id == student_id).order_by(QuizAnswer.attempted_at.asc())
    res = await db.execute(stmt)
    return list(res.scalars().all())
