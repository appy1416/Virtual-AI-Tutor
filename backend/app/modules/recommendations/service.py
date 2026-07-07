from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Tuple, Optional

from app.modules.recommendations import crud as rec_crud
from app.modules.recommendations.engine import simple_recommendation_engine
from app.db.models.recommendation import Recommendation

async def get_recommendations(
    db: AsyncSession,
    student_id: str,
    limit: int = 10,
    skip: int = 0
) -> Tuple[List[Recommendation], int]:
    # Try fetching from DB
    recs, total = await rec_crud.get_recommendations(db, student_id, limit, skip)
    
    # If empty, generate them on the fly
    if not recs:
        generated = await generate_recommendations(db, student_id)
        # Re-fetch from DB
        recs, total = await rec_crud.get_recommendations(db, student_id, limit, skip)
        
    return recs, total

async def mark_recommendation_clicked(db: AsyncSession, recommendation_id: str) -> Optional[Recommendation]:
    return await rec_crud.mark_clicked(db, recommendation_id)

async def generate_recommendations(db: AsyncSession, student_id: str) -> List[Recommendation]:
    # 1. Clear existing recommendations for this user
    from sqlalchemy import delete
    await db.execute(delete(Recommendation).where(Recommendation.student_id == student_id))
    await db.flush()

    # 2. Run engine
    results = await simple_recommendation_engine(student_id, db)

    # 3. Save to DB
    saved_recs = []
    for r in results[:10]:  # store top 10
        rec = await rec_crud.create_recommendation(
            db=db,
            student_id=student_id,
            recommendation_type=r["recommendation_type"],
            target_id=r["target_id"],
            target_title=r["target_title"],
            reason=r["reason"],
            relevance_score=r["relevance_score"]
        )
        saved_recs.append(rec)
        
    return saved_recs
