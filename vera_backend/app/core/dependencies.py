"""
Enhanced FastAPI Dependencies for Vira
Implements advanced dependency injection patterns for role-based access and AI services
"""
import uuid
from functools import lru_cache
from typing import Annotated, Any, Dict, Generator, Optional

from fastapi import BackgroundTasks, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.api_gateway import AuthenticationMiddleware
from app.core.config import settings
from app.database import get_db
from app.models.sql_models import Company, User
from app.repositories.user_repository import UserRepository
from app.services.langgraph_integration import IntegratedAIService
from app.services.langgraph_workflows import LangGraphWorkflowService


# Database Session Dependency with proper cleanup
def get_db_session() -> Generator[Session, None, None]:
    """Database session with automatic cleanup"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_db_session)]


# User Authentication Dependencies
async def get_current_user_id(
    token_payload: Dict[str, Any] = Depends(AuthenticationMiddleware.verify_token)
) -> str:
    """Get current authenticated user ID"""
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return user_id


async def get_current_user(
    user_id: Annotated[str, Depends(get_current_user_id)], db: SessionDep
) -> User:
    """Get current authenticated user object"""
    user_repo = UserRepository(db)
    user = user_repo.get(uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


# Role-based Dependencies
class RoleChecker:
    """Callable dependency for role-based access control"""

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: CurrentUserDep) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}",
            )
        return current_user


# Specific role checkers
require_ceo = RoleChecker(["CEO"])
require_manager = RoleChecker(["CEO", "CTO", "PM"])
require_supervisor = RoleChecker(["CEO", "CTO", "PM", "Supervisor"])
require_authenticated = RoleChecker(["CEO", "CTO", "PM", "Supervisor", "Employee"])


# Company Context Dependencies
async def get_user_company(current_user: CurrentUserDep, db: SessionDep) -> Company:
    """Get the company associated with the current user"""
    if not current_user.company_id:
        raise HTTPException(
            status_code=400, detail="User not associated with a company"
        )

    company = db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


CompanyDep = Annotated[Company, Depends(get_user_company)]


# AI Service Dependencies
@lru_cache()
def get_ai_service_config() -> Dict[str, Any]:
    """Get AI service configuration (cached)"""
    return {
        "openai_api_key": settings.openai_api_key,
        "model": settings.openai_model,
        "max_tokens": getattr(settings, "max_tokens", 4000),
        "temperature": getattr(settings, "temperature", 0.7),
    }


def get_integrated_ai_service(db: SessionDep) -> IntegratedAIService:
    """Get IntegratedAIService instance with proper dependency injection"""
    return IntegratedAIService(db)


def get_workflow_service(db: SessionDep) -> LangGraphWorkflowService:
    """Get LangGraphWorkflowService instance"""
    return LangGraphWorkflowService(db)


AIServiceDep = Annotated[IntegratedAIService, Depends(get_integrated_ai_service)]
WorkflowServiceDep = Annotated[LangGraphWorkflowService, Depends(get_workflow_service)]


# Request Context Dependencies
async def get_request_context(
    current_user: CurrentUserDep,
    company: CompanyDep,
    x_client_version: Annotated[Optional[str], Header()] = None,
    x_user_agent: Annotated[Optional[str], Header()] = None,
) -> Dict[str, Any]:
    """Build comprehensive request context for AI services"""
    return {
        "user": {
            "id": str(current_user.id),
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "preferences": current_user.preferences or {},
        },
        "company": {
            "id": str(company.id),
            "name": company.name,
            "profile": company.company_profile or {},
        },
        "client": {"version": x_client_version, "user_agent": x_user_agent},
        "timestamp": uuid.uuid4().hex,  # Request correlation ID
    }


RequestContextDep = Annotated[Dict[str, Any], Depends(get_request_context)]


# Background Task Dependencies for AI Operations
# Note: BackgroundTasks should be used directly without Depends()
# AIBackgroundTasksDep = BackgroundTasks  # Use directly in function parameters


# Hierarchical Permission Checker
class HierarchyChecker:
    """Check if user can access target user's data based on hierarchy"""

    def __init__(self, allow_self: bool = True, allow_subordinates: bool = True):
        self.allow_self = allow_self
        self.allow_subordinates = allow_subordinates

    def __call__(
        self, target_user_id: str, current_user: CurrentUserDep, db: SessionDep
    ) -> bool:
        """Check hierarchical access permissions"""
        target_uuid = uuid.UUID(target_user_id)

        # Self access
        if self.allow_self and current_user.id == target_uuid:
            return True

        # Hierarchical access
        if self.allow_subordinates:
            user_repo = UserRepository(db)
            target_user = user_repo.get(target_uuid)

            if not target_user:
                raise HTTPException(status_code=404, detail="Target user not found")

            # Check if current user can access target user based on hierarchy
            role_hierarchy = ["CEO", "CTO", "PM", "Supervisor", "Employee"]
            current_level = (
                role_hierarchy.index(current_user.role)
                if current_user.role in role_hierarchy
                else -1
            )
            target_level = (
                role_hierarchy.index(target_user.role)
                if target_user.role in role_hierarchy
                else -1
            )

            # Higher roles can access lower roles
            if (
                current_level >= 0
                and target_level >= 0
                and current_level < target_level
            ):
                return True

            # Same team access for supervisors
            if (
                current_user.role == "Supervisor"
                and current_user.team_id == target_user.team_id
            ):
                return True

        raise HTTPException(
            status_code=403,
            detail="Access denied: insufficient permissions for target user",
        )


# Team-based Dependencies
async def get_team_members(current_user: CurrentUserDep, db: SessionDep) -> list[User]:
    """Get team members for the current user"""
    if not current_user.team_id:
        return []

    user_repo = UserRepository(db)
    return user_repo.get_by_team(current_user.team_id)


TeamMembersDep = Annotated[list[User], Depends(get_team_members)]


# Workflow-specific Dependencies
async def validate_workflow_access(
    workflow_id: str, current_user: CurrentUserDep, db: SessionDep
) -> str:
    """Validate user has access to the specified workflow"""
    # This would typically check workflow ownership/permissions
    # For now, we'll implement basic validation
    try:
        uuid.UUID(workflow_id)
        return workflow_id
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workflow ID format")


WorkflowAccessDep = Annotated[str, Depends(validate_workflow_access)]
