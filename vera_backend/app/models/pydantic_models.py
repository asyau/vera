from pydantic import BaseModel, validator
from typing import Optional, Union
from datetime import datetime, date

class TimelineBase(BaseModel):
    createdAt: datetime
    sentAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None

class UserBase(BaseModel):
    id: str
    name: str
    email: str
    role: str
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    company_name: Optional[str] = None

class TaskCreate(BaseModel):
    name: str
    assignedTo: str
    dueDate: Optional[str] = None
    status: str
    description: str
    originalPrompt: str

    @validator('dueDate')
    def parse_due_date(cls, v):
        if not v:  # If empty string or None
            return None
        try:
            return datetime.fromisoformat(v)
        except ValueError:
            return None

class TaskResponse(BaseModel):
    id: str
    name: str
    assignedTo: str
    assignedToName: Optional[str] = None
    dueDate: Optional[datetime] = None
    status: str
    description: str
    originalPrompt: str
    timeline: TimelineBase
    assigned_user: Optional[UserBase] = None

    class Config:
        from_attributes = True 