import os
import uuid
import mimetypes
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.db.models.user import User
from app.db.models.assignment import Assignment, AssignmentSubmission
from app.modules.assignments.schemas import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    SubmissionCreate,
    SubmissionResponse,
    SubmissionGradeRequest
)
from app.utils.response import send_response
from app.utils.lms_helpers import log_activity, create_notification

router = APIRouter(tags=["Assignments"])

# Configure local uploads folder
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/assignments/upload", status_code=status.HTTP_201_CREATED)
async def upload_assignment_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads a PDF, DOCX, or PPT file for assignments or study notes.
    """
    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    dest_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file content locally
    with open(dest_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    file_url = f"/uploads/{unique_filename}"
    return send_response(
        status_code=status.HTTP_201_CREATED,
        success=True,
        data={
            "file_url": file_url, 
            "file_name": file.filename,
            "file_size": len(content)
        },
        message="File uploaded successfully."
    )

@router.get("/assignments")
async def list_assignments(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Lists all assignments. Students only see published ones and filtered by their course enrollments.
    """
    query = {}
    if current_user.role == "student":
        query["is_published"] = True
        
        # Filter assignments by enrolled courses
        enrolled_docs = await db.db["user_courses"].find({"user_id": current_user.id}).to_list(length=1000)
        enrolled_course_ids = [doc["course_id"] for doc in enrolled_docs]
        query["$or"] = [
            {"course_ids": {"$in": enrolled_course_ids}},
            {"course_ids": []},
            {"course_ids": None}
        ]
    
    cursor = db.db["assignments"].find(query)
    assignments_docs = await cursor.to_list(length=1000)
    assignments = [Assignment(**a) for a in assignments_docs]
    
    # Enrich response with student submission state if they are student
    enriched = []
    for a in assignments:
        sub_status = "unsubmitted"
        marks = None
        feedback = None
        sub_id = None
        submitted_file_name = None
        submitted_file_url = None
        submission_text = None
        submitted_at = None
        
        if current_user.role == "student":
            sub = await db.db["assignment_submissions"].find_one({
                "assignment_id": a.id,
                "student_id": current_user.id
            })
            if sub:
                sub_status = "submitted" if sub.get("marks") is None else "graded"
                marks = sub.get("marks")
                feedback = sub.get("feedback")
                sub_id = sub.get("id")
                submitted_file_name = sub.get("file_name")
                submitted_file_url = sub.get("file_url")
                submission_text = sub.get("submission_text")
                submitted_at = sub.get("submitted_at")
                
        enriched.append({
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "deadline": a.deadline,
            "file_url": a.file_url,
            "is_published": a.is_published,
            "course_ids": getattr(a, "course_ids", []),
            "max_marks": getattr(a, "max_marks", 100),
            "created_at": a.created_at,
            "updated_at": a.updated_at,
            "submission_status": sub_status,
            "marks": marks,
            "feedback": feedback,
            "submission_id": sub_id,
            "submitted_file_name": submitted_file_name,
            "submitted_file_url": submitted_file_url,
            "submission_text": submission_text,
            "submitted_at": submitted_at
        })
        
    return send_response(status_code=status.HTTP_200_OK, success=True, data=enriched)

@router.post("/assignments", status_code=status.HTTP_201_CREATED)
async def create_assignment(
    body: AssignmentCreate,
    current_user: User = Depends(RoleChecker(["admin"])),
    db = Depends(get_db)
):
    """
    Creates a new assignment and dispatches notification to all users.
    """
    now = datetime.now(timezone.utc)
    assignment_doc = {
        "id": str(uuid.uuid4()),
        "title": body.title,
        "description": body.description,
        "deadline": body.deadline.isoformat() if isinstance(body.deadline, datetime) else body.deadline,
        "file_url": body.file_url,
        "is_published": body.is_published,
        "course_ids": body.course_ids or [],
        "max_marks": body.max_marks or 100,
        "created_at": now,
        "updated_at": now
    }
    await db.db["assignments"].insert_one(assignment_doc)
    assignment = Assignment(**assignment_doc)
    
    # Audit log
    await log_activity(db, current_user.id, "create_assignment", f"Created assignment: {body.title}")
    
    # Broadcast notification to all students if published
    if body.is_published:
        deadline_str = body.deadline.strftime('%Y-%m-%d %H:%M') if isinstance(body.deadline, datetime) else str(body.deadline)
        await create_notification(
            db=db,
            user_id=None,
            title="New Assignment Released!",
            content=f"Assignment '{body.title}' is now available. Deadline: {deadline_str}",
            notification_type="assignment"
        )
        
    return send_response(status_code=status.HTTP_201_CREATED, success=True, data=AssignmentResponse.model_validate(assignment))

