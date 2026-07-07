from datetime import datetime, timezone
import uuid
from typing import List, Tuple, Optional
from app.db.models.note import Note

async def create_note(db, student_id: str, lesson_id: str, content: str, word_count: int) -> Note:
    note_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    note_doc = {
        "id": note_id,
        "student_id": student_id,
        "lesson_id": lesson_id,
        "content": content,
        "word_count": word_count,
        "ai_summary": None,
        "tags": [],
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }
    await db.db["notes"].insert_one(note_doc)
    return Note(**note_doc)

async def get_note(db, note_id: str) -> Optional[Note]:
    doc = await db.db["notes"].find_one({"id": note_id, "deleted_at": None})
    return Note(**doc) if doc else None

async def list_notes(db, student_id: str, skip: int = 0, limit: int = 20) -> Tuple[List[Note], int]:
    query = {"student_id": student_id, "deleted_at": None}
    total = await db.db["notes"].count_documents(query)
    cursor = db.db["notes"].find(query).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [Note(**d) for d in docs], total

async def list_notes_by_lesson(db, lesson_id: str, student_id: str) -> List[Note]:
    query = {"lesson_id": lesson_id, "student_id": student_id, "deleted_at": None}
    cursor = db.db["notes"].find(query)
    docs = await cursor.to_list(length=100)
    return [Note(**d) for d in docs]

async def update_note(db, note_id: str, content: Optional[str] = None, tags: Optional[List[str]] = None, word_count: Optional[int] = None) -> Optional[Note]:
    note = await get_note(db, note_id)
    if not note:
        return None
    fields = {"updated_at": datetime.now(timezone.utc)}
    if content is not None:
        fields["content"] = content
    if tags is not None:
        fields["tags"] = tags
    if word_count is not None:
        fields["word_count"] = word_count
        
    await db.db["notes"].update_one({"id": note_id}, {"$set": fields})
    updated = await db.db["notes"].find_one({"id": note_id})
    return Note(**updated) if updated else None

async def delete_note(db, note_id: str) -> bool:
    res = await db.db["notes"].update_one(
        {"id": note_id, "deleted_at": None},
        {"$set": {"deleted_at": datetime.now(timezone.utc)}}
    )
    return res.modified_count > 0

async def search_notes(db, student_id: str, query: str) -> List[Note]:
    query_dict = {
        "student_id": student_id,
        "deleted_at": None,
        "content": {"$regex": query, "$options": "i"}
    }
    cursor = db.db["notes"].find(query_dict)
    docs = await cursor.to_list(length=100)
    return [Note(**doc) for doc in docs]
