from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any
from app.db.models.user import User

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
    db,
    skip: int = 0,
    limit: int = 50,
    role: Optional[str] = None
) -> Tuple[List[User], int]:
    query = {}
    if role:
        query["role"] = role
        
    total = await db.db["users"].count_documents(query)
    cursor = db.db["users"].find(query).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [User(**d) for d in docs], total

async def get_user_admin_view(db, user_id: str) -> Optional[User]:
    doc = await db.db["users"].find_one({"id": user_id})
    return User(**doc) if doc else None

async def update_user_role(db, user_id: str, new_role: str) -> Optional[User]:
    await db.db["users"].update_one({"id": user_id}, {"$set": {"role": new_role, "updated_at": datetime.now(timezone.utc)}})
    updated = await db.db["users"].find_one({"id": user_id})
    return User(**updated) if updated else None

async def deactivate_user(db, user_id: str) -> Optional[User]:
    await db.db["users"].update_one(
        {"id": user_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)}}
    )
    updated = await db.db["users"].find_one({"id": user_id})
    return User(**updated) if updated else None

async def reactivate_user(db, user_id: str) -> Optional[User]:
    await db.db["users"].update_one(
        {"id": user_id},
        {"$set": {"deleted_at": None, "updated_at": datetime.now(timezone.utc)}}
    )
    updated = await db.db["users"].find_one({"id": user_id})
    return User(**updated) if updated else None

async def get_platform_settings() -> Dict[str, Any]:
    return _PLATFORM_SETTINGS

async def update_platform_settings(**fields) -> Dict[str, Any]:
    global _PLATFORM_SETTINGS
    for k, v in fields.items():
        if k in _PLATFORM_SETTINGS:
            _PLATFORM_SETTINGS[k] = v
    return _PLATFORM_SETTINGS
