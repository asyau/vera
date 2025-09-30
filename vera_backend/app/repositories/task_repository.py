"""
Task repository implementation
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from app.models.sql_models import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Repository for Task entity operations"""

    def __init__(self, db: Session):
        super().__init__(db, Task)

    def get_by_assignee(self, assignee_id: str) -> List[Task]:
        """Get tasks assigned to a specific user"""
        return self.db.query(Task).filter(Task.assigned_to == assignee_id).all()

    def get_by_creator(self, creator_id: str) -> List[Task]:
        """Get tasks created by a specific user"""
        return self.db.query(Task).filter(Task.created_by == creator_id).all()

    def get_by_status(self, status: str) -> List[Task]:
        """Get tasks by status"""
        return self.db.query(Task).filter(Task.status == status).all()

    def get_by_priority(self, priority: str) -> List[Task]:
        """Get tasks by priority"""
        return self.db.query(Task).filter(Task.priority == priority).all()

    def get_by_project(self, project_id: str) -> List[Task]:
        """Get tasks in a specific project"""
        return self.db.query(Task).filter(Task.project_id == project_id).all()

    def get_overdue_tasks(self) -> List[Task]:
        """Get all overdue tasks"""
        return (
            self.db.query(Task)
            .filter(
                and_(
                    Task.due_date < datetime.utcnow(),
                    Task.status.notin_(["completed", "cancelled"]),
                )
            )
            .all()
        )

    def get_due_today(self) -> List[Task]:
        """Get tasks due today"""
        today = datetime.utcnow().date()
        return (
            self.db.query(Task)
            .filter(
                and_(
                    Task.due_date >= today,
                    Task.due_date < datetime.combine(today, datetime.max.time()),
                    Task.status.notin_(["completed", "cancelled"]),
                )
            )
            .all()
        )

    def get_upcoming_tasks(self, days: int = 7) -> List[Task]:
        """Get tasks due within the specified number of days"""
        from datetime import timedelta

        end_date = datetime.utcnow() + timedelta(days=days)

        return (
            self.db.query(Task)
            .filter(
                and_(
                    Task.due_date <= end_date,
                    Task.due_date >= datetime.utcnow(),
                    Task.status.notin_(["completed", "cancelled"]),
                )
            )
            .order_by(Task.due_date)
            .all()
        )

    def get_recent_tasks(self, user_id: str, limit: int = 10) -> List[Task]:
        """Get recently created or updated tasks for a user"""
        return (
            self.db.query(Task)
            .filter(or_(Task.assigned_to == user_id, Task.created_by == user_id))
            .order_by(desc(Task.updated_at))
            .limit(limit)
            .all()
        )

    def search_tasks(self, query: str, user_id: Optional[str] = None) -> List[Task]:
        """Search tasks by title or description"""
        search_filter = or_(
            Task.title.ilike(f"%{query}%"), Task.description.ilike(f"%{query}%")
        )

        if user_id:
            search_filter = and_(
                search_filter,
                or_(Task.assigned_to == user_id, Task.created_by == user_id),
            )

        return self.db.query(Task).filter(search_filter).all()

    def get_by_filters(self, **filters) -> List[Task]:
        """Get tasks by custom filters"""
        query = self.db.query(Task)

        if "assignee_id" in filters:
            query = query.filter(Task.assigned_to == filters["assignee_id"])

        if "creator_id" in filters:
            query = query.filter(Task.created_by == filters["creator_id"])

        if "status" in filters:
            query = query.filter(Task.status == filters["status"])

        if "priority" in filters:
            query = query.filter(Task.priority == filters["priority"])

        if "project_id" in filters:
            query = query.filter(Task.project_id == filters["project_id"])

        if "due_before" in filters:
            query = query.filter(Task.due_date <= filters["due_before"])

        if "due_after" in filters:
            query = query.filter(Task.due_date >= filters["due_after"])

        return query.all()
