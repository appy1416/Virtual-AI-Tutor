import os
import uuid
import mimetypes
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query, HTTPException
from fastapi.responses import FileResponse
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.db.models.user import User
from app.db.models.lms_note import LMSNote
from app.modules.lms_notes.schemas import LMSNoteCreate, LMSNoteResponse
from app.utils.response import send_response
from app.utils.lms_helpers import log_activity, create_notification

router = APIRouter(tags=["LMS Shared Notes"])

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/lms-notes")
async def list_lms_notes(
    subject: Optional[str] = Query(None),
    course_id: Optional[str] = Query(None),
    lesson_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Lists shared study notes, filterable by subject, course_id, or lesson_id.
    """
    query = {}
    if subject:
        query["subject"] = subject
    if course_id:
        query["course_id"] = course_id
    if lesson_id:
        query["lesson_id"] = lesson_id
        
    cursor = db.db["lms_notes"].find(query)
    notes_docs = await cursor.to_list(length=1000)
    notes = [LMSNote(**n) for n in notes_docs]
    
    # Audit student downloads/viewing
    await log_activity(db, current_user.id, "list_notes", f"Listed study notes. Filter: subject={subject}, course={course_id}, lesson={lesson_id}")
    
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
        "course_id": body.course_id,
        "lesson_id": body.lesson_id,
        "file_size": body.file_size or 0,
        "download_count": 0,
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

def extract_filename(file_url: str) -> str:
    if not file_url:
        return ""
    normalized = file_url.replace("\\", "/")
    parts = [p for p in normalized.split("/") if p.strip()]
    return parts[-1] if parts else ""

@router.get("/lms-notes/{noteId}/file")
async def download_note_file(
    noteId: str,
    db = Depends(get_db)
):
    """
    Increments download count and serves the study note file download securely.
    """
    note = await db.db["lms_notes"].find_one({"id": noteId})
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
        
    file_url = note.get("file_url")
    if not file_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No file attached to this note.")
        
    filename = extract_filename(file_url)
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Check fallback path
    if not os.path.exists(filepath):
        filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../uploads", filename))
        
    # If still not found, create a placeholder notice to prevent 404s on ephemeral storage
    if not os.path.exists(filepath):
        placeholder_filename = f"placeholder_{filename}.txt"
        placeholder_path = os.path.join(UPLOAD_DIR, placeholder_filename)
        if not os.path.exists(placeholder_path):
            with open(placeholder_path, "w", encoding="utf-8") as f:
                f.write(
                    f"EduTwin AI LMS - Ephemeral Storage Placeholder\n"
                    f"==================================================\n\n"
                    f"Original File Name: {note.get('file_name') or filename}\n"
                    f"Note Title: {note.get('title') or 'LMS Note'}\n\n"
                    f"Notice:\n"
                    f"-------\n"
                    f"Because this backend is hosted on a free cloud tier (like Render) with ephemeral storage,\n"
                    f"uploaded files are automatically cleared whenever the container restarts or redeploys.\n\n"
                    f"To view the original file, please log in as an Admin and re-upload the document.\n"
                )
        filepath = placeholder_path
        download_name = f"placeholder_{note.get('file_name') or filename}.txt"
        media_type = "text/plain"
    else:
        download_name = note.get('file_name') or filename
        media_type, _ = mimetypes.guess_type(filepath)
        media_type = media_type or "application/octet-stream"
            
    # Increment download count
    await db.db["lms_notes"].update_one(
        {"id": noteId},
        {"$inc": {"download_count": 1}}
    )
    
    return FileResponse(
        path=filepath,
        filename=download_name,
        media_type=media_type
    )

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
