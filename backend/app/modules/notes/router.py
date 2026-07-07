from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.db.models.user import User
from app.modules.notes import service as note_service
from app.modules.notes import crud as note_crud
from app.modules.notes.schemas import NoteCreateRequest, NoteUpdateRequest, NoteResponse, NoteDetailResponse
from app.utils.response import send_response

router = APIRouter(tags=["Notes"])

@router.get("/users/me/notes")
async def list_student_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(RoleChecker(["student"])),
    db: AsyncSession = Depends(get_db)
):
    notes, total = await note_crud.list_notes(db, current_user.id, skip, limit)
    
    items = []
    for n in notes:
        preview = n.content[:100] + "..." if len(n.content) > 100 else n.content
        items.append(NoteResponse(
            id=n.id,
            lesson_id=n.lesson_id,
            content_preview=preview,
            word_count=n.word_count,
            tags=n.tags or [],
            created_at=n.created_at
        ))
        
    data = {
        "items": items,
        "total_count": total
    }
    return send_response(status_code=status.HTTP_200_OK, success=True, data=data)

@router.post("/lessons/{lessonId}/notes", status_code=status.HTTP_201_CREATED)
async def create_student_note(
    lessonId: str,
    body: NoteCreateRequest,
    current_user: User = Depends(RoleChecker(["student"])),
    db: AsyncSession = Depends(get_db)
):
    note = await note_service.create_note(db, current_user.id, lessonId, body.content)
    return send_response(
        status_code=status.HTTP_201_CREATED,
        success=True,
        data=NoteDetailResponse.model_validate(note),
        message="Note drafted successfully."
    )

@router.get("/notes/{noteId}")
async def get_note_by_id(
    noteId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    note = await note_crud.get_note(db, noteId)
    if not note:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Note not found.")
        
    # Check authorization
    if current_user.role != "admin" and note.student_id != current_user.id:
        return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="Unauthorized access.")
        
    return send_response(status_code=status.HTTP_200_OK, success=True, data=NoteDetailResponse.model_validate(note))

@router.put("/notes/{noteId}")
async def update_note_by_id(
    noteId: str,
    body: NoteUpdateRequest,
    current_user: User = Depends(RoleChecker(["student"])),
    db: AsyncSession = Depends(get_db)
):
    note = await note_crud.get_note(db, noteId)
    if not note:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Note not found.")
        
    if note.student_id != current_user.id:
         return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="Unauthorized modification.")

    word_count = None
    if body.content is not None:
        word_count = len(body.content.strip().split())

    updated = await note_crud.update_note(
        db=db,
        note_id=noteId,
        content=body.content,
        tags=body.tags,
        word_count=word_count
    )
    return send_response(status_code=status.HTTP_200_OK, success=True, data=NoteDetailResponse.model_validate(updated))

@router.delete("/notes/{noteId}")
async def delete_note_by_id(
    noteId: str,
    current_user: User = Depends(RoleChecker(["student"])),
    db: AsyncSession = Depends(get_db)
):
    note = await note_crud.get_note(db, noteId)
    if not note:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Note not found.")
        
    if note.student_id != current_user.id:
         return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="Unauthorized deletion.")

    await note_crud.delete_note(db, noteId)
    return send_response(status_code=status.HTTP_200_OK, success=True, message="Note soft-deleted successfully.")

@router.get("/users/me/notes/search")
async def search_student_notes(
    q: str = Query(""),
    current_user: User = Depends(RoleChecker(["student"])),
    db: AsyncSession = Depends(get_db)
):
    notes = await note_service.search_notes(db, current_user.id, q)
    
    items = []
    for n in notes:
        preview = n.content[:100] + "..." if len(n.content) > 100 else n.content
        items.append(NoteResponse(
            id=n.id,
            lesson_id=n.lesson_id,
            content_preview=preview,
            word_count=n.word_count,
            tags=n.tags or [],
            created_at=n.created_at
        ))
        
    return send_response(status_code=status.HTTP_200_OK, success=True, data=items)

@router.post("/notes/{noteId}/summarize")
async def summarize_note_by_id(
    noteId: str,
    current_user: User = Depends(RoleChecker(["student"])),
    db: AsyncSession = Depends(get_db)
):
    note = await note_crud.get_note(db, noteId)
    if not note:
         return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Note not found.")
         
    if note.student_id != current_user.id:
         return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="Unauthorized access.")
         
    summarized = await note_service.summarize_note(db, noteId)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=NoteDetailResponse.model_validate(summarized))
