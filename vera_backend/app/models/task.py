from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Timeline(BaseModel):
    createdAt: str
    sentAt: Optional[str] = None
    completedAt: Optional[str] = None

class Task(BaseModel):
    id: str
    name: str
    assignedTo: str
    dueDate: str
    status: str  # 'pending' | 'in-progress' | 'completed' | 'cancelled'
    description: str
    originalPrompt: str
    timeline: Timeline 