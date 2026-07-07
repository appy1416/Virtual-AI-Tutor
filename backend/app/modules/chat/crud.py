from datetime import datetime, timezone
import uuid
from typing import List, Tuple, Optional, Dict, Any
from app.db.models.chat import ChatHistory

async def create_chat_session(
    db,
    student_id: str,
    lesson_id: Optional[str] = None,
    course_id: Optional[str] = None,
    ai_model: str = "openai"
) -> ChatHistory:
    sess_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    sess_doc = {
        "id": sess_id,
        "student_id": student_id,
        "lesson_id": lesson_id,
        "course_id": course_id,
        "ai_model": ai_model,
        "messages": [],
        "message_count": 0,
        "started_at": now,
        "ended_at": None,
        "created_at": now,
        "updated_at": now
    }
    await db.db["chat_sessions"].insert_one(sess_doc)
    return ChatHistory(**sess_doc)

async def get_chat_session(db, session_id: str) -> Optional[ChatHistory]:
    doc = await db.db["chat_sessions"].find_one({"id": session_id})
    return ChatHistory(**doc) if doc else None

async def list_chat_sessions(
    db,
    student_id: str,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[ChatHistory], int]:
    query = {"student_id": student_id}
    total = await db.db["chat_sessions"].count_documents(query)
    cursor = db.db["chat_sessions"].find(query).sort("started_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [ChatHistory(**d) for d in docs], total

async def add_message_to_session(
    db,
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
    
    fields = {
        "messages": current_messages,
        "message_count": len(current_messages),
        "updated_at": datetime.now(timezone.utc)
    }
    await db.db["chat_sessions"].update_one({"id": session_id}, {"$set": fields})
    updated = await db.db["chat_sessions"].find_one({"id": session_id})
    return ChatHistory(**updated) if updated else None

async def close_chat_session(db, session_id: str) -> Optional[ChatHistory]:
    ended_at = datetime.now(timezone.utc)
    await db.db["chat_sessions"].update_one(
        {"id": session_id},
        {"$set": {"ended_at": ended_at, "updated_at": ended_at}}
    )
    updated = await db.db["chat_sessions"].find_one({"id": session_id})
    return ChatHistory(**updated) if updated else None
