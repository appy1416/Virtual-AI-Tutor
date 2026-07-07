from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.db.models.user import User
from app.db.models.lms_note import LMSNote
from app.modules.lms_notes.schemas import LMSNoteCreate, LMSNoteResponse
from app.utils.response import send_response
from app.utils.lms_helpers import log_activity, create_notification

router = APIRouter(tags=["LMS Shared Notes"])

@router.get("/lms-notes")
async def list_lms_notes(
    subject: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists shared study notes, filterable by subject.
    """
    stmt = select(LMSNote)
    if subject:
        stmt = stmt.where(LMSNote.subject == subject)
        
    res = await db.execute(stmt)
    notes = res.scalars().all()
    
    # Audit student downloads/viewing
    await log_activity(db, current_user.id, "list_notes", f"Listed study notes. Filter: {subject}")
    
    data = [LMSNoteResponse.model_validate(n) for n in notes]
    return send_response(status_code=status.HTTP_200_OK, success=True, data=data)

@router.post("/lms-notes", status_code=status.HTTP_201_CREATED)
async def create_lms_note(
    body: LMSNoteCreate,
    current_user: User = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Saves a shared note metadata and sends notifications to students.
    """
    note = LMSNote(
        title=body.title,
        description=body.description,
        subject=body.subject,
        file_name=body.file_name,
        file_url=body.file_url,
        file_type=body.file_type,
        uploaded_by=current_user.id
    )
    db.add(note)
    await db.flush()
    
    # Audit log
    await log_activity(db, current_user.id, "upload_note", f"Uploaded shared note: {body.title}")
    
    # Dispatch notification to all students
    await create_notification(
        db=db,
        user_id=None,
        title="New Study Note Added!",
        content=f"Study note '{body.title}' has been uploaded for subject: {body.subject}.",
        notification_type="note"
    )
    
    await db.commit()
    return send_response(status_code=status.HTTP_201_CREATED, success=True, data=LMSNoteResponse.model_validate(note))

@router.delete("/lms-notes/{noteId}")
async def delete_lms_note(
    noteId: str,
    current_user: User = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Removes shared note metadata.
    """
    stmt = select(LMSNote).where(LMSNote.id == noteId)
    res = await db.execute(stmt)
    note = res.scalars().first()
    if not note:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Note not found.")
        
    await db.delete(note)
    await db.commit()
    return send_response(status_code=status.HTTP_200_OK, success=True, message="Note deleted successfully.")
