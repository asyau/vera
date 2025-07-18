from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime
import uuid
import logging

from app.models.sql_models import Task, Timeline, User
from app.models.pydantic_models import TaskCreate, TaskResponse
from app.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def get_user_id_by_name(db: Session, name: str) -> str:
    """Get user ID by name. If user doesn't exist, create them."""
    user = db.query(User).filter(User.name == name).first()
    if user:
        return user.id
    # Create new user if they don't exist
    new_user = User(
        id=str(uuid.uuid4()),
        name=name,
        email=f"{name.lower()}@company.com",
        role="employee"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"Created new user: {name} with ID: {new_user.id}")
    return new_user.id

def task_to_response(task: Task) -> TaskResponse:
    """Convert a Task model to TaskResponse with user name."""
    # Convert timeline to dict
    timeline_dict = {
        "createdAt": task.timeline.createdAt,
        "sentAt": task.timeline.sentAt,
        "completedAt": task.timeline.completedAt
    } if task.timeline else None
    
    # Convert assigned_user to dict
    assigned_user_dict = {
        "id": task.assigned_user.id,
        "name": task.assigned_user.name,
        "email": task.assigned_user.email,
        "role": task.assigned_user.role
    } if task.assigned_user else None
    
    task_dict = {
        "id": task.id,
        "name": task.name,
        "assignedTo": task.assignedTo,
        "assignedToName": task.assigned_user.name if task.assigned_user else None,
        "dueDate": task.dueDate,
        "status": task.status,
        "description": task.description,
        "originalPrompt": task.originalPrompt,
        "timeline": timeline_dict,
        "assigned_user": assigned_user_dict
    }
    return TaskResponse(**task_dict)

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(db: Session = Depends(get_db)):
    """Get all tasks."""
    try:
        # Query tasks with user information
        tasks = db.query(Task).options(joinedload(Task.assigned_user)).all()
        return [task_to_response(task) for task in tasks]
    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}")
        # Return empty list if there's an error (e.g., no users in database)
        return []

@router.post("/tasks", response_model=TaskResponse)
async def create_task(request: Request, task_info: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    print(f"Received task creation request: {task_info.dict()}")
    try:
        # Log the incoming request data
        logger.info(f"Received task creation request: {task_info.dict()}")
        # Get or create user ID from name
        user_id = get_user_id_by_name(db, task_info.assignedTo)
        task_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
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
            assignedTo=user_id,  # Use the user ID instead of name
            dueDate=task_info.dueDate,
            status=task_info.status,
            description=task_info.description,
            originalPrompt=task_info.originalPrompt,  # Use the original prompt
            timeline=timeline
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        # Reload the task with user information
        task_with_user = db.query(Task).options(joinedload(Task.assigned_user)).filter(Task.id == task.id).first()
        return task_to_response(task_with_user)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific task by ID."""
    task = db.query(Task).options(joinedload(Task.assigned_user)).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_to_response(task)

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
        # Reload the task with user information
        task_with_user = db.query(Task).options(joinedload(Task.assigned_user)).filter(Task.id == task.id).first()
        return task_to_response(task_with_user)
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 