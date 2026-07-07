from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional
import uuid
from datetime import datetime, timezone

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
    db = Depends(get_db)
):
    """
    Lists shared study notes, filterable by subject.
    """
    query = {}
    if subject:
        query["subject"] = subject
        
    cursor = db.db["lms_notes"].find(query)
    notes_docs = await cursor.to_list(length=1000)
    notes = [LMSNote(**n) for n in notes_docs]
    
    # Audit student downloads/viewing
    await log_activity(db, current_user.id, "list_notes", f"Listed study notes. Filter: {subject}")
    
    data = [LMSNoteResponse.model_validate(n) for n in notes]
    return send_response(status_code=status.HTTP_200_OK, success=True, data=data)

@router.post("/lms-notes", status_code=status.HTTP_201_CREATED)
async def create_lms_note(
    body: LMSNoteCreate,
    current_user: User = Depends(RoleChecker(["admin"])),
    db = Depends(get_db)
):
    """
    Saves a shared note metadata and sends notifications to students.
    """
    now = datetime.now(timezone.utc)
    note_id = str(uuid.uuid4())
    note_doc = {
        "id": note_id,
        "title": body.title,
        "description": body.description,
        "subject": body.subject,
        "file_name": body.file_name,
        "file_url": body.file_url,
        "file_type": body.file_type,
        "uploaded_by": current_user.id,
        "created_at": now,
        "updated_at": now
    }
    await db.db["lms_notes"].insert_one(note_doc)
    note = LMSNote(**note_doc)
    
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
    
    return send_response(status_code=status.HTTP_201_CREATED, success=True, data=LMSNoteResponse.model_validate(note))

@router.delete("/lms-notes/{noteId}")
async def delete_lms_note(
    noteId: str,
    current_user: User = Depends(RoleChecker(["admin"])),
    db = Depends(get_db)
):
    """
    Removes shared note metadata.
    """
    res = await db.db["lms_notes"].delete_one({"id": noteId})
    if res.deleted_count == 0:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Note not found.")
        
    return send_response(status_code=status.HTTP_200_OK, success=True, message="Note deleted successfully.")