@router.put("/assignments/{assignmentId}")
async def update_assignment(
    assignmentId: str,
    body: AssignmentUpdate,
    current_user: User = Depends(RoleChecker(["admin"])),
    db = Depends(get_db)
):
    """
    Modifies an existing assignment.
    """
    assignment_doc = await db.db["assignments"].find_one({"id": assignmentId})
    if not assignment_doc:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Assignment not found.")
        
    update_data = body.model_dump(exclude_unset=True)
    if "deadline" in update_data and isinstance(update_data["deadline"], datetime):
        update_data["deadline"] = update_data["deadline"].isoformat()
        
    update_data["updated_at"] = datetime.now(timezone.utc)
    await db.db["assignments"].update_one({"id": assignmentId}, {"$set": update_data})
    
    updated_doc = await db.db["assignments"].find_one({"id": assignmentId})
    assignment = Assignment(**updated_doc)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=AssignmentResponse.model_validate(assignment))

@router.delete("/assignments/{assignmentId}")
async def delete_assignment(
    assignmentId: str,
    current_user: User = Depends(RoleChecker(["admin"])),
    db = Depends(get_db)
):
    """
    Deletes an assignment record.
    """
    res = await db.db["assignments"].delete_one({"id": assignmentId})
    if res.deleted_count == 0:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Assignment not found.")
        
    # Cascade delete submissions
    await db.db["assignment_submissions"].delete_many({"assignment_id": assignmentId})
    return send_response(status_code=status.HTTP_200_OK, success=True, message="Assignment deleted successfully.")

