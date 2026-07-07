import logging
from datetime import timedelta, datetime, timezone
from typing import Tuple

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.core.cache import token_blacklist
from app.core.exceptions import (
    InvalidCredentials,
    UserAlreadyExists,
    UserNotFound,
    TokenInvalid,
    TokenExpired
)
from app.modules.users import crud
from app.modules.users.schemas import UserResponse
from app.utils.validators import validate_email, validate_password, validate_full_name
from app.utils.lms_helpers import log_activity

logger = logging.getLogger("edutwin.auth")

async def register_user(
    db, 
    email: str, 
    password: str, 
    full_name: str,
    role: str = "student"
) -> UserResponse:
    """
    Registers a new student or admin. Validates input formatting and checks email uniqueness.
    """
    email = validate_email(email)
    validate_password(password)
    full_name = validate_full_name(full_name)
    
    existing_user = await crud.get_user_by_email(db, email)
    if existing_user:
        logger.warning("Registration attempt failed: email %s already in use", email)
        raise UserAlreadyExists()
        
    hashed_pwd = hash_password(password)
    new_user = await crud.create_user(
        db=db, 
        email=email, 
        hashed_password=hashed_pwd, 
        full_name=full_name,
        role=role
    )
    
    logger.info("Successfully registered new user: %s (role: %s)", email, role)
    await log_activity(db, new_user.id, "register", f"User registered: {email}")
    return UserResponse.model_validate(new_user)

async def login_user(
    db, 
    email: str, 
    password: str
) -> Tuple[str, str, UserResponse]:
    """
    Validates user credentials, issues access/refresh tokens, and returns user profile.
    """
    email = email.strip().lower()
    user = await crud.get_user_by_email(db, email)
    
    if not user or not verify_password(password, user.password_hash):
        logger.warning("Failed login attempt for email: %s", email)
        raise InvalidCredentials()
        
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    logger.info("Successfully authenticated user: %s", email)
    await log_activity(db, user.id, "login", f"User logged in: {email}")
    return access_token, refresh_token, UserResponse.model_validate(user)

async def refresh_access_token(db, refresh_token: str) -> str:
    """
    Decodes a refresh token and issues a new access token if valid.
    """
    user = await crud.get_user_by_refresh_token(db, refresh_token)
    if not user:
        logger.warning("Token refresh failed: invalid or expired refresh token.")
        raise TokenInvalid("Invalid refresh token or user not found.")
        
    new_access_token = create_access_token(data={"sub": user.id, "role": user.role})
    logger.info("Issued new access token for user ID: %s via refresh token", user.id)
    return new_access_token

async def logout_user(token: str) -> None:
    """
    Revokes the active access token by adding it to the blacklist.
    """
    try:
        payload = verify_token(token, "access")
        exp = payload.get("exp")
        now = datetime.now(timezone.utc).timestamp()
        seconds_remaining = int(exp - now) if exp else 86400
        
        if seconds_remaining > 0:
            token_blacklist.blacklist_token(token, seconds_remaining)
            logger.info("Access token blacklisted successfully on logout.")
    except Exception as e:
        logger.error("Error during token blacklisting: %s", e)

async def initiate_password_reset(db, email: str) -> None:
    """
    Generates a secure password reset link and writes it to logs.
    """
    email = email.strip().lower()
    user = await crud.get_user_by_email(db, email)
    if not user:
        logger.warning("Password reset requested for non-existent email: %s", email)
        return
        
    reset_payload = {
        "sub": user.id,
        "email": user.email,
        "type": "reset",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
    }
    reset_token = create_access_token(data=reset_payload, expires_delta=timedelta(minutes=15))
    
    reset_link = f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}"
    
    logger.info("--- PASSWORD RESET LINK GENERATED ---")
    logger.info("Sent to: %s", email)
    logger.info("Link: %s", reset_link)
    logger.info("-------------------------------------")

async def reset_password(db, token: str, new_password: str) -> None:
    """
    Validates a password reset token and updates the user's password.
    """
    try:
        payload = verify_token(token, "reset")
    except Exception:
        raise TokenInvalid("Invalid or expired password reset token.")
        
    user_id = payload.get("sub")
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise UserNotFound()
        
    validate_password(new_password)
    hashed_pwd = hash_password(new_password)
    
    await crud.update_user(db, user_id, password_hash=hashed_pwd)
    logger.info("Successfully reset password for user ID: %s", user_id)
