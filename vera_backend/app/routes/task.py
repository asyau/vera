from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid
import logging

from app.models.sql_models import Task, Timeline
from app.models.pydantic_models import TaskCreate, TaskResponse
from app.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(db: Session = Depends(get_db)):
    """Get all tasks."""
    return db.query(Task).all()

@router.post("/tasks", response_model=TaskResponse)
async def create_task(request: Request, task_info: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    
    print(f"Received task creation request: {task_info.dict()}")
    try:
        # Log the incoming request data
        logger.info(f"Received task creation request: {task_info.dict()}")
        
        task_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        # Add current day information to the original prompt
        
        # Create timeline
        timeline = Timeline(
            id=str(uuid.uuid4()),
            createdAt=current_time,
            sentAt=current_time,
            task_id=task_id
        )
        
        # Create task
        task = Task(
            id=task_id,
            name=task_info.name,
            assignedTo=task_info.assignedTo,
            dueDate=task_info.dueDate,
            status=task_info.status,
            description=task_info.description,
            originalPrompt=task_info.originalPrompt,  # Use the original prompt
            timeline=timeline
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific task by ID."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_update: TaskCreate, db: Session = Depends(get_db)):
    """Update a task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        for key, value in task_update.dict().items():
            if key == "status" and value == "completed":
                task.timeline.completedAt = datetime.utcnow()
            else:
                setattr(task, key, value)
        
        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 