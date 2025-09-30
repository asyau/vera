"""
Enhanced Task Management Routes using Service Layer pattern
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api_gateway import AuthenticationMiddleware
from app.core.exceptions import ViraException
from app.database import get_db
from app.services.task_service import TaskService

router = APIRouter()


# Request/Response Models
class TaskCreateRequest(BaseModel):
    title: str
    description: str
    assignee_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    priority: str = "medium"
    tags: Optional[List[str]] = None


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str
    creator_id: UUID
    assignee_id: Optional[UUID]
    project_id: Optional[UUID]
    status: str
    priority: str
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskAnalyticsResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    overdue_tasks: int
    upcoming_tasks: int
    status_breakdown: Dict[str, int]


# Routes
@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: TaskCreateRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new task"""
    try:
        task_service = TaskService(db)

        task = task_service.create_task(
            title=request.title,
            description=request.description,
            creator_id=UUID(current_user_id),
            assignee_id=request.assignee_id,
            project_id=request.project_id,
            due_date=request.due_date,
            priority=request.priority,
            tags=request.tags,
        )

        return TaskResponse.from_orm(task)

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    status_filter: Optional[str] = Query(None, description="Filter by task status"),
    include_created: bool = Query(True, description="Include tasks created by user"),
    include_assigned: bool = Query(True, description="Include tasks assigned to user"),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get tasks for the current user"""
    try:
        task_service = TaskService(db)

        tasks = task_service.get_user_tasks(
            user_id=UUID(current_user_id),
            status_filter=status_filter,
            include_created=include_created,
            include_assigned=include_assigned,
        )

        return [TaskResponse.from_orm(task) for task in tasks]

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get a specific task"""
    try:
        task_service = TaskService(db)
        task = task_service.repository.get_or_raise(task_id)

        return TaskResponse.from_orm(task)

    except ViraException as e:
        raise HTTPException(
            status_code=404 if "not found" in e.message.lower() else 400,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    request: TaskUpdateRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update a task"""
    try:
        task_service = TaskService(db)

        # Filter out None values
        update_data = {k: v for k, v in request.dict().items() if v is not None}

        task = task_service.update_task(
            task_id=task_id, update_data=update_data, requester_id=UUID(current_user_id)
        )

        return TaskResponse.from_orm(task)

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")


@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: UUID,
    assignee_id: UUID,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Assign a task to a user"""
    try:
        task_service = TaskService(db)

        task = task_service.assign_task(
            task_id=task_id, assignee_id=assignee_id, requester_id=UUID(current_user_id)
        )

        return TaskResponse.from_orm(task)

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign task: {str(e)}")


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: UUID,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Mark a task as completed"""
    try:
        task_service = TaskService(db)

        task = task_service.complete_task(
            task_id=task_id, requester_id=UUID(current_user_id)
        )

        return TaskResponse.from_orm(task)

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to complete task: {str(e)}"
        )


@router.get("/overdue/list", response_model=List[TaskResponse])
async def get_overdue_tasks(
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get overdue tasks for the current user"""
    try:
        task_service = TaskService(db)

        tasks = task_service.get_overdue_tasks(user_id=UUID(current_user_id))

        return [TaskResponse.from_orm(task) for task in tasks]

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get overdue tasks: {str(e)}"
        )


@router.get("/upcoming/list", response_model=List[TaskResponse])
async def get_upcoming_tasks(
    days: int = Query(7, description="Number of days to look ahead"),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get upcoming tasks for the current user"""
    try:
        task_service = TaskService(db)

        tasks = task_service.get_upcoming_tasks(
            user_id=UUID(current_user_id), days=days
        )

        return [TaskResponse.from_orm(task) for task in tasks]

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get upcoming tasks: {str(e)}"
        )


@router.get("/search/query", response_model=List[TaskResponse])
async def search_tasks(
    q: str = Query(..., description="Search query"),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Search tasks by title or description"""
    try:
        task_service = TaskService(db)

        tasks = task_service.search_tasks(query=q, user_id=UUID(current_user_id))

        return [TaskResponse.from_orm(task) for task in tasks]

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search tasks: {str(e)}")


@router.get("/analytics/summary", response_model=TaskAnalyticsResponse)
async def get_task_analytics(
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get task analytics for the current user"""
    try:
        task_service = TaskService(db)

        analytics = task_service.get_task_analytics(user_id=UUID(current_user_id))

        return TaskAnalyticsResponse(**analytics)

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get task analytics: {str(e)}"
        )


# Supervisor-only routes
@router.get("/team/{team_id}", response_model=List[TaskResponse])
async def get_team_tasks(
    team_id: UUID,
    current_user_token: dict = Depends(
        AuthenticationMiddleware.require_role("supervisor")
    ),
    db: Session = Depends(get_db),
):
    """Get all tasks for a team (supervisor only)"""
    try:
        task_service = TaskService(db)

        # Get all team members and their tasks
        team_tasks = task_service.repository.get_by_filters(team_id=str(team_id))

        return [TaskResponse.from_orm(task) for task in team_tasks]

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get team tasks: {str(e)}"
        )


@router.delete("/{task_id}")
async def delete_task(
    task_id: UUID,
    current_user_token: dict = Depends(
        AuthenticationMiddleware.require_any_role(["supervisor", "admin"])
    ),
    db: Session = Depends(get_db),
):
    """Delete a task (supervisor/admin only)"""
    try:
        task_service = TaskService(db)

        success = task_service.repository.delete(task_id)

        if success:
            return {"message": "Task deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Task not found")

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")
