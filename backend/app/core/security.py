from datetime import datetime, timedelta, timezone
from typing import Optional, List, Union
import jwt
import bcrypt
from fastapi import Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.database import get_db
from app.db.models.user import User
from app.core.exceptions import TokenExpired, TokenInvalid, RoleNotAllowed, UserNotFound

security_scheme = HTTPBearer()

def hash_password(password: str) -> str:
    """
    Hashes a plain text password using bcrypt.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies that a plain text password matches its bcrypt hash.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), 
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT access token containing subject data and expiration time.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_type = to_encode.get("type", "access")
    to_encode.update({"exp": expire, "type": token_type})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """
    Creates a long-lived JWT refresh token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str, expected_type: str = "access") -> dict:
    """
    Verifies JWT token integrity and validates payload parameters.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        if token_type != expected_type:
            raise TokenInvalid(f"Token type mismatch. Expected: {expected_type}, Found: {token_type}")
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpired()
    except jwt.InvalidTokenError:
        raise TokenInvalid()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db = Depends(get_db)
) -> User:
    """
    FastAPI dependency that extracts JWT from request header, verifies it,
    and returns the active User object.
    """
    token = credentials.credentials
    payload = verify_token(token, "access")
    user_id = payload.get("sub")
    if not user_id:
        raise TokenInvalid("Subject (sub) claim missing from token.")
        
    user_doc = await db.db["users"].find_one({"id": user_id, "deleted_at": None})
    if not user_doc:
        raise UserNotFound("Authenticated user not found or has been deleted.")
        
    return User(**user_doc)

class RoleChecker:
    """
    Dependency injector for Role-Based Access Control (RBAC).
    Usage: Depends(RoleChecker(["admin"]))
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise RoleNotAllowed(f"You do not have permission to access this resource. Required: one of {self.allowed_roles}. Found: {current_user.role}")
        return current_user