@router.post("/assignments/{assignmentId}/submit")
async def submit_assignment(
    assignmentId: str,
    body: SubmissionCreate,
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    """
    Submits student work for an assignment. Overwrites previous submission if exists.
    """
    # Verify assignment exists
    assignment_doc = await db.db["assignments"].find_one({"id": assignmentId})
    if not assignment_doc:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Assignment not found.")
        
    # Check if already submitted
    query = {
        "assignment_id": assignmentId,
        "student_id": current_user.id
    }
    existing = await db.db["assignment_submissions"].find_one(query)
    now = datetime.now(timezone.utc)
    
    if existing:
        fields = {
            "submission_text": body.submission_text,
            "file_name": body.file_name,
            "file_url": body.file_url,
            "submitted_at": now
        }
        await db.db["assignment_submissions"].update_one({"id": existing["id"]}, {"$set": fields})
        updated = await db.db["assignment_submissions"].find_one({"id": existing["id"]})
        submission = AssignmentSubmission(**updated)
    else:
        sub_doc = {
            "id": str(uuid.uuid4()),
            "assignment_id": assignmentId,
            "student_id": current_user.id,
            "submission_text": body.submission_text,
            "file_name": body.file_name,
            "file_url": body.file_url,
            "submitted_at": now,
            "marks": None,
            "feedback": None,
            "graded_at": None
        }
        await db.db["assignment_submissions"].insert_one(sub_doc)
        submission = AssignmentSubmission(**sub_doc)
    
    # Audit log
    await log_activity(db, current_user.id, "submit_assignment", f"Submitted assignment: {assignment_doc.get('title')}")
    return send_response(status_code=status.HTTP_200_OK, success=True, data=SubmissionResponse.model_validate(submission))

@router.get("/assignments/{assignmentId}/submissions")
async def list_assignment_submissions(
    assignmentId: str,
    current_user: User = Depends(RoleChecker(["admin"])),
    db = Depends(get_db)
):
    """
    Lists all student submissions for a specific assignment.
    """
    cursor = db.db["assignment_submissions"].find({"assignment_id": assignmentId})
    submissions_docs = await cursor.to_list(length=1000)
    submissions = [AssignmentSubmission(**s) for s in submissions_docs]
    
    # Enrich submissions with student names
    enriched = []
    for s in submissions:
        student_doc = await db.db["users"].find_one({"id": s.student_id})
        student_name = student_doc.get("full_name") if student_doc else "Unknown Student"
        student_email = student_doc.get("email") if student_doc else ""
        
        enriched.append({
            "id": s.id,
            "assignment_id": s.assignment_id,
            "student_id": s.student_id,
            "student_name": student_name,
            "student_email": student_email,
            "submission_text": s.submission_text,
            "file_name": s.file_name,
            "file_url": s.file_url,
            "submitted_at": s.submitted_at,
            "marks": s.marks,
            "feedback": s.feedback,
            "graded_at": s.graded_at
        })
        
    return send_response(status_code=status.HTTP_200_OK, success=True, data=enriched)

@router.post("/submissions/{submissionId}/grade")
async def grade_submission(
    submissionId: str,
    body: SubmissionGradeRequest,
    current_user: User = Depends(RoleChecker(["admin"])),
    db = Depends(get_db)
):
    """
    Grades a student submission and alerts the student.
    """
    sub_doc = await db.db["assignment_submissions"].find_one({"id": submissionId})
    if not sub_doc:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Submission not found.")
        
    now = datetime.now(timezone.utc)
    fields = {
        "marks": body.marks,
        "feedback": body.feedback,
        "graded_at": now
    }
    await db.db["assignment_submissions"].update_one({"id": submissionId}, {"$set": fields})
    
    # Audit log
    await log_activity(db, current_user.id, "grade_assignment", f"Graded submission {submissionId} with marks: {body.marks}")
    
    # Fetch assignment details for notification
    assignment_doc = await db.db["assignments"].find_one({"id": sub_doc.get("assignment_id")})
    title = assignment_doc.get("title") if assignment_doc else "Assignment"
    max_marks = assignment_doc.get("max_marks", 100) if assignment_doc else 100
    
    # Notify student
    await create_notification(
        db=db,
        user_id=sub_doc.get("student_id"),
        title="Assignment Graded!",
        content=f"Your submission for '{title}' has been graded. Marks: {body.marks}/{max_marks}",
        notification_type="result"
    )
    
    return send_response(status_code=status.HTTP_200_OK, success=True, message="Submission graded successfully.")

def extract_filename(file_url: str) -> str:
    if not file_url:
        return ""
    normalized = file_url.replace("\\", "/")
    parts = [p for p in normalized.split("/") if p.strip()]
    return parts[-1] if parts else ""

@router.get("/assignments/{assignmentId}/file")
async def download_assignment_file(
    assignmentId: str,
    db = Depends(get_db)
):
    assignment = await db.db["assignments"].find_one({"id": assignmentId})
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")
        
    file_url = assignment.get("file_url")
    if not file_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No file attached to this assignment.")
        
    filename = extract_filename(file_url)
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../uploads", filename))
        
    if not os.path.exists(filepath):
        placeholder_filename = f"placeholder_{filename}.txt"
        placeholder_path = os.path.join(UPLOAD_DIR, placeholder_filename)
        if not os.path.exists(placeholder_path):
            with open(placeholder_path, "w", encoding="utf-8") as f:
                f.write(
                    f"EduTwin AI LMS - Ephemeral Storage Placeholder\n"
                    f"==================================================\n\n"
                    f"Original File Name: {filename}\n"
                    f"Assignment: {assignment.get('title') or 'LMS Assignment'}\n\n"
                    f"Notice:\n"
                    f"-------\n"
                    f"Because this backend is hosted on a free cloud tier (like Render) with ephemeral storage,\n"
                    f"uploaded files are automatically cleared whenever the container restarts or redeploys.\n\n"
                    f"To view the original file, please log in as an Admin and re-upload the document.\n"
                )
        filepath = placeholder_path
        download_name = f"placeholder_{assignment.get('title') or 'assignment'}.txt"
        media_type = "text/plain"
    else:
        download_name = assignment.get("title") + os.path.splitext(filename)[1]
        media_type, _ = mimetypes.guess_type(filepath)
        media_type = media_type or "application/octet-stream"
            
    return FileResponse(
        path=filepath,
        filename=download_name,
        media_type=media_type
    )

@router.get("/submissions/{submissionId}/file")
async def download_submission_file(
    submissionId: str,
    db = Depends(get_db)
):
    sub = await db.db["assignment_submissions"].find_one({"id": submissionId})
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found.")
        
    file_url = sub.get("file_url")
    if not file_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No file attached to this submission.")
        
    filename = extract_filename(file_url)
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../uploads", filename))
        
    if not os.path.exists(filepath):
        placeholder_filename = f"placeholder_{filename}.txt"
        placeholder_path = os.path.join(UPLOAD_DIR, placeholder_filename)
        if not os.path.exists(placeholder_path):
            with open(placeholder_path, "w", encoding="utf-8") as f:
                f.write(
                    f"EduTwin AI LMS - Ephemeral Storage Placeholder\n"
                    f"==================================================\n\n"
                    f"Original File Name: {sub.get('file_name') or filename}\n"
                    f"Student Name: {sub.get('student_name') or 'Student'}\n\n"
                    f"Notice:\n"
                    f"-------\n"
                    f"Because this backend is hosted on a free cloud tier (like Render) with ephemeral storage,\n"
                    f"uploaded files are automatically cleared whenever the container restarts or redeploys.\n\n"
                    f"Please contact the student to re-submit their work if you need to review the original document.\n"
                )
        filepath = placeholder_path
        download_name = f"placeholder_{sub.get('file_name') or filename}.txt"
        media_type = "text/plain"
    else:
        download_name = sub.get("file_name") or filename
        media_type, _ = mimetypes.guess_type(filepath)
        media_type = media_type or "application/octet-stream"
            
    return FileResponse(
        path=filepath,
        filename=download_name,
        media_type=media_type
    )
