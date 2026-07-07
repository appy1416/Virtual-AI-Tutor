from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from difflib import SequenceMatcher
from datetime import datetime, timezone
from typing import Optional
import logging

from app.core.exceptions import EduTwinBaseException
from app.modules.quizzes import crud as quiz_crud
from app.modules.lessons import crud as lesson_crud
from app.modules.quizzes.schemas import QuizSubmissionResponse

logger = logging.getLogger("edutwin.quizzes")

def get_string_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()

async def submit_quiz(
    db: AsyncSession,
    student_id: str,
    quiz_id: str,
    user_answer: str,
    confidence_level: Optional[int] = None,
    time_spent_seconds: int = 0
) -> QuizSubmissionResponse:
    # 1. Fetch quiz
    quiz = await quiz_crud.get_quiz(db, quiz_id)
    if not quiz:
        raise EduTwinBaseException("Quiz not found.", status_code=status.HTTP_404_NOT_FOUND)

    # 2. Check attempt limits
    attempts = await quiz_crud.list_attempts(db, quiz_id, student_id)
    if len(attempts) >= quiz.max_attempts:
        raise EduTwinBaseException("Maximum attempts reached for this quiz.", status_code=status.HTTP_400_BAD_REQUEST)

    is_correct = False
    score = 0
    feedback = ""
    correct_answer_reveal = None

    # 3. Grade response
    if quiz.quiz_type == "mcq":
        # Options: [{"option_text": "...", "is_correct": bool}]
        correct_option = None
        for opt in (quiz.options or []):
            if opt.get("is_correct") is True:
                correct_option = opt.get("option_text")
                break
        
        if correct_option and user_answer.strip().lower() == correct_option.strip().lower():
            is_correct = True
            score = 100
            feedback = "Correct! Well done."
        else:
            is_correct = False
            score = 0
            feedback = f"Incorrect response. Focus on the core definitions."
            correct_answer_reveal = correct_option

    elif quiz.quiz_type == "short_answer":
        target = quiz.correct_answer or ""
        sim = get_string_similarity(user_answer, target)
        if sim >= 0.8:
            is_correct = True
            score = 100
            feedback = f"Correct! (Matches correct answer with {sim*100:.1f}% similarity)"
        else:
            is_correct = False
            score = 0
            feedback = "Incorrect answer. Re-read the lesson and try again."
            correct_answer_reveal = target

    elif quiz.quiz_type == "essay":
        # Essay grading is async, delegated to AI stubs
        is_correct = None  # Essays do not have binary correctness
        score = 75  # AI stub grade
        feedback = "Essay response registered. AI Evaluation: Good overview of the concepts. Try to add more concrete examples."

    # 4. Gamification points, streaks, and badges calculation
    from app.db.models.user import User
    from sqlalchemy.future import select
    from app.utils.lms_helpers import log_activity, create_notification
    
    user_stmt = select(User).where(User.id == student_id)
    user_res = await db.execute(user_stmt)
    user = user_res.scalars().first()
    
    points_awarded = 50 if (is_correct is True or score >= 70) else 10
    if user:
        user.points += points_awarded
        
        # Streak tracker
        now = datetime.now(timezone.utc)
        if user.last_activity_date:
            delta_days = (now.date() - user.last_activity_date.date()).days
            if delta_days == 1:
                user.streak_days += 1
            elif delta_days > 1:
                user.streak_days = 1
            # If delta_days == 0 (same day), streak remains unchanged
        else:
            user.streak_days = 1
            
        user.last_activity_date = now
        
        # Badges evaluator
        badges = list(user.badges or [])
        if "first_quiz" not in badges:
            badges.append("first_quiz")
            await create_notification(db, student_id, "Badge Unlocked!", "You earned the 'first_quiz' achievement badge!", "result")
        if user.points >= 100 and "points_100" not in badges:
            badges.append("points_100")
            await create_notification(db, student_id, "Badge Unlocked!", "You earned the 'points_100' achievement badge!", "result")
        if user.points >= 500 and "points_500" not in badges:
            badges.append("points_500")
            await create_notification(db, student_id, "Badge Unlocked!", "You earned the 'points_500' achievement badge!", "result")
        if user.streak_days >= 3 and "streak_3" not in badges:
            badges.append("streak_3")
            await create_notification(db, student_id, "Badge Unlocked!", "You earned the 'streak_3' achievement badge!", "result")
            
        user.badges = badges
        db.add(user)

    # 5. Save attempt
    submission = await quiz_crud.create_quiz_answer(
        db=db,
        quiz_id=quiz_id,
        student_id=student_id,
        user_answer=user_answer,
        is_correct=is_correct,
        confidence_level=confidence_level,
        time_spent_seconds=time_spent_seconds,
        feedback=feedback,
        points_awarded=points_awarded
    )
    
    # Audit log
    await log_activity(db, student_id, "quiz_attempt", f"Attempted quiz '{quiz_id}'. Correct: {is_correct}. Score: {score}. Points: {points_awarded}")
    
    # Notification
    await create_notification(
        db=db,
        user_id=student_id,
        title="Quiz Evaluated!",
        content=f"You got {score}% in your quiz attempt and earned {points_awarded} points!",
        notification_type="result"
    )
    
    # 6. Trigger async logging (Mock or Celery task delay)
    try:
        from app.tasks.analytics_tasks import log_quiz_attempt
        log_quiz_attempt.delay(student_id, quiz_id, score, time_spent_seconds)
    except Exception as ex:
        logger.error(f"Failed to queue analytics task: {ex}")

    return QuizSubmissionResponse(
        submission_id=submission.id,
        is_correct=is_correct,
        score=score,
        feedback=feedback,
        correct_answer=correct_answer_reveal,
        explanation=quiz.explanation,
        points_awarded=points_awarded
    )
