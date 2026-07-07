import os
import uuid
import logging
from typing import Optional, Dict, Any
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserNotFound, InvalidCredentials
from app.core.security import verify_password, hash_password
from app.modules.users import crud
from app.modules.users.schemas import UserResponse
from app.utils.validators import validate_password, validate_full_name

logger = logging.getLogger("edutwin.users")

# Setup uploads directory path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads", "avatars")

async def get_profile(db: AsyncSession, user_id: str) -> UserResponse:
    """
    Retrieves user profile details by ID. Raises 404 if user doesn't exist.
    """
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise UserNotFound()
    return UserResponse.model_validate(user)

async def update_profile(
    db: AsyncSession, 
    user_id: str, 
    full_name: Optional[str] = None, 
    bio: Optional[str] = None, 
    preferences: Optional[Dict[str, Any]] = None
) -> UserResponse:
    """
    Updates the customizable profile fields of a user.
    """
    # Verify user exists
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise UserNotFound()
        
    update_data = {}
    if full_name is not None:
        validate_full_name(full_name)
        update_data["full_name"] = full_name
    if bio is not None:
        update_data["bio"] = bio
    if preferences is not None:
        # Merge or replace preferences dictionary
        current_prefs = user.preferences or {}
        merged_prefs = {**current_prefs, **preferences}
        update_data["preferences"] = merged_prefs
        
    updated_user = await crud.update_user(db, user_id, **update_data)
    logger.info("Updated profile for user ID: %s", user_id)
    return UserResponse.model_validate(updated_user)

async def upload_avatar(db: AsyncSession, user_id: str, file: UploadFile) -> UserResponse:
    """
    Saves an uploaded image locally under static file uploads and records the URL.
    """
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise UserNotFound()
        
    # Ensure uploads folder exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Generate unique file extension preservation filename
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".png"
    # Basic sanitize extension
    if file_ext.lower() not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        file_ext = ".png"
        
    filename = f"{user_id}_{uuid.uuid4().hex}{file_ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Save the file
    try:
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error("Failed to write avatar file: %s", e)
        raise RuntimeError("Failed to save avatar image file.")
        
    # Record local static URL path
    avatar_url = f"/static/uploads/avatars/{filename}"
    updated_user = await crud.update_user(db, user_id, profile_picture_url=avatar_url)
    
    logger.info("Uploaded avatar for user ID: %s. Saved path: %s", user_id, avatar_url)
    return UserResponse.model_validate(updated_user)

async def change_password(
    db: AsyncSession, 
    user_id: str, 
    old_password: str, 
    new_password: str
) -> None:
    """
    Verifies old password and assigns a newly hashed password.
    """
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise UserNotFound()
        
    # Check old password match
    if not verify_password(old_password, user.password_hash):
        logger.warning("Password change attempt failed: invalid current password for user ID: %s", user_id)
        raise InvalidCredentials("Current password provided is incorrect.")
        
    # Validate and hash new password
    validate_password(new_password)
    hashed_pwd = hash_password(new_password)
    
    await crud.update_user(db, user_id, password_hash=hashed_pwd)
    logger.info("Successfully updated password for user ID: %s", user_id)
