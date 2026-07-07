from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.db.models.user import User
from app.modules.quizzes import service as quiz_service
from app.modules.quizzes import crud as quiz_crud
from app.modules.lessons import crud as lesson_crud
from app.modules.courses import crud as course_crud
from app.modules.quizzes.schemas import (
    QuizCreateRequest,
    QuizUpdateRequest,
    QuizResponse,
    QuizResponseWithAnswers,
    QuizSubmissionRequest,
    QuizSubmissionResponse
)
from app.utils.response import send_response

router = APIRouter(tags=["Quizzes"])

@router.get("/lessons/{lessonId}/quizzes")
async def list_lesson_quizzes(
    lessonId: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    quizzes, total = await quiz_crud.list_quizzes(db, lessonId, skip, limit)
    
    # Map to student response schema, stripping is_correct options
    items = []
    for q in quizzes:
        stripped_options = []
        for opt in (q.options or []):
            stripped_options.append({"option_text": opt.get("option_text")})
            
        items.append({
            "id": q.id,
            "lesson_id": q.lesson_id,
            "question_text": q.question_text,
            "quiz_type": q.quiz_type,
            "options": stripped_options,
            "difficulty_level": q.difficulty_level,
            "max_attempts": q.max_attempts,
            "time_limit_seconds": q.time_limit_seconds
        })

    data = {
        "items": items,
        "total_count": total
    }
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=data,
        message="Quizzes retrieved successfully."
    )

@router.post("/lessons/{lessonId}/quizzes", status_code=status.HTTP_201_CREATED)
async def create_lesson_quiz(
    lessonId: str,
    body: QuizCreateRequest,
    current_user: User = Depends(RoleChecker(["tutor", "admin"])),
    db = Depends(get_db)
):
    # Verify lesson and course ownership
    lesson = await lesson_crud.get_lesson(db, lessonId)
    if not lesson:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Lesson not found.")
        
    course = await course_crud.get_course(db, lesson.course_id)
    if not course:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Course not found.")
        
    if current_user.role != "admin" and course.tutor_id != current_user.id:
        return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="You are not authorized to manage quizzes for this course.")
        
    quiz = await quiz_crud.create_quiz(
        db=db,
        lesson_id=lessonId,
        question_text=body.question_text,
        quiz_type=body.quiz_type,
        options=[opt.model_dump() for opt in body.options] if body.options else [],
        correct_answer=body.correct_answer,
        difficulty_level=body.difficulty_level,
        max_attempts=body.max_attempts,
        time_limit_seconds=body.time_limit_seconds,
        passing_score=body.passing_score,
        explanation=body.explanation,
        is_published=body.is_published,
        available_from=body.available_from,
        available_until=body.available_until
    )
    return send_response(
        status_code=status.HTTP_201_CREATED,
        success=True,
        data=QuizResponseWithAnswers.model_validate(quiz),
        message="Quiz created successfully."
    )

@router.get("/quizzes/{quizId}")
async def get_quiz_details(
    quizId: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    quiz = await quiz_crud.get_quiz(db, quizId)
    if not quiz:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Quiz not found.")

    if current_user.role == "student":
        stripped_options = [{"option_text": opt.get("option_text")} for opt in (quiz.options or [])]
        data = {
            "id": quiz.id,
            "lesson_id": quiz.lesson_id,
            "question_text": quiz.question_text,
            "quiz_type": quiz.quiz_type,
            "options": stripped_options,
            "difficulty_level": quiz.difficulty_level,
            "max_attempts": quiz.max_attempts,
            "time_limit_seconds": quiz.time_limit_seconds
        }
        return send_response(status_code=status.HTTP_200_OK, success=True, data=data)
        
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=QuizResponseWithAnswers.model_validate(quiz)
    )

@router.put("/quizzes/{quizId}")
async def update_quiz(
    quizId: str,
    body: QuizUpdateRequest,
    current_user: User = Depends(RoleChecker(["tutor", "admin"])),
    db = Depends(get_db)
):
    quiz = await quiz_crud.get_quiz(db, quizId)
    if not quiz:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Quiz not found.")
        
    lesson = await lesson_crud.get_lesson(db, quiz.lesson_id)
    course = await course_crud.get_course(db, lesson.course_id)
    if current_user.role != "admin" and course.tutor_id != current_user.id:
        return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="You are not authorized to manage quizzes for this course.")
        
    fields = body.model_dump(exclude_unset=True)
    if "options" in fields and fields["options"]:
        fields["options"] = [opt.model_dump() for opt in body.options]
        
    updated = await quiz_crud.update_quiz(db, quizId, **fields)
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=QuizResponseWithAnswers.model_validate(updated),
        message="Quiz updated successfully."
    )

@router.delete("/quizzes/{quizId}")
async def delete_quiz(
    quizId: str,
    current_user: User = Depends(RoleChecker(["tutor", "admin"])),
    db = Depends(get_db)
):
    quiz = await quiz_crud.get_quiz(db, quizId)
    if not quiz:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Quiz not found.")
        
    lesson = await lesson_crud.get_lesson(db, quiz.lesson_id)
    course = await course_crud.get_course(db, lesson.course_id)
    if current_user.role != "admin" and course.tutor_id != current_user.id:
        return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="You are not authorized to manage quizzes for this course.")
        
    await quiz_crud.delete_quiz(db, quizId)
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        message="Quiz deleted successfully."
    )

@router.post("/quizzes/{quizId}/submit")
async def submit_quiz(
    quizId: str,
    body: QuizSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    res = await quiz_service.submit_quiz(
        db=db,
        student_id=current_user.id,
        quiz_id=quizId,
        user_answer=body.user_answer,
        confidence_level=body.confidence_level,
        time_spent_seconds=body.time_spent_seconds
    )
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=res,
        message="Quiz submission evaluated successfully."
    )

@router.get("/quizzes/{quizId}/results")
async def get_student_quiz_results(
    quizId: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    perf = await quiz_crud.get_quiz_performance(db, current_user.id, quizId)
    attempts = await quiz_crud.list_attempts(db, quizId, current_user.id)
    
    data = {
        "performance": perf,
        "attempts": [
            {
                "id": a.id,
                "user_answer": a.user_answer,
                "is_correct": a.is_correct,
                "time_spent_seconds": a.time_spent_seconds,
                "feedback": a.feedback,
                "attempted_at": a.attempted_at
            }
            for a in attempts
        ]
    }
    return send_response(status_code=status.HTTP_200_OK, success=True, data=data)

@router.get("/quizzes/{quizId}/stats")
async def get_quiz_global_stats(
    quizId: str,
    current_user: User = Depends(RoleChecker(["tutor", "admin"])),
    db = Depends(get_db)
):
    # Fetch performance stats for all attempts
    # Calculate average score and total attempts in MongoDB
    pipeline = [
        {"$match": {"quiz_id": quizId}},
        {"$group": {"_id": "$quiz_id", "avg_score": {"$avg": "$score"}, "count": {"$sum": 1}}}
    ]
    cursor = db.db["student_performances"].aggregate(pipeline)
    res = await cursor.to_list(length=1)
    
    avg_score = res[0]["avg_score"] if res else 0.0
    total_attempts = res[0]["count"] if res else 0
    
    data = {
        "average_score": round(avg_score or 0.0, 1),
        "total_attempts": total_attempts or 0
    }
    return send_response(status_code=status.HTTP_200_OK, success=True, data=data)
