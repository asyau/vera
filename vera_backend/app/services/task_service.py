"""
Task management service implementing business logic
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.exceptions import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models.sql_models import Task
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


class TaskService(BaseService[Task]):
    """Service for task management business logic"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.repository = TaskRepository(db)
        self.user_repository = UserRepository(db)

    def create_task(
        self,
        title: str,
        description: str,
        creator_id: UUID,
        assignee_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        due_date: Optional[datetime] = None,
        priority: str = "medium",
        status: str = "todo",
        tags: Optional[List[str]] = None,
    ) -> Task:
        """Create a new task with business validation"""

        # Validate business rules
        self._validate_task_creation(
            creator_id, assignee_id, project_id, priority, status
        )

        task_data = {
            "id": uuid4(),
            "title": title,
            "description": description,
            "creator_id": creator_id,
            "assignee_id": assignee_id,
            "project_id": project_id,
            "due_date": due_date,
            "priority": priority,
            "status": status,
            "tags": tags or [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        task = self._handle_transaction(self.repository.create, task_data)

        # Log task creation
        self._log_operation(
            "CREATE_TASK",
            str(task.id),
            {
                "creator_id": str(creator_id),
                "assignee_id": str(assignee_id) if assignee_id else None,
                "title": title,
            },
        )

        return task

    def update_task(
        self, task_id: UUID, update_data: Dict[str, Any], requester_id: UUID
    ) -> Task:
        """Update task with authorization checks"""

        task = self.repository.get_or_raise(task_id)

        # Check authorization
        if not self._can_modify_task(task, requester_id):
            raise AuthorizationError(
                "You don't have permission to modify this task",
                error_code="INSUFFICIENT_PERMISSIONS",
            )

        # Validate updates
        self._validate_task_updates(update_data)

        # Handle status changes
        if "status" in update_data:
            self._handle_status_change(task, update_data["status"])

        update_data["updated_at"] = datetime.utcnow()

        updated_task = self._handle_transaction(
            self.repository.update, task_id, update_data
        )

        # Log task update
        self._log_operation(
            "UPDATE_TASK",
            str(task_id),
            {"requester_id": str(requester_id), "changes": list(update_data.keys())},
        )

        return updated_task

    def assign_task(self, task_id: UUID, assignee_id: UUID, requester_id: UUID) -> Task:
        """Assign task to a user"""

        task = self.repository.get_or_raise(task_id)

        # Check authorization (creator or supervisor can assign)
        requester = self.user_repository.get_or_raise(requester_id)
        if not (task.created_by == requester_id or requester.role == "supervisor"):
            raise AuthorizationError(
                "Only task creator or supervisor can assign tasks",
                error_code="INSUFFICIENT_PERMISSIONS",
            )

        # Validate assignee exists
        assignee = self.user_repository.get_or_raise(assignee_id)

        return self._handle_transaction(
            self.repository.update,
            task_id,
            {
                "assignee_id": assignee_id,
                "status": "assigned" if task.status == "todo" else task.status,
                "updated_at": datetime.utcnow(),
            },
        )

    def complete_task(self, task_id: UUID, requester_id: UUID) -> Task:
        """Mark task as completed"""

        task = self.repository.get_or_raise(task_id)

        # Check authorization (assignee or creator can complete)
        if not (task.assigned_to == requester_id or task.created_by == requester_id):
            raise AuthorizationError(
                "Only task assignee or creator can complete tasks",
                error_code="INSUFFICIENT_PERMISSIONS",
            )

        return self._handle_transaction(
            self.repository.update,
            task_id,
            {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
        )

    def get_user_tasks(
        self,
        user_id: UUID,
        status_filter: Optional[str] = None,
        include_created: bool = True,
        include_assigned: bool = True,
    ) -> List[Task]:
        """Get tasks for a user (created or assigned)"""

        tasks = []

        if include_assigned:
            assigned_tasks = self.repository.get_by_assignee(str(user_id))
            if status_filter:
                assigned_tasks = [
                    t for t in assigned_tasks if t.status == status_filter
                ]
            tasks.extend(assigned_tasks)

        if include_created:
            created_tasks = self.repository.get_by_creator(str(user_id))
            if status_filter:
                created_tasks = [t for t in created_tasks if t.status == status_filter]
            tasks.extend(created_tasks)

        # Remove duplicates and sort by due date
        unique_tasks = list({t.id: t for t in tasks}.values())
        return sorted(unique_tasks, key=lambda x: x.due_date or datetime.max)

    def get_overdue_tasks(self, user_id: Optional[UUID] = None) -> List[Task]:
        """Get overdue tasks, optionally filtered by user"""
        overdue_tasks = self.repository.get_overdue_tasks()

        if user_id:
            overdue_tasks = [
                t
                for t in overdue_tasks
                if t.assigned_to == user_id or t.created_by == user_id
            ]

        return overdue_tasks

    def get_upcoming_tasks(self, user_id: UUID, days: int = 7) -> List[Task]:
        """Get tasks due within specified days for a user"""
        upcoming_tasks = self.repository.get_upcoming_tasks(days)

        return [
            t
            for t in upcoming_tasks
            if t.assigned_to == user_id or t.created_by == user_id
        ]

    def search_tasks(self, query: str, user_id: UUID) -> List[Task]:
        """Search tasks by title or description"""
        return self.repository.search_tasks(query, str(user_id))

    def get_task_analytics(self, user_id: UUID) -> Dict[str, Any]:
        """Get task analytics for a user"""
        user_tasks = self.get_user_tasks(user_id)

        total_tasks = len(user_tasks)
        completed_tasks = len([t for t in user_tasks if t.status == "completed"])
        overdue_tasks = len(self.get_overdue_tasks(user_id))
        upcoming_tasks = len(self.get_upcoming_tasks(user_id, 7))

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100)
            if total_tasks > 0
            else 0,
            "overdue_tasks": overdue_tasks,
            "upcoming_tasks": upcoming_tasks,
            "status_breakdown": self._get_status_breakdown(user_tasks),
        }

    def _validate_task_creation(
        self,
        creator_id: UUID,
        assignee_id: Optional[UUID],
        project_id: Optional[UUID],
        priority: str,
        status: str,
    ) -> None:
        """Validate task creation business rules"""

        # Validate creator exists
        self.user_repository.get_or_raise(creator_id)

        # Validate assignee exists if provided
        if assignee_id:
            self.user_repository.get_or_raise(assignee_id)

        # Validate priority
        valid_priorities = ["low", "medium", "high", "urgent"]
        if priority not in valid_priorities:
            raise ValidationError(
                f"Invalid priority. Must be one of: {valid_priorities}",
                error_code="INVALID_PRIORITY",
            )

        # Validate status
        valid_statuses = ["todo", "assigned", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            raise ValidationError(
                f"Invalid status. Must be one of: {valid_statuses}",
                error_code="INVALID_STATUS",
            )

    def _validate_task_updates(self, update_data: Dict[str, Any]) -> None:
        """Validate task update data"""

        if "priority" in update_data:
            valid_priorities = ["low", "medium", "high", "urgent"]
            if update_data["priority"] not in valid_priorities:
                raise ValidationError(
                    f"Invalid priority. Must be one of: {valid_priorities}",
                    error_code="INVALID_PRIORITY",
                )

        if "status" in update_data:
            valid_statuses = [
                "todo",
                "assigned",
                "in_progress",
                "completed",
                "cancelled",
            ]
            if update_data["status"] not in valid_statuses:
                raise ValidationError(
                    f"Invalid status. Must be one of: {valid_statuses}",
                    error_code="INVALID_STATUS",
                )

    def _can_modify_task(self, task: Task, requester_id: UUID) -> bool:
        """Check if user can modify the task"""
        requester = self.user_repository.get_or_raise(requester_id)

        # Creator, assignee, or supervisor can modify
        return (
            task.created_by == requester_id
            or task.assigned_to == requester_id
            or requester.role == "supervisor"
        )

    def _handle_status_change(self, task: Task, new_status: str) -> None:
        """Handle business logic for status changes"""

        # If completing task, set completion timestamp
        if new_status == "completed" and task.status != "completed":
            task.completed_at = datetime.utcnow()

        # If reopening completed task, clear completion timestamp
        if task.status == "completed" and new_status != "completed":
            task.completed_at = None  # type: ignore

    def _get_status_breakdown(self, tasks: List[Task]) -> Dict[str, int]:
        """Get breakdown of tasks by status"""
        breakdown: Dict[str, int] = {}
        for task in tasks:
            status = task.status
            breakdown[status] = breakdown.get(status, 0) + 1
        return breakdown
