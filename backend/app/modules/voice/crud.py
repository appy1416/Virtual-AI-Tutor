from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List, Tuple, Optional

from app.db.models.voice import VoiceSession

async def create_voice_session(
    db: AsyncSession,
    student_id: str,
    tutor_type: str = "ai_voice",
    lesson_id: Optional[str] = None
) -> VoiceSession:
    sess = VoiceSession(
        student_id=student_id,
        tutor_type=tutor_type,
        lesson_id=lesson_id,
        duration_seconds=0,
        audio_quality="medium"
    )
    db.add(sess)
    await db.flush()
    return sess

async def get_voice_session(db: AsyncSession, session_id: str) -> Optional[VoiceSession]:
    stmt = select(VoiceSession).where(VoiceSession.id == session_id)
    res = await db.execute(stmt)
    return res.scalars().first()

async def list_voice_sessions(
    db: AsyncSession,
    student_id: str,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[VoiceSession], int]:
    stmt_count = select(func.count(VoiceSession.id)).where(VoiceSession.student_id == student_id)
    res_count = await db.execute(stmt_count)
    total = res_count.scalar() or 0

    stmt = select(VoiceSession).where(VoiceSession.student_id == student_id).order_by(VoiceSession.started_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all()), total

async def update_voice_session(
    db: AsyncSession,
    session_id: str,
    transcription: Optional[str] = None,
    ai_response_audio: Optional[str] = None,
    audio_url: Optional[str] = None,
    duration_seconds: Optional[int] = None
) -> Optional[VoiceSession]:
    sess = await get_voice_session(db, session_id)
    if not sess:
        return None
    if transcription is not None:
        sess.transcription = transcription
    if ai_response_audio is not None:
        sess.ai_response_audio = ai_response_audio
    if audio_url is not None:
        sess.audio_url = audio_url
    if duration_seconds is not None:
        sess.duration_seconds = duration_seconds
    db.add(sess)
    await db.flush()
    return sess

async def close_voice_session(db: AsyncSession, session_id: str) -> Optional[VoiceSession]:
    sess = await get_voice_session(db, session_id)
    if not sess:
        return None
    ended_at = datetime.now(timezone.utc)
    started_at = sess.started_at
    if started_at and hasattr(started_at, "tzinfo"):
        if started_at.tzinfo is None:
            ended_at = ended_at.replace(tzinfo=None)
        else:
            started_at = started_at.astimezone(timezone.utc)
            ended_at = ended_at.astimezone(timezone.utc)
    else:
        ended_at = ended_at.replace(tzinfo=None)
    sess.ended_at = ended_at
    delta = ended_at - (started_at or ended_at)
    sess.duration_seconds = int(delta.total_seconds())
    db.add(sess)
    await db.flush()
    return sess

async def delete_voice_session(db: AsyncSession, session_id: str) -> bool:
    sess = await get_voice_session(db, session_id)
    if not sess:
        return False
    # Standard DB delete since voice logs are transient/removable or can be soft deleted if needed. 
    # We will do direct delete or set deleted_at. Since model doesn't have deleted_at field, we delete.
    from sqlalchemy import delete
    await db.execute(delete(VoiceSession).where(VoiceSession.id == session_id))
    await db.flush()
    return True
