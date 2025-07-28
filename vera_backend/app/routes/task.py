from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime
import uuid
import logging

from app.models.sql_models import Task, User
from app.models.pydantic_models import TaskCreate, TaskResponse, TaskUpdate
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
        id=uuid.uuid4(),
        name=name,
        email=f"{name.lower()}@company.com",
        role="Employee",
        company_id=uuid.uuid4()  # This should be properly set based on context
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"Created new user: {name} with ID: {new_user.id}")
    return new_user.id

def task_to_response(task: Task) -> TaskResponse:
    """Convert a Task model to TaskResponse."""
    
    # Get assignee user info
    assignee_dict = None
    if task.assignee:
        assignee_dict = {
            "id": task.assignee.id,
            "name": task.assignee.name,
            "email": task.assignee.email,
            "role": task.assignee.role,
            "company_id": task.assignee.company_id,
            "team_id": task.assignee.team_id,
            "project_id": task.assignee.project_id,
            "created_at": task.assignee.created_at,
            "preferences": task.assignee.preferences
        }
    
    # Get creator user info
    creator_dict = None
    if task.creator:
        creator_dict = {
            "id": task.creator.id,
            "name": task.creator.name,
            "email": task.creator.email,
            "role": task.creator.role,
            "company_id": task.creator.company_id,
            "team_id": task.creator.team_id,
            "project_id": task.creator.project_id,
            "created_at": task.creator.created_at,
            "preferences": task.creator.preferences
        }
    
    # Get project info
    project_dict = None
    if task.project:
        project_dict = {
            "id": task.project.id,
            "name": task.project.name,
            "description": task.project.description,
            "company_id": task.project.company_id,
            "created_at": task.project.created_at
        }
    
    task_dict = {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "status": task.status,
        "assigned_to": task.assigned_to,
        "due_date": task.due_date,
        "created_by": task.created_by,
        "original_prompt": task.original_prompt,
        "project_id": task.project_id,
        "conversation_id": task.conversation_id,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "completed_at": task.completed_at,
        "priority": task.priority,
        "assignee": assignee_dict,
        "creator": creator_dict,
        "project": project_dict
    }
    return TaskResponse(**task_dict)

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(db: Session = Depends(get_db)):
    """Get all tasks."""
    try:
        # Query tasks with related information
        tasks = db.query(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.creator),
            joinedload(Task.project)
        ).all()
        return [task_to_response(task) for task in tasks]
    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}")
        return []

@router.post("/tasks", response_model=TaskResponse)
async def create_task(request: Request, task_info: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    print(f"Received task creation request: {task_info.dict()}")
    try:
        # Log the incoming request data
        logger.info(f"Received task creation request: {task_info.dict()}")
        
        # Handle assigned_to field
        assigned_to = task_info.assigned_to
        
        # Create task
        task = Task(
            id=uuid.uuid4(),
            name=task_info.name,
            description=task_info.description,
            status=task_info.status,
            assigned_to=assigned_to,
            due_date=task_info.due_date,
            created_by=task_info.created_by,
            original_prompt=task_info.original_prompt,
            project_id=task_info.project_id,
            conversation_id=task_info.conversation_id,
            priority=task_info.priority
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Load related data for response
        db.refresh(task)
        task = db.query(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.creator),
            joinedload(Task.project)
        ).filter(Task.id == task.id).first()
        
        logger.info(f"Created task: {task.name} with ID: {task.id}")
        return task_to_response(task)
        
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific task by ID."""
    try:
        task = db.query(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.creator),
            joinedload(Task.project)
        ).filter(Task.id == uuid.UUID(task_id)).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task_to_response(task)
    except Exception as e:
        logger.error(f"Error fetching task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching task: {str(e)}")

@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task."""
    try:
        task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update fields if provided
        if task_update.name is not None:
            task.name = task_update.name
        if task_update.description is not None:
            task.description = task_update.description
        if task_update.status is not None:
            task.status = task_update.status
        if task_update.assigned_to is not None:
            task.assigned_to = task_update.assigned_to
        if task_update.due_date is not None:
            task.due_date = task_update.due_date
        if task_update.priority is not None:
            task.priority = task_update.priority
        if task_update.completed_at is not None:
            task.completed_at = task_update.completed_at
        
        # Update the updated_at timestamp
        task.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(task)
        
        # Load related data for response
        task = db.query(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.creator),
            joinedload(Task.project)
        ).filter(Task.id == task.id).first()
        
        return task_to_response(task)
        
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """Delete a task."""
    try:
        task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        db.delete(task)
        db.commit()
        
        return {"message": "Task deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}") 