"""
User repository implementation
"""
from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.models.sql_models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity operations"""

    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_company(self, company_id: str) -> List[User]:
        """Get all users in a company with team and company relationships loaded"""
        return (
            self.db.query(User)
            .options(joinedload(User.team), joinedload(User.company))
            .filter(User.company_id == company_id)
            .all()
        )

    def get_by_role(self, role: str) -> List[User]:
        """Get users by role"""
        return self.db.query(User).filter(User.role == role).all()

    def get_by_team(self, team_id: str) -> List[User]:
        """Get users in a specific team"""
        return self.db.query(User).filter(User.team_id == team_id).all()

    def get_supervisors(self, company_id: Optional[str] = None) -> List[User]:
        """Get all supervisors, optionally filtered by company"""
        query = self.db.query(User).filter(User.role == "supervisor")
        if company_id:
            query = query.filter(User.company_id == company_id)
        return query.all()

    def get_employees(self, company_id: Optional[str] = None) -> List[User]:
        """Get all employees, optionally filtered by company"""
        query = self.db.query(User).filter(User.role == "employee")
        if company_id:
            query = query.filter(User.company_id == company_id)
        return query.all()

    def search_by_name(self, name: str, company_id: Optional[str] = None) -> List[User]:
        """Search users by name"""
        query = self.db.query(User).filter(
            or_(User.name.ilike(f"%{name}%"), User.email.ilike(f"%{name}%"))
        )
        if company_id:
            query = query.filter(User.company_id == company_id)
        return query.all()

    def get_by_filters(self, **filters) -> List[User]:
        """Get users by custom filters"""
        query = self.db.query(User)

        if "company_id" in filters:
            query = query.filter(User.company_id == filters["company_id"])

        if "role" in filters:
            query = query.filter(User.role == filters["role"])

        if "team_id" in filters:
            query = query.filter(User.team_id == filters["team_id"])

        if "active" in filters:
            query = query.filter(User.is_active == filters["active"])

        return query.all()
