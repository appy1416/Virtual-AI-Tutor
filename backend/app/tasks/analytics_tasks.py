import asyncio
from typing import Dict, Any
from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.modules.analytics import crud as analytics_crud
from app.modules.recommendations import service as rec_service

def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)

async def _log_page_view(student_id: str, page: str, duration: int):
    async with AsyncSessionLocal() as db:
        await analytics_crud.create_event(
            db=db,
            student_id=student_id,
            event_type="page_view",
            metadata_json={"page": page, "duration": duration}
        )
        await db.commit()

@celery_app.task
def log_page_view(student_id: str, page: str, duration: int):
    run_async(_log_page_view(student_id, page, duration))

async def _log_quiz_attempt(student_id: str, quiz_id: str, score: int, time_spent_seconds: int):
    async with AsyncSessionLocal() as db:
        # Create event
        await analytics_crud.create_event(
            db=db,
            student_id=student_id,
            event_type="quiz_attempt",
            metadata_json={"quiz_id": quiz_id, "score": score, "time_spent": time_spent_seconds}
        )
        # Create student performance record
        from app.modules.quizzes import crud as quiz_crud
        quiz = await quiz_crud.get_quiz(db, quiz_id)
        if quiz:
            await analytics_crud.create_performance_record(
                db=db,
                student_id=student_id,
                lesson_id=quiz.lesson_id,
                quiz_id=quiz_id,
                score=score,
                accuracy=score,
                time_spent_seconds=time_spent_seconds
            )
            # Update learning twin gaps
            from app.modules.learning_twin.profiler import update_learning_gaps_from_quizzes
            await update_learning_gaps_from_quizzes(student_id, db)
            
        await db.commit()

@celery_app.task
def log_quiz_attempt(student_id: str, quiz_id: str, score: int, time_spent_seconds: int):
    run_async(_log_quiz_attempt(student_id, quiz_id, score, time_spent_seconds))

async def _log_lesson_completion(student_id: str, lesson_id: str):
    async with AsyncSessionLocal() as db:
        await analytics_crud.create_event(
            db=db,
            student_id=student_id,
            event_type="lesson_complete",
            metadata_json={"lesson_id": lesson_id}
        )
        await db.commit()

@celery_app.task
def log_lesson_completion(student_id: str, lesson_id: str):
    run_async(_log_lesson_completion(student_id, lesson_id))

async def _log_note_creation(student_id: str, note_id: str):
    async with AsyncSessionLocal() as db:
        await analytics_crud.create_event(
            db=db,
            student_id=student_id,
            event_type="note_created",
            metadata_json={"note_id": note_id}
        )
        await db.commit()

@celery_app.task
def log_note_creation(student_id: str, note_id: str):
    run_async(_log_note_creation(student_id, note_id))

async def _log_chat_message(student_id: str, char_count: int):
    async with AsyncSessionLocal() as db:
        await analytics_crud.create_event(
            db=db,
            student_id=student_id,
            event_type="chat_message",
            metadata_json={"char_count": char_count}
        )
        await db.commit()

@celery_app.task
def log_chat_message(student_id: str, char_count: int):
    run_async(_log_chat_message(student_id, char_count))

async def _refresh_recommendations(student_id: str):
    async with AsyncSessionLocal() as db:
        await rec_service.generate_recommendations(db, student_id)
        await db.commit()

@celery_app.task
def refresh_recommendations(student_id: str):
    run_async(_refresh_recommendations(student_id))

async def _cleanup_old_events(days: int = 90):
    async with AsyncSessionLocal() as db:
        await analytics_crud.delete_old_events(db, days)
        await db.commit()

@celery_app.task
def cleanup_old_events(days: int = 90):
    run_async(_cleanup_old_events(days))
