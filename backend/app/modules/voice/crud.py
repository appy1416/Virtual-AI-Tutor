from datetime import datetime, timezone
import uuid
from typing import List, Tuple, Optional
from app.db.models.voice import VoiceSession

async def create_voice_session(
    db,
    student_id: str,
    tutor_type: str = "ai_voice",
    lesson_id: Optional[str] = None
) -> VoiceSession:
    sess_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    sess_doc = {
        "id": sess_id,
        "student_id": student_id,
        "tutor_type": tutor_type,
        "lesson_id": lesson_id,
        "audio_url": None,
        "transcription": None,
        "ai_response_audio": None,
        "duration_seconds": 0,
        "audio_quality": "medium",
        "started_at": now,
        "ended_at": None,
        "created_at": now
    }
    await db.db["voice_sessions"].insert_one(sess_doc)
    return VoiceSession(**sess_doc)

async def get_voice_session(db, session_id: str) -> Optional[VoiceSession]:
    doc = await db.db["voice_sessions"].find_one({"id": session_id})
    return VoiceSession(**doc) if doc else None

async def list_voice_sessions(
    db,
    student_id: str,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[VoiceSession], int]:
    query = {"student_id": student_id}
    total = await db.db["voice_sessions"].count_documents(query)
    cursor = db.db["voice_sessions"].find(query).sort("started_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [VoiceSession(**d) for d in docs], total

async def update_voice_session(
    db,
    session_id: str,
    transcription: Optional[str] = None,
    ai_response_audio: Optional[str] = None,
    audio_url: Optional[str] = None,
    duration_seconds: Optional[int] = None
) -> Optional[VoiceSession]:
    sess = await get_voice_session(db, session_id)
    if not sess:
        return None
    fields = {}
    if transcription is not None:
        fields["transcription"] = transcription
    if ai_response_audio is not None:
        fields["ai_response_audio"] = ai_response_audio
    if audio_url is not None:
        fields["audio_url"] = audio_url
    if duration_seconds is not None:
        fields["duration_seconds"] = duration_seconds
        
    await db.db["voice_sessions"].update_one({"id": session_id}, {"$set": fields})
    updated = await db.db["voice_sessions"].find_one({"id": session_id})
    return VoiceSession(**updated) if updated else None

async def close_voice_session(db, session_id: str) -> Optional[VoiceSession]:
    sess = await get_voice_session(db, session_id)
    if not sess:
        return None
    ended_at = datetime.now(timezone.utc)
    started_at = sess.started_at
    
    if started_at:
        if isinstance(started_at, str):
            try:
                started_at = datetime.fromisoformat(started_at)
            except Exception:
                started_at = ended_at
        started_at = started_at.astimezone(timezone.utc)
    else:
        started_at = ended_at
        
    ended_at = ended_at.astimezone(timezone.utc)
    delta = ended_at - started_at
    duration = int(delta.total_seconds())
    
    fields = {
        "ended_at": ended_at.isoformat(),
        "duration_seconds": duration
    }
    await db.db["voice_sessions"].update_one({"id": session_id}, {"$set": fields})
    updated = await db.db["voice_sessions"].find_one({"id": session_id})
    return VoiceSession(**updated) if updated else None

async def delete_voice_session(db, session_id: str) -> bool:
    res = await db.db["voice_sessions"].delete_one({"id": session_id})
    return res.deleted_count > 0
