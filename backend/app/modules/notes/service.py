from typing import List, Optional, Dict, Any
import logging

from app.modules.notes import crud as note_crud
from app.db.models.note import Note

logger = logging.getLogger("edutwin.notes")

async def create_note(db, student_id: str, lesson_id: str, content: str) -> Note:
    word_count = len(content.strip().split()) if content else 0
    note = await note_crud.create_note(db, student_id, lesson_id, content, word_count)
    
    try:
        from app.tasks.analytics_tasks import log_note_creation
        log_note_creation.delay(student_id, note.id)
    except Exception as ex:
        logger.error(f"Failed to queue note creation task: {ex}")
        
    return note

async def summarize_note(db, note_id: str) -> Optional[Note]:
    note = await note_crud.get_note(db, note_id)
    if not note:
        return None
        
    note.ai_summary = f"Summary of Note ({note_id}): Focuses on core lesson concepts. Word count: {note.word_count}."
    db.add(note)
    await db.flush()
    return note

async def search_notes(db, student_id: str, query: str) -> List[Note]:
    return await note_crud.search_notes(db, student_id, query)

async def get_note_suggestions(db, student_id: str) -> List[Dict[str, Any]]:
    return [
        {"note_id": "suggested-note-1", "reason": "Weak topic detected in calculus"},
        {"note_id": "suggested-note-2", "reason": "No review in the last 7 days"}
    ]
