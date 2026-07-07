from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, delete
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Dict, Any, Optional

from app.db.models.analytics import AnalyticsEvent, StudentPerformance

async def create_event(
    db: AsyncSession,
    student_id: str,
    event_type: str,
    metadata_json: Dict[str, Any]
) -> AnalyticsEvent:
    event = AnalyticsEvent(
        student_id=student_id,
        event_type=event_type,
        metadata_json=metadata_json
    )
    db.add(event)
    await db.flush()
    return event

async def get_student_events(
    db: AsyncSession,
    student_id: str,
    skip: int = 0,
    limit: int = 50,
    event_type: Optional[str] = None
) -> Tuple[List[AnalyticsEvent], int]:
    conditions = [AnalyticsEvent.student_id == student_id]
    if event_type:
        conditions.append(AnalyticsEvent.event_type == event_type)
        
    stmt_count = select(func.count(AnalyticsEvent.id)).where(and_(*conditions))
    res_count = await db.execute(stmt_count)
    total = res_count.scalar() or 0

    stmt = select(AnalyticsEvent).where(and_(*conditions)).order_by(AnalyticsEvent.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all()), total

async def delete_old_events(db: AsyncSession, days: int = 90) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = delete(AnalyticsEvent).where(AnalyticsEvent.created_at < cutoff)
    res = await db.execute(stmt)
    return res.rowcount

async def count_active_users(db: AsyncSession, last_n_days: int = 1) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=last_n_days)
    stmt = select(func.count(func.distinct(AnalyticsEvent.student_id))).where(AnalyticsEvent.created_at >= cutoff)
    res = await db.execute(stmt)
    return res.scalar() or 0

# StudentPerformance CRUD
async def create_performance_record(
    db: AsyncSession,
    student_id: str,
    lesson_id: str,
    quiz_id: str,
    score: int,
    accuracy: int,
    time_spent_seconds: int
) -> StudentPerformance:
    # Check if a performance record already exists for this student + quiz
    stmt = select(StudentPerformance).where(
        StudentPerformance.student_id == student_id,
        StudentPerformance.quiz_id == quiz_id
    )
    res = await db.execute(stmt)
    existing = res.scalars().first()
    
    if existing:
        existing.score = score
        existing.accuracy = accuracy
        existing.time_spent_seconds = time_spent_seconds
        existing.completion_status = "completed"
        existing.completed_at = datetime.now(timezone.utc)
        db.add(existing)
        await db.flush()
        return existing
        
    perf = StudentPerformance(
        student_id=student_id,
        lesson_id=lesson_id,
        quiz_id=quiz_id,
        score=score,
        accuracy=accuracy,
        time_spent_seconds=time_spent_seconds,
        completion_status="completed",
        mastery_level=score,  # initial mastery equals initial score
        completed_at=datetime.now(timezone.utc)
    )
    db.add(perf)
    await db.flush()
    return perf

async def update_mastery_level(db: AsyncSession, student_id: str, lesson_id: str, new_mastery: int) -> None:
    stmt = update(StudentPerformance).where(
        StudentPerformance.student_id == student_id,
        StudentPerformance.lesson_id == lesson_id
    ).values(mastery_level=new_mastery)
    await db.execute(stmt)
    await db.flush()

async def get_student_performance(
    db: AsyncSession,
    student_id: str,
    skip: int = 0,
    limit: int = 50
) -> Tuple[List[StudentPerformance], int]:
    stmt_count = select(func.count(StudentPerformance.id)).where(StudentPerformance.student_id == student_id)
    res_count = await db.execute(stmt_count)
    total = res_count.scalar() or 0

    stmt = select(StudentPerformance).where(StudentPerformance.student_id == student_id).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all()), total

async def get_performance_by_lesson(db: AsyncSession, lesson_id: str) -> List[StudentPerformance]:
    stmt = select(StudentPerformance).where(StudentPerformance.lesson_id == lesson_id)
    res = await db.execute(stmt)
    return list(res.scalars().all())
