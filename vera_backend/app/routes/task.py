from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
import uuid

from app.models.task import Task, Timeline

router = APIRouter()

# In-memory task storage (replace with database in production)
tasks: List[Task] = []

@router.get("/tasks", response_model=List[Task])
async def get_tasks():
    """Get all tasks."""
    return tasks

@router.post("/tasks", response_model=Task)
async def create_task(task_info: dict):
    """Create a new task."""
    try:
        # Create timeline
        timeline = Timeline(
            createdAt=datetime.now().isoformat(),
            sentAt=datetime.now().isoformat()
        )
        
        # Create task with default values for optional fields
        task = Task(
            id=str(uuid.uuid4()),
            name=task_info.get("name", ""),
            assignedTo=task_info.get("assignedTo", ""),
            dueDate=task_info.get("dueDate", datetime.now().isoformat().split("T")[0]),
            status=task_info.get("status", "pending"),
            description=task_info.get("description", ""),
            originalPrompt=task_info.get("originalPrompt", ""),
            timeline=timeline
        )
        
        tasks.append(task)
        return task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """Get a specific task by ID."""
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: dict):
    """Update a task."""
    for i, task in enumerate(tasks):
        if task.id == task_id:
            # Update task fields
            for key, value in task_update.items():
                if key == "status" and value == "completed":
                    # Update timeline when task is completed
                    task.timeline.completedAt = datetime.now().isoformat()
                setattr(task, key, value)
            tasks[i] = task
            return task
    raise HTTPException(status_code=404, detail="Task not found") 