from datetime import datetime, timezone
import uuid
from typing import Optional, List
from app.db.models.user import User

async def create_user(
    db, 
    email: str, 
    hashed_password: str, 
    full_name: str, 
    role: str = "student"
) -> User:
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    user_doc = {
        "id": user_id,
        "email": email.lower(),
        "password_hash": hashed_password,
        "full_name": full_name,
        "role": role,
        "profile_picture_url": None,
        "bio": None,
        "preferences": {},
        "points": 0,
        "badges": [],
        "streak_days": 0,
        "last_activity_date": None,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None
    }
    await db.db["users"].insert_one(user_doc)
    return User(**user_doc)

async def get_user_by_email(db, email: str) -> Optional[User]:
    doc = await db.db["users"].find_one({"email": email.lower(), "deleted_at": None})
    return User(**doc) if doc else None

async def get_user_by_id(db, user_id: str) -> Optional[User]:
    doc = await db.db["users"].find_one({"id": user_id, "deleted_at": None})
    return User(**doc) if doc else None

async def update_user(db, user_id: str, **fields) -> Optional[User]:
    doc = await db.db["users"].find_one({"id": user_id, "deleted_at": None})
    if not doc:
        return None
    fields["updated_at"] = datetime.now(timezone.utc)
    await db.db["users"].update_one({"id": user_id}, {"$set": fields})
    updated_doc = await db.db["users"].find_one({"id": user_id})
    return User(**updated_doc) if updated_doc else None

async def delete_user(db, user_id: str) -> bool:
    res = await db.db["users"].update_one(
        {"id": user_id, "deleted_at": None},
        {"$set": {"deleted_at": datetime.now(timezone.utc)}}
    )
    return res.modified_count > 0

async def list_users(db, skip: int = 0, limit: int = 100) -> List[User]:
    cursor = db.db["users"].find({"deleted_at": None}).sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [User(**d) for d in docs]

async def get_user_by_refresh_token(db, token: str) -> Optional[User]:
    from app.core.security import verify_token
    try:
        payload = verify_token(token, "refresh")
        user_id = payload.get("sub")
        if not user_id:
            return None
        return await get_user_by_id(db, user_id)
    except Exception:
        return None
