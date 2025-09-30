"""
User management service implementing business logic
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import bcrypt
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models.sql_models import User
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


class UserService(BaseService[User]):
    """Service for user management business logic"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.repository = UserRepository(db)

    def create_user(
        self,
        name: str,
        email: str,
        password: str,
        role: str,
        company_id: str,
        team_id: Optional[str] = None,
    ) -> User:
        """Create a new user with business validation"""

        # Validate business rules
        self._validate_user_creation(email, role, company_id)

        # Hash password
        hashed_password = self._hash_password(password)

        user_data = {
            "id": uuid4(),
            "name": name,
            "email": email.lower(),
            "password_hash": hashed_password,
            "role": role,
            "company_id": UUID(company_id),
            "team_id": UUID(team_id) if team_id else None,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        return self._handle_transaction(self.repository.create, user_data)

    def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user credentials"""
        user = self.repository.get_by_email(email.lower())

        if not user:
            raise AuthenticationError(
                "Invalid credentials", error_code="INVALID_CREDENTIALS"
            )

        if not user.is_active:
            raise AuthenticationError(
                "Account is deactivated", error_code="ACCOUNT_DEACTIVATED"
            )

        if not self._verify_password(password, user.password_hash):
            raise AuthenticationError(
                "Invalid credentials", error_code="INVALID_CREDENTIALS"
            )

        # Update last login
        self.repository.update(user.id, {"last_login": datetime.utcnow()})

        return user

    def update_user_profile(self, user_id: UUID, update_data: Dict[str, Any]) -> User:
        """Update user profile with validation"""

        # Remove sensitive fields that shouldn't be updated directly
        sensitive_fields = ["password_hash", "role", "company_id", "is_active"]
        filtered_data = {
            k: v for k, v in update_data.items() if k not in sensitive_fields
        }

        if "email" in filtered_data:
            filtered_data["email"] = filtered_data["email"].lower()
            self._validate_email_uniqueness(filtered_data["email"], user_id)

        filtered_data["updated_at"] = datetime.utcnow()

        return self._handle_transaction(self.repository.update, user_id, filtered_data)

    def change_password(
        self, user_id: UUID, current_password: str, new_password: str
    ) -> bool:
        """Change user password with current password verification"""
        user = self.repository.get_or_raise(user_id)

        if not self._verify_password(current_password, user.password_hash):
            raise AuthenticationError(
                "Current password is incorrect", error_code="INVALID_CURRENT_PASSWORD"
            )

        new_hash = self._hash_password(new_password)
        self.repository.update(
            user_id, {"password_hash": new_hash, "updated_at": datetime.utcnow()}
        )

        return True

    def assign_user_to_team(
        self, user_id: UUID, team_id: UUID, requester_role: str
    ) -> User:
        """Assign user to a team (supervisor only)"""
        if requester_role != "supervisor":
            raise AuthorizationError(
                "Only supervisors can assign team members",
                error_code="INSUFFICIENT_PERMISSIONS",
            )

        return self._handle_transaction(
            self.repository.update,
            user_id,
            {"team_id": team_id, "updated_at": datetime.utcnow()},
        )

    def deactivate_user(self, user_id: UUID, requester_role: str) -> User:
        """Deactivate a user account (supervisor only)"""
        if requester_role != "supervisor":
            raise AuthorizationError(
                "Only supervisors can deactivate users",
                error_code="INSUFFICIENT_PERMISSIONS",
            )

        return self._handle_transaction(
            self.repository.update,
            user_id,
            {"is_active": False, "updated_at": datetime.utcnow()},
        )

    def get_team_members(self, team_id: UUID) -> List[User]:
        """Get all members of a team"""
        return self.repository.get_by_team(str(team_id))

    def get_company_users(self, company_id: UUID) -> List[User]:
        """Get all users in a company"""
        return self.repository.get_by_company(str(company_id))

    def search_users(self, query: str, company_id: Optional[UUID] = None) -> List[User]:
        """Search users by name or email"""
        return self.repository.search_by_name(
            query, str(company_id) if company_id else None
        )

    def _validate_user_creation(self, email: str, role: str, company_id: str) -> None:
        """Validate user creation business rules"""
        # Check email uniqueness
        existing_user = self.repository.get_by_email(email.lower())
        if existing_user:
            raise ConflictError("Email already registered", error_code="EMAIL_EXISTS")

        # Validate role
        valid_roles = ["employee", "supervisor", "admin"]
        if role not in valid_roles:
            raise ValidationError(
                f"Invalid role. Must be one of: {valid_roles}",
                error_code="INVALID_ROLE",
            )

        # TODO: Validate company exists

    def _validate_email_uniqueness(self, email: str, exclude_user_id: UUID) -> None:
        """Validate email uniqueness for updates"""
        existing_user = self.repository.get_by_email(email)
        if existing_user and existing_user.id != exclude_user_id:
            raise ConflictError("Email already in use", error_code="EMAIL_EXISTS")

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
