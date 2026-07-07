from datetime import datetime, timezone, timedelta
import uuid
from typing import List, Tuple, Optional
from app.db.models.recommendation import Recommendation

async def create_recommendation(
    db,
    student_id: str,
    recommendation_type: str,
    target_id: str,
    target_title: str,
    reason: str,
    relevance_score: int
) -> Recommendation:
    rec_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    rec_doc = {
        "id": rec_id,
        "student_id": student_id,
        "recommendation_type": recommendation_type,
        "target_id": target_id,
        "target_title": target_title,
        "reason": reason,
        "relevance_score": relevance_score,
        "clicked": False,
        "created_at": now,
        "updated_at": now
    }
    await db.db["recommendations"].insert_one(rec_doc)
    return Recommendation(**rec_doc)

async def get_recommendations(
    db,
    student_id: str,
    limit: int = 10,
    skip: int = 0
) -> Tuple[List[Recommendation], int]:
    query = {"student_id": student_id}
    total = await db.db["recommendations"].count_documents(query)
    cursor = db.db["recommendations"].find(query).sort("relevance_score", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [Recommendation(**d) for d in docs], total

async def mark_clicked(db, recommendation_id: str) -> Optional[Recommendation]:
    now = datetime.now(timezone.utc)
    await db.db["recommendations"].update_one(
        {"id": recommendation_id},
        {"$set": {"clicked": True, "updated_at": now}}
    )
    updated = await db.db["recommendations"].find_one({"id": recommendation_id})
    return Recommendation(**updated) if updated else None

async def delete_old_recommendations(db, days: int = 30) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    res = await db.db["recommendations"].delete_many({"created_at": {"$lt": cutoff}})
    return res.deleted_count
