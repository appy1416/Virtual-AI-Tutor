from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.db.models.user import User
from app.modules.users import service, crud
from app.modules.users.schemas import UserUpdateRequest, PasswordChangeRequest
from app.utils.response import send_response

router = APIRouter(prefix="/users", tags=["Users & Profiles"])

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile details.
    """
    from app.modules.users.schemas import UserResponse
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=UserResponse.model_validate(current_user),
        message="Profile retrieved successfully."
    )

@router.put("/me")
async def update_me(
    body: UserUpdateRequest, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates profile details of the active user.
    """
    updated_profile = await service.update_profile(
        db=db,
        user_id=current_user.id,
        full_name=body.full_name,
        bio=body.bio,
        preferences=body.preferences
    )
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=updated_profile,
        message="Profile updated successfully."
    )

@router.post("/avatar")
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Uploads and saves a profile picture for the active user.
    """
    updated_profile = await service.upload_avatar(
        db=db,
        user_id=current_user.id,
        file=file
    )
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=updated_profile,
        message="Avatar uploaded successfully."
    )

@router.post("/change-password")
async def change_my_password(
    body: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Changes the authenticated user's password.
    """
    await service.change_password(
        db=db,
        user_id=current_user.id,
        old_password=body.old_password,
        new_password=body.new_password
    )
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        message="Password updated successfully."
    )

@router.get("/{userId}")
async def get_user_by_admin(
    userId: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(RoleChecker(["admin"]))
):
    """
    Retrieve any user's profile details. Restricted to administrator accounts.
    """
    profile = await service.get_profile(db=db, user_id=userId)
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=profile,
        message="User profile retrieved successfully (Admin view)."
    )

@router.delete("/{userId}")
async def delete_user_by_admin(
    userId: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(RoleChecker(["admin"]))
):
    """
    Soft-delete a user record. Restricted to administrator accounts.
    """
    deleted = await crud.delete_user(db=db, user_id=userId)
    if not deleted:
        return send_response(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message="User not found or already deleted."
        )
        
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        message="User record soft-deleted successfully."
    )

@router.get("")
async def list_users_by_admin(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(RoleChecker(["admin"]))
):
    """
    List all active users. Restricted to administrator accounts.
    """
    users = await crud.list_users(db=db, skip=skip, limit=limit)
    from app.modules.users.schemas import UserResponse
    data = [UserResponse.model_validate(u) for u in users]
    return send_response(
        status_code=status.HTTP_200_OK,
        success=True,
        data=data,
        message="Users list retrieved successfully."
    )
