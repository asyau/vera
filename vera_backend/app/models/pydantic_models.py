from pydantic import BaseModel, validator
from typing import Optional, Union
from datetime import datetime, date

class TimelineBase(BaseModel):
    createdAt: datetime
    sentAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None

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
    dueDate: Optional[datetime] = None
    status: str
    description: str
    originalPrompt: str
    timeline: TimelineBase

    class Config:
        from_attributes = True 