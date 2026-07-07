from datetime import datetime, timezone, timedelta
import uuid
from typing import List, Tuple, Dict, Any, Optional
from app.db.models.analytics import AnalyticsEvent, StudentPerformance

async def create_event(
    db,
    student_id: str,
    event_type: str,
    metadata_json: Dict[str, Any]
) -> AnalyticsEvent:
    ev_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    ev_doc = {
        "id": ev_id,
        "student_id": student_id,
        "event_type": event_type,
        "metadata_json": metadata_json,
        "created_at": now
    }
    await db.db["analytics_events"].insert_one(ev_doc)
    return AnalyticsEvent(**ev_doc)

async def get_student_events(
    db,
    student_id: str,
    skip: int = 0,
    limit: int = 50,
    event_type: Optional[str] = None
) -> Tuple[List[AnalyticsEvent], int]:
    query = {"student_id": student_id}
    if event_type:
        query["event_type"] = event_type
        
    total = await db.db["analytics_events"].count_documents(query)
    cursor = db.db["analytics_events"].find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [AnalyticsEvent(**d) for d in docs], total

async def delete_old_events(db, days: int = 90) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    res = await db.db["analytics_events"].delete_many({"created_at": {"$lt": cutoff}})
    return res.deleted_count

async def count_active_users(db, last_n_days: int = 1) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=last_n_days)
    # Perform distinct student_id aggregation
    pipeline = [
        {"$match": {"created_at": {"$gte": cutoff}}},
        {"$group": {"_id": "$student_id"}},
        {"$count": "count"}
    ]
    cursor = db.db["analytics_events"].aggregate(pipeline)
    res = await cursor.to_list(length=1)
    return res[0]["count"] if res else 0

# StudentPerformance CRUD
async def create_performance_record(
    db,
    student_id: str,
    lesson_id: str,
    quiz_id: str,
    score: int,
    accuracy: int,
    time_spent_seconds: int
) -> StudentPerformance:
    query = {
        "student_id": student_id,
        "quiz_id": quiz_id
    }
    existing = await db.db["student_performances"].find_one(query)
    now = datetime.now(timezone.utc)
    
    if existing:
        fields = {
            "score": score,
            "accuracy": accuracy,
            "time_spent_seconds": time_spent_seconds,
            "completion_status": "completed",
            "completed_at": now
        }
        await db.db["student_performances"].update_one({"id": existing["id"]}, {"$set": fields})
        updated = await db.db["student_performances"].find_one({"id": existing["id"]})
        return StudentPerformance(**updated)
        
    perf_id = str(uuid.uuid4())
    perf_doc = {
        "id": perf_id,
        "student_id": student_id,
        "lesson_id": lesson_id,
        "quiz_id": quiz_id,
        "score": score,
        "accuracy": accuracy,
        "time_spent_seconds": time_spent_seconds,
        "completion_status": "completed",
        "mastery_level": score,
        "completed_at": now
    }
    await db.db["student_performances"].insert_one(perf_doc)
    return StudentPerformance(**perf_doc)

async def update_mastery_level(db, student_id: str, lesson_id: str, new_mastery: int) -> None:
    await db.db["student_performances"].update_many(
        {"student_id": student_id, "lesson_id": lesson_id},
        {"$set": {"mastery_level": new_mastery}}
    )

async def get_student_performance(
    db,
    student_id: str,
    skip: int = 0,
    limit: int = 50
) -> Tuple[List[StudentPerformance], int]:
    query = {"student_id": student_id}
    total = await db.db["student_performances"].count_documents(query)
    cursor = db.db["student_performances"].find(query).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [StudentPerformance(**d) for d in docs], total

async def get_performance_by_lesson(db, lesson_id: str) -> List[StudentPerformance]:
    cursor = db.db["student_performances"].find({"lesson_id": lesson_id})
    docs = await cursor.to_list(length=1000)
    return [StudentPerformance(**d) for d in docs]
