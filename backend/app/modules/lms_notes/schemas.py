from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class LMSNoteCreate(BaseModel):
    title: str
    description: str
    subject: str
    file_name: str
    file_url: str
    file_type: str

class LMSNoteResponse(BaseModel):
    id: str
    title: str
    description: str
    subject: str
    file_name: str
    file_url: str
    file_type: str
    uploaded_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
