from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class AdminUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    created_at: datetime
    courses_enrolled: int
    last_login: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True

class AdminUserListResponse(BaseModel):
    items: List[AdminUserResponse] = []
    total_count: int
    page_count: int

class AdminSettingsResponse(BaseModel):
    platform_name: str
    max_file_size: int
    maintenance_mode: bool
    features_enabled: Dict[str, bool] = {}

class AdminRoleUpdateRequest(BaseModel):
    role: str

class AdminAnnouncementRequest(BaseModel):
    title: str
    content: str
