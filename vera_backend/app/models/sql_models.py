from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Timeline(Base):
    __tablename__ = "timelines"

    id = Column(String, primary_key=True, index=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    sentAt = Column(DateTime, nullable=True)
    completedAt = Column(DateTime, nullable=True)
    task_id = Column(String, ForeignKey("tasks.id"))
    task = relationship("Task", back_populates="timeline")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    assignedTo = Column(String)
    dueDate = Column(DateTime, nullable=True)
    status = Column(String)  # 'pending' | 'in-progress' | 'completed' | 'cancelled'
    description = Column(String)
    originalPrompt = Column(String)
    timeline = relationship("Timeline", uselist=False, back_populates="task") 