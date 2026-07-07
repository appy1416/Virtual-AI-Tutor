from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from datetime import datetime, timezone
from typing import List, Tuple, Optional

from app.db.models.note import Note

async def create_note(db: AsyncSession, student_id: str, lesson_id: str, content: str, word_count: int) -> Note:
    note = Note(
        student_id=student_id,
        lesson_id=lesson_id,
        content=content,
        word_count=word_count,
        tags=[]
    )
    db.add(note)
    await db.flush()
    return note

async def get_note(db: AsyncSession, note_id: str) -> Optional[Note]:
    stmt = select(Note).where(Note.id == note_id, Note.deleted_at == None)
    res = await db.execute(stmt)
    return res.scalars().first()

async def list_notes(db: AsyncSession, student_id: str, skip: int = 0, limit: int = 20) -> Tuple[List[Note], int]:
    stmt_count = select(func.count(Note.id)).where(Note.student_id == student_id, Note.deleted_at == None)
    res_count = await db.execute(stmt_count)
    total = res_count.scalar() or 0

    stmt = select(Note).where(Note.student_id == student_id, Note.deleted_at == None).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all()), total

async def list_notes_by_lesson(db: AsyncSession, lesson_id: str, student_id: str) -> List[Note]:
    stmt = select(Note).where(Note.lesson_id == lesson_id, Note.student_id == student_id, Note.deleted_at == None)
    res = await db.execute(stmt)
    return list(res.scalars().all())

async def update_note(db: AsyncSession, note_id: str, content: Optional[str] = None, tags: Optional[List[str]] = None, word_count: Optional[int] = None) -> Optional[Note]:
    note = await get_note(db, note_id)
    if not note:
        return None
    if content is not None:
        note.content = content
    if tags is not None:
        note.tags = tags
    if word_count is not None:
        note.word_count = word_count
    db.add(note)
    await db.flush()
    return note

async def delete_note(db: AsyncSession, note_id: str) -> bool:
    note = await get_note(db, note_id)
    if not note:
        return False
    note.deleted_at = datetime.now(timezone.utc)
    db.add(note)
    await db.flush()
    return True

async def search_notes(db: AsyncSession, student_id: str, query: str) -> List[Note]:
    # Simple ilike SQL query for searching content/tags
    search_pattern = f"%{query}%"
    stmt = select(Note).where(
        Note.student_id == student_id,
        Note.deleted_at == None,
        Note.content.ilike(search_pattern)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())
