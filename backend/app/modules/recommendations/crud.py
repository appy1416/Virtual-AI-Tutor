from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Optional

from app.db.models.recommendation import Recommendation

async def create_recommendation(
    db: AsyncSession,
    student_id: str,
    recommendation_type: str,
    target_id: str,
    target_title: str,
    reason: str,
    relevance_score: int
) -> Recommendation:
    rec = Recommendation(
        student_id=student_id,
        recommendation_type=recommendation_type,
        target_id=target_id,
        target_title=target_title,
        reason=reason,
        relevance_score=relevance_score,
        clicked=False
    )
    db.add(rec)
    await db.flush()
    return rec

async def get_recommendations(
    db: AsyncSession,
    student_id: str,
    limit: int = 10,
    skip: int = 0
) -> Tuple[List[Recommendation], int]:
    stmt_count = select(func.count(Recommendation.id)).where(Recommendation.student_id == student_id)
    res_count = await db.execute(stmt_count)
    total = res_count.scalar() or 0

    stmt = select(Recommendation).where(Recommendation.student_id == student_id).order_by(Recommendation.relevance_score.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all()), total

async def mark_clicked(db: AsyncSession, recommendation_id: str) -> Optional[Recommendation]:
    stmt = select(Recommendation).where(Recommendation.id == recommendation_id)
    res = await db.execute(stmt)
    rec = res.scalars().first()
    if not rec:
        return None
    rec.clicked = True
    db.add(rec)
    await db.flush()
    return rec

async def delete_old_recommendations(db: AsyncSession, days: int = 30) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = delete(Recommendation).where(Recommendation.created_at < cutoff)
    res = await db.execute(stmt)
    return res.rowcount
