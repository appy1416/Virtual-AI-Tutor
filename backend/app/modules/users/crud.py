from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func

from app.db.models.user import User

async def create_user(
    db: AsyncSession, 
    email: str, 
    hashed_password: str, 
    full_name: str, 
    role: str = "student"
) -> User:
    """
    Creates and persists a new User model.
    """
    db_user = User(
        email=email,
        password_hash=hashed_password,
        full_name=full_name,
        role=role
    )
    db.add(db_user)
    await db.flush() # Flushes changes to get the auto-generated UUID
    return db_user

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Finds a user by email address. Ignores soft-deleted accounts.
    """
    result = await db.execute(
        select(User).where(User.email == email.lower(), User.deleted_at == None)
    )
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    Finds a user by UUID. Ignores soft-deleted accounts.
    """
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at == None)
    )
    return result.scalars().first()

async def update_user(db: AsyncSession, user_id: str, **fields) -> Optional[User]:
    """
    Updates designated fields on a user record.
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
        
    for key, value in fields.items():
        if hasattr(user, key):
            setattr(user, key, value)
            
    user.updated_at = datetime.now(timezone.utc)
    db.add(user)
    await db.flush()
    return user

async def delete_user(db: AsyncSession, user_id: str) -> bool:
    """
    Performs soft deletion of a user record by assigning `deleted_at`.
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
        
    user.deleted_at = datetime.now(timezone.utc)
    db.add(user)
    await db.flush()
    return True

async def list_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Lists users with offset/limit pagination parameters. Excludes deleted users.
    """
    result = await db.execute(
        select(User)
        .where(User.deleted_at == None)
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    return list(result.scalars().all())

async def get_user_by_refresh_token(db: AsyncSession, token: str) -> Optional[User]:
    """
    Decodes refresh token and retrieves the corresponding User.
    """
    from app.core.security import verify_token
    try:
        payload = verify_token(token, "refresh")
        user_id = payload.get("sub")
        if not user_id:
            return None
        return await get_user_by_id(db, user_id)
    except Exception:
        return None
