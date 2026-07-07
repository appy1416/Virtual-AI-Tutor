from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.db.models.user import User
from app.modules.lessons import service as lesson_service
from app.modules.lessons import crud as lesson_crud
from app.modules.courses import crud as course_crud
from app.modules.lessons.schemas import LessonCreateRequest, LessonUpdateRequest, LessonReorderRequest
from app.utils.response import send_response

router = APIRouter(tags=["Lessons"])

@router.get("/courses/{courseId}/lessons")
async def list_course_lessons(
    courseId: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists preview elements of lessons for a course, sorted by sequence_order.
    """
    lessons, total = await lesson_crud.list_lessons(db=db, course_id=courseId, skip=skip, limit=limit)
    
    from app.modules.lessons.schemas import LessonResponse
    items = [LessonResponse.model_validate(l) for l in lessons]
    
    data = {
        "items": items,
        "total_count": total,
        "page_count": (total + limit - 1) // limit if limit > 0 else 0,
        "current_page": (skip // limit) + 1 if limit > 0 else 1
    }
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=data,
        message="Lessons retrieved successfully."
    )

@router.post("/courses/{courseId}/lessons", status_code=status.HTTP_201_CREATED)
async def create_new_lesson(
    courseId: str,
    body: LessonCreateRequest,
    current_user: User = Depends(RoleChecker(["tutor", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new lesson inside a course. Requires course ownership or admin rights.
    """
    lesson = await lesson_service.create_lesson(
        db=db,
        course_id=courseId,
        tutor_id=current_user.id,
        tutor_role=current_user.role,
        title=body.title,
        description=body.description,
        content=body.content,
        learning_objectives=body.learning_objectives,
        estimated_duration_minutes=body.estimated_duration_minutes,
        difficulty_score=body.difficulty_score
    )
    
    from app.modules.lessons.schemas import LessonDetailResponse
    return send_response(
        status_code=status.HTTP_201_CREATED,
        success=True,
        data=LessonDetailResponse.model_validate(lesson),
        message="Lesson created successfully."
    )

@router.get("/lessons/{lessonId}")
async def get_lesson_details(
    lessonId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves full details of a specific lesson, including large markdown content blocks.
    """
    lesson = await lesson_service.get_lesson_full(
        db=db,
        lesson_id=lessonId,
        actor_id=current_user.id,
        actor_role=current_user.role
    )
    
    from app.modules.lessons.schemas import LessonDetailResponse
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=LessonDetailResponse.model_validate(lesson),
        message="Lesson details retrieved successfully."
    )

@router.put("/lessons/{lessonId}")
async def update_lesson_details(
    lessonId: str,
    body: LessonUpdateRequest,
    current_user: User = Depends(RoleChecker(["tutor", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Modifies configuration or content parameters of a lesson. Requires course ownership or admin rights.
    """
    # Verify ownership
    lesson = await lesson_crud.get_lesson(db, lessonId)
    if not lesson:
        return send_response(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message="Lesson not found."
        )
        
    course = await course_crud.get_course(db, lesson.course_id)
    if not course:
         return send_response(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message="Course associated with lesson not found."
        )
        
    if current_user.role != "admin" and course.tutor_id != current_user.id:
        return send_response(
            status_code=status.HTTP_403_FORBIDDEN,
            success=False,
            message="You do not own the parent course of this lesson."
        )
        
    update_fields = body.model_dump(exclude_unset=True)
    updated = await lesson_crud.update_lesson(db, lessonId, **update_fields)
    
    from app.modules.lessons.schemas import LessonDetailResponse
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=LessonDetailResponse.model_validate(updated),
        message="Lesson updated successfully."
    )

@router.delete("/lessons/{lessonId}")
async def delete_lesson_record(
    lessonId: str,
    current_user: User = Depends(RoleChecker(["tutor", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft-deletes a lesson. Requires course ownership or admin rights.
    """
    lesson = await lesson_crud.get_lesson(db, lessonId)
    if not lesson:
        return send_response(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message="Lesson not found."
        )
        
    course = await course_crud.get_course(db, lesson.course_id)
    if not course:
         return send_response(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message="Course associated with lesson not found."
        )
        
    if current_user.role != "admin" and course.tutor_id != current_user.id:
        return send_response(
            status_code=status.HTTP_403_FORBIDDEN,
            success=False,
            message="You do not own the parent course of this lesson."
        )
        
    await lesson_crud.delete_lesson(db, lessonId)
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        message="Lesson soft-deleted successfully."
    )

@router.post("/lessons/{lessonId}/complete")
async def mark_lesson_as_complete(
    lessonId: str,
    current_user: User = Depends(RoleChecker(["student"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Logs lesson completion for the authenticated student.
    """
    await lesson_service.complete_lesson(db=db, user_id=current_user.id, lesson_id=lessonId)
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        message="Lesson completed successfully."
    )

@router.put("/lessons/{courseId}/reorder")
async def reorder_course_lessons(
    courseId: str,
    body: LessonReorderRequest,
    current_user: User = Depends(RoleChecker(["tutor", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Re-orders sequence allocations for all lessons within a course. Requires course ownership or admin rights.
    """
    course = await course_crud.get_course(db, courseId)
    if not course:
        return send_response(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message="Course not found."
        )
        
    if current_user.role != "admin" and course.tutor_id != current_user.id:
        return send_response(
            status_code=status.HTTP_403_FORBIDDEN,
            success=False,
            message="You do not own this course to reorder lessons."
        )
        
    await lesson_crud.reorder_lessons(db=db, course_id=courseId, lesson_order_list=body.lesson_order_list)
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        message="Lessons reordered successfully."
    )
