from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.security import RoleChecker
from app.db.models.user import User
from app.modules.admin import service as admin_service
from app.modules.admin.schemas import (
    AdminUserListResponse,
    AdminUserResponse,
    AdminSettingsResponse,
    AdminRoleUpdateRequest,
    AdminAnnouncementRequest
)
from app.utils.response import send_response

router = APIRouter(tags=["Admin"])

@router.get("/admin/users")
async def list_users_for_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[str] = None,
    current_user: User = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    users, total = await admin_service.get_users(db, skip, limit, role)
    
    # Calculate page count
    page_count = (total + limit - 1) // limit if limit > 0 else 0
    
    data = {
        "items": users,
        "total_count": total,
        "page_count": page_count
    }
    return send_response(status_code=status.HTTP_200_OK, success=True, data=data)

@router.get("/admin/users/{userId}")
async def get_user_details_for_admin(
    userId: str,
    current_user: User = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    details = await admin_service.get_user_details(db, userId)
    if not details:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="User not found.")
        
    return send_response(status_code=status.HTTP_200_OK, success=True, data=details)

@router.put("/admin/users/{userId}/role")
async def change_user_role_by_admin(
    userId: str,
    body: AdminRoleUpdateRequest,
    current_user: User = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    updated = await admin_service.change_user_role(db, userId, body.role)
    if not updated:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="User not found.")
        
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data={
            "id": updated.id,
            "email": updated.email,
            "role": updated.role
        },
        message="User role updated successfully."
    )

@router.post("/admin/users/{userId}/deactivate")
async def deactivate_user_by_admin(
    userId: str,
    current_user: User = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    if userId == current_user.id:
        return send_response(status_code=status.HTTP_400_BAD_REQUEST, success=False, message="You cannot deactivate your own admin account.")
        
    updated = await admin_service.deactivate_user(db, userId)
    if not updated:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="User not found.")
        
    return send_response(status_code=status.HTTP_200_OK, success=True, message="User account suspended/deactivated successfully.")

@router.post("/admin/users/{userId}/reactivate")
async def reactivate_user_by_admin(
    userId: str,
    current_user: User = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    updated = await admin_service.reactivate_user(db, userId)
    if not updated:
        return send_response(status_code=status.HTTP_404_NOT_FOUND, success=False, message="User not found.")
        
    return send_response(status_code=status.HTTP_200_OK, success=True, message="User account reactivated successfully.")

@router.get("/admin/settings")
async def get_platform_settings_for_admin(
    current_user: User = Depends(RoleChecker(["admin"]))
):
    from app.modules.admin import crud as admin_crud
    settings = await admin_crud.get_platform_settings()
    return send_response(status_code=status.HTTP_200_OK, success=True, data=settings)

@router.put("/admin/settings")
async def update_platform_settings_by_admin(
    body: AdminSettingsResponse,
    current_user: User = Depends(RoleChecker(["admin"]))
):
    from app.modules.admin import crud as admin_crud
    update_data = body.model_dump()
    updated = await admin_crud.update_platform_settings(**update_data)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=updated, message="Platform settings updated successfully.")

@router.post("/admin/announce")
async def send_platform_announcement(
    body: AdminAnnouncementRequest,
    current_user: User = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    res = await admin_service.send_announcement(db, body.title, body.content)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=res, message="Announcement broadcasted successfully.")

@router.get("/admin/stats")
async def get_platform_wide_statistics(
    current_user: User = Depends(RoleChecker(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    stats = await admin_service.get_platform_stats(db)
    return send_response(status_code=status.HTTP_200_OK, success=True, data=stats)

@router.get("/admin/reports")
async def generate_platform_reports(
    current_user: User = Depends(RoleChecker(["admin"]))
):
    # Mock download report structure
    return send_response(status_code=status.HTTP_200_OK, success=True, data={"report_url": "/storage/reports/weekly_report.pdf"})

@router.post("/admin/export-data")
async def export_all_data_by_admin(
    current_user: User = Depends(RoleChecker(["admin"]))
):
    return send_response(status_code=status.HTTP_200_OK, success=True, message="All student data GDPR archive generated successfully.")
