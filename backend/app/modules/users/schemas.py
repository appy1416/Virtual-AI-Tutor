from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    created_at: datetime
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    preferences: Dict[str, Any] = {}

    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    preferences: Optional[Dict[str, Any]] = None

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str
