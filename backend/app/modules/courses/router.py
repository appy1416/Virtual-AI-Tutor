from fastapi import APIRouter, Depends, status, Query
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.db.models.user import User
from app.modules.courses import service as course_service
from app.modules.courses import crud as course_crud
from app.modules.courses.schemas import CourseCreateRequest, CourseUpdateRequest
from app.utils.response import send_response

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.get("")
async def get_published_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    db = Depends(get_db)
):
    """
    Retrieves all published courses with pagination and filter criteria.
    """
    courses, total = await course_crud.list_courses(
        db=db,
        skip=skip,
        limit=limit,
        category=category,
        level=level,
        published_only=True
    )
    
    from app.modules.courses.schemas import CourseResponse
    items = [CourseResponse.model_validate(c) for c in courses]
    
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
        message="Published courses retrieved successfully."
    )

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_new_course(
    body: CourseCreateRequest,
    current_user: User = Depends(RoleChecker(["tutor", "admin"])),
    db = Depends(get_db)
):
    """
    Creates a new course blueprint. Restricted to tutors and admins.
    """
    course = await course_service.create_course(
        db=db,
        tutor_id=current_user.id,
        title=body.title,
        description=body.description,
        category=body.category,
        level=body.level,
        thumbnail_url=body.thumbnail_url,
        max_students=body.max_students
    )
    
    from app.modules.courses.schemas import CourseResponse
    return send_response(
        status_code=status.HTTP_201_CREATED,
        success=True,
        data=CourseResponse.model_validate(course),
        message="Course created successfully."
    )

@router.get("/my-courses")
async def list_enrolled_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    """
    Lists courses in which the authenticated student is currently enrolled.
    """
    res = await course_service.get_student_courses(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=res,
        message="Enrolled courses retrieved successfully."
    )

@router.get("/instructor")
async def list_tutor_created_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(RoleChecker(["tutor", "admin"])),
    db = Depends(get_db)
):
    """
    Lists course blueprints created by the authenticated instructor.
    """
    courses, total = await course_crud.get_tutor_courses(
        db=db,
        tutor_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    from app.modules.courses.schemas import CourseResponse
    items = [CourseResponse.model_validate(c) for c in courses]
    
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
        message="Instructor courses retrieved successfully."
    )

@router.get("/{courseId}")
async def get_course_details(
    courseId: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Retrieves full details of a course including nested lessons.
    """
    course_detail = await course_service.get_course_with_lessons(
        db=db,
        course_id=courseId,
        actor_role=current_user.role,
        actor_id=current_user.id
    )
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=course_detail,
        message="Course details retrieved successfully."
    )

@router.put("/{courseId}")
async def update_course_details(
    courseId: str,
    body: CourseUpdateRequest,
    current_user: User = Depends(RoleChecker(["tutor", "admin"])),
    db = Depends(get_db)
):
    """
    Modifies configuration attributes of a course. Requires course ownership or admin rights.
    """
    course = await course_crud.get_course(db, courseId)
    if not course:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Course not found.")
        
    if current_user.role != "admin" and course.tutor_id != current_user.id:
        return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="Access denied. You do not own this course.")
        
    fields = body.model_dump(exclude_unset=True)
    updated = await course_crud.update_course(db, courseId, **fields)
    
    from app.modules.courses.schemas import CourseResponse
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=CourseResponse.model_validate(updated),
        message="Course updated successfully."
    )

@router.delete("/{courseId}")
async def delete_course_blueprint(
    courseId: str,
    current_user: User = Depends(RoleChecker(["tutor", "admin"])),
    db = Depends(get_db)
):
    """
    Soft deletes a course record. Requires course ownership or admin rights.
    """
    course = await course_crud.get_course(db, courseId)
    if not course:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="Course not found.")
        
    if current_user.role != "admin" and course.tutor_id != current_user.id:
        return send_response(status_code=status.HTTP_403_FORBIDDEN, success=False, message="Access denied. You do not own this course.")
        
    await course_crud.delete_course(db, courseId)
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        message="Course soft-deleted successfully."
    )

@router.post("/{courseId}/publish")
async def publish_course_blueprint(
    courseId: str,
    current_user: User = Depends(RoleChecker(["tutor", "admin"])),
    db = Depends(get_db)
):
    """
    Publishes a course to make it visible to students. Requires course ownership or admin rights.
    """
    updated = await course_service.publish_course(
        db=db,
        course_id=courseId,
        actor_id=current_user.id,
        actor_role=current_user.role
    )
    
    from app.modules.courses.schemas import CourseResponse
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=CourseResponse.model_validate(updated),
        message="Course published successfully."
    )

@router.post("/{courseId}/enroll")
async def enroll_in_course(
    courseId: str,
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    """
    Enrolls the authenticated student into the designated course.
    """
    await course_service.enroll_student(db=db, user_id=current_user.id, course_id=courseId)
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        message="Enrolled in course successfully."
    )

@router.delete("/{courseId}/enroll")
async def unenroll_from_course(
    courseId: str,
    current_user: User = Depends(RoleChecker(["student"])),
    db = Depends(get_db)
):
    """
    Unenrolls the authenticated student from the designated course.
    """
    await course_service.unenroll_student(db=db, user_id=current_user.id, course_id=courseId)
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        message="Unenrolled from course successfully."
    )

@router.get("/instructor/{courseId}/dashboard")
async def get_course_dashboard(
    courseId: str,
    current_user: User = Depends(RoleChecker(["tutor", "admin"])),
    db = Depends(get_db)
):
    """
    Aggregates analytics telemetry for tutors. Requires ownership or admin permissions.
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
            message="Access denied. You do not own this course."
        )
        
    dashboard_data = await course_service.get_instructor_dashboard(db, current_user.id)
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=dashboard_data,
        message="Instructor analytics retrieved successfully."
    )
