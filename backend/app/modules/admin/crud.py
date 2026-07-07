from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any

from app.db.models.user import User

# In-memory settings for platform control
_PLATFORM_SETTINGS = {
    "platform_name": "EduTwin AI",
    "max_file_size": 52428800,  # 50MB
    "maintenance_mode": False,
    "features_enabled": {
        "voice_tutor": True,
        "ai_chat": True,
        "analytics": True
    }
}

async def list_all_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    role: Optional[str] = None
) -> Tuple[List[User], int]:
    conditions = []
    if role:
        conditions.append(User.role == role)
        
    stmt_count = select(func.count(User.id))
    if conditions:
        stmt_count = stmt_count.where(and_(*conditions))
    res_count = await db.execute(stmt_count)
    total = res_count.scalar() or 0

    stmt = select(User)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all()), total

async def get_user_admin_view(db: AsyncSession, user_id: str) -> Optional[User]:
    # Admin can view even deactivated users
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    return res.scalars().first()

async def update_user_role(db: AsyncSession, user_id: str, new_role: str) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        return None
    user.role = new_role
    db.add(user)
    await db.flush()
    return user

async def deactivate_user(db: AsyncSession, user_id: str) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        return None
    user.deleted_at = datetime.now(timezone.utc)
    db.add(user)
    await db.flush()
    return user

async def reactivate_user(db: AsyncSession, user_id: str) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        return None
    user.deleted_at = None
    db.add(user)
    await db.flush()
    return user

async def get_platform_settings() -> Dict[str, Any]:
    return _PLATFORM_SETTINGS

async def update_platform_settings(**fields) -> Dict[str, Any]:
    global _PLATFORM_SETTINGS
    for k, v in fields.items():
        if k in _PLATFORM_SETTINGS:
            _PLATFORM_SETTINGS[k] = v
    return _PLATFORM_SETTINGS
