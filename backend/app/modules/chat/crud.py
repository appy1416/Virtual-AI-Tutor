from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any

from app.db.models.chat import ChatHistory

async def create_chat_session(
    db: AsyncSession,
    student_id: str,
    lesson_id: Optional[str] = None,
    course_id: Optional[str] = None,
    ai_model: str = "openai"
) -> ChatHistory:
    session = ChatHistory(
        student_id=student_id,
        lesson_id=lesson_id,
        course_id=course_id,
        ai_model=ai_model,
        messages=[],
        message_count=0
    )
    db.add(session)
    await db.flush()
    return session

async def get_chat_session(db: AsyncSession, session_id: str) -> Optional[ChatHistory]:
    stmt = select(ChatHistory).where(ChatHistory.id == session_id)
    res = await db.execute(stmt)
    return res.scalars().first()

async def list_chat_sessions(
    db: AsyncSession,
    student_id: str,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[ChatHistory], int]:
    stmt_count = select(func.count(ChatHistory.id)).where(ChatHistory.student_id == student_id)
    res_count = await db.execute(stmt_count)
    total = res_count.scalar() or 0

    stmt = select(ChatHistory).where(ChatHistory.student_id == student_id).order_by(ChatHistory.started_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all()), total

async def add_message_to_session(
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str
) -> Optional[ChatHistory]:
    session = await get_chat_session(db, session_id)
    if not session:
        return None
        
    current_messages = list(session.messages or [])
    new_message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    current_messages.append(new_message)
    
    # We must explicitly re-assign to trigger SQLAlchemy JSON mutation detection!
    session.messages = current_messages
    session.message_count = len(current_messages)
    db.add(session)
    await db.flush()
    return session

async def close_chat_session(db: AsyncSession, session_id: str) -> Optional[ChatHistory]:
    session = await get_chat_session(db, session_id)
    if not session:
        return None
    session.ended_at = datetime.now(timezone.utc)
    db.add(session)
    await db.flush()
    return session
