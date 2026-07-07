import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

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
        data={"file_url": file_url, "file_name": file.filename},
        message="File uploaded successfully."
    )

@router.get("/assignments")
async def list_assignments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all assignments. Students only see published ones.
    """
    stmt = select(Assignment)
    if current_user.role == "student":
        stmt = stmt.where(Assignment.is_published == True)
    
    res = await db.execute(stmt)
    assignments = res.scalars().all()
    
    # Enrich response with student submission state if they are student
    enriched = []
    for a in assignments:
        sub_status = "unsubmitted"
        marks = None
        feedback = None
        
        if current_user.role == "student":
            sub_stmt = select(AssignmentSubmission).where(
                AssignmentSubmission.assignment_id == a.id,
                AssignmentSubmission.student_id == current_user.id
            )
            sub_res = await db.execute(sub_stmt)
            sub = sub_res.scalars().first()
            if sub:
                sub_status = "submitted" if sub.marks is None else "graded"
                marks = sub.marks
                feedback = sub.feedback
                
        enriched.append({
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "deadline": a.deadline,
            "file_url": a.file_url,
            "is_published": a.is_published,
            "created_at": a.created_at,
            "updated_at": a.updated_at,
            "submission_status": sub_status,
            "marks": marks,
            "feedback": feedback
        })
        
    return send_response(status_code=status.HTTP_200_OK, success=True, data=enriched)

@router.post("/assignments", status_code=status.HTTP_201_CREATED)
async def create_assignment(
    body: AssignmentCreate,
    current_user: User = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new assignment and dispatches notification to all users.
    """
    assignment = Assignment(
        title=body.title,
        description=body.description,
        deadline=body.deadline,
        file_url=body.file_url,
        is_published=body.is_published
    )
    db.add(assignment)
    await db.flush()
    
    # Audit log
    await log_activity(db, current_user.id, "create_assignment", f"Created assignment: {body.title}")
    
    # Broadcast notification to all students if published
    if body.is_published:
        # We can find all students or broadcast globally (user_id = None)
        await create_notification(
            db=db,
            user_id=None,
            title="New Assignment Released!",
            content=f"Assignment '{body.title}' is now available. Deadline: {body.deadline.strftime('%Y-%m-%d %H:%M')}",
            notification_type="assignment"
        )
        
    await db.commit()
    return send_response(status_code=status.HTTP_201_CREATED, success=True, data=AssignmentResponse.model_validate(assignment))

@router.put("/assignments/{assignmentId}")
async def update_assignment(
    assignmentId: str,
    body: AssignmentUpdate,
    current_user: User = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Modifies an existing assignment.
    """
    stmt = select(Assignment).where(Assignment.id == assignmentId)
    res = await db.execute(stmt)
    assignment = res.scalars().first()
    if not assignment:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Assignment not found.")
        
    update_data = body.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(assignment, k, v)
        
    db.add(assignment)
    await db.commit()
    return send_response(status_code=status.HTTP_200_OK, success=True, data=AssignmentResponse.model_validate(assignment))

@router.delete("/assignments/{assignmentId}")
async def delete_assignment(
    assignmentId: str,
    current_user: User = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes an assignment record.
    """
    stmt = select(Assignment).where(Assignment.id == assignmentId)
    res = await db.execute(stmt)
    assignment = res.scalars().first()
    if not assignment:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Assignment not found.")
        
    await db.delete(assignment)
    await db.commit()
    return send_response(status_code=status.HTTP_200_OK, success=True, message="Assignment deleted successfully.")

@router.post("/assignments/{assignmentId}/submit")
async def submit_assignment(
    assignmentId: str,
    body: SubmissionCreate,
    current_user: User = Depends(RoleChecker(["student"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Submits student work for an assignment. Overwrites previous submission if exists.
    """
    # Verify assignment exists
    as_stmt = select(Assignment).where(Assignment.id == assignmentId)
    as_res = await db.execute(as_stmt)
    assignment = as_res.scalars().first()
    if not assignment:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Assignment not found.")
        
    # Check if already submitted
    stmt = select(AssignmentSubmission).where(
        AssignmentSubmission.assignment_id == assignmentId,
        AssignmentSubmission.student_id == current_user.id
    )
    res = await db.execute(stmt)
    submission = res.scalars().first()
    
    if submission:
        submission.submission_text = body.submission_text
        submission.file_name = body.file_name
        submission.file_url = body.file_url
        submission.submitted_at = datetime.now(timezone.utc)
    else:
        submission = AssignmentSubmission(
            assignment_id=assignmentId,
            student_id=current_user.id,
            submission_text=body.submission_text,
            file_name=body.file_name,
            file_url=body.file_url
        )
    
    db.add(submission)
    
    # Audit log
    await log_activity(db, current_user.id, "submit_assignment", f"Submitted assignment: {assignment.title}")
    
    await db.commit()
    return send_response(status_code=status.HTTP_200_OK, success=True, data=SubmissionResponse.model_validate(submission))

@router.get("/assignments/{assignmentId}/submissions")
async def list_assignment_submissions(
    assignmentId: str,
    current_user: User = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all student submissions for a specific assignment.
    """
    stmt = select(AssignmentSubmission).where(AssignmentSubmission.assignment_id == assignmentId)
    res = await db.execute(stmt)
    submissions = res.scalars().all()
    
    # Enrich submissions with student names
    enriched = []
    for s in submissions:
        student_stmt = select(User).where(User.id == s.student_id)
        student_res = await db.execute(student_stmt)
        student = student_res.scalars().first()
        
        enriched.append({
            "id": s.id,
            "assignment_id": s.assignment_id,
            "student_id": s.student_id,
            "student_name": student.full_name if student else "Unknown Student",
            "student_email": student.email if student else "",
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
    db: AsyncSession = Depends(get_db)
):
    """
    Grades a student submission and alerts the student.
    """
    stmt = select(AssignmentSubmission).where(AssignmentSubmission.id == submissionId)
    res = await db.execute(stmt)
    sub = res.scalars().first()
    if not sub:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Submission not found.")
        
    sub.marks = body.marks
    sub.feedback = body.feedback
    sub.graded_at = datetime.now(timezone.utc)
    db.add(sub)
    
    # Audit log
    await log_activity(db, current_user.id, "grade_assignment", f"Graded submission {submissionId} with marks: {body.marks}")
    
    # Fetch assignment details for notification
    as_stmt = select(Assignment).where(Assignment.id == sub.assignment_id)
    as_res = await db.execute(as_stmt)
    assignment = as_res.scalars().first()
    
    # Notify student
    await create_notification(
        db=db,
        user_id=sub.student_id,
        title="Assignment Graded!",
        content=f"Your submission for '{assignment.title if assignment else 'Assignment'}' has been graded. Marks: {body.marks}/100",
        notification_type="result"
    )
    
    await db.commit()
    return send_response(status_code=status.HTTP_200_OK, success=True, message="Submission graded successfully.")
