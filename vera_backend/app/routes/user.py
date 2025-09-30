"""
Enhanced User Management Routes using Service Layer pattern
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api_gateway import AuthenticationMiddleware
from app.core.exceptions import ViraException
from app.database import get_db
from app.services.user_service import UserService

# AuthUser type not needed for this file


router = APIRouter()


# Request/Response Models
class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    team_id: Optional[UUID] = None
    preferences: Optional[Dict[str, Any]] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UserCreateRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str
    company_id: UUID
    team_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    company_id: str
    team_id: Optional[str]
    is_active: bool
    created_at: str
    last_login: Optional[str]
    preferences: Optional[Dict[str, Any]]
    # Additional fields for frontend
    team_name: Optional[str] = None
    company_name: Optional[str] = None

    class Config:
        from_attributes = True


# Routes
@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get current user profile"""
    try:
        user_service = UserService(db)
        user = user_service.repository.get_or_raise(UUID(current_user_id))

        return UserResponse.from_orm(user)

    except ViraException as e:
        raise HTTPException(
            status_code=404 if "not found" in e.message.lower() else 400,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    request: UserUpdateRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update current user profile"""
    try:
        user_service = UserService(db)

        # Filter out None values
        update_data = {k: v for k, v in request.dict().items() if v is not None}

        user = user_service.update_user_profile(
            user_id=UUID(current_user_id), update_data=update_data
        )

        return UserResponse.from_orm(user)

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.post("/me/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Change user password"""
    try:
        user_service = UserService(db)

        success = user_service.change_password(
            user_id=UUID(current_user_id),
            current_password=request.current_password,
            new_password=request.new_password,
        )

        return {"message": "Password changed successfully"}

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to change password: {str(e)}"
        )


@router.get("/", response_model=List[UserResponse])
async def get_users(
    company_filter: Optional[str] = Query(None, description="Filter by company ID"),
    team_filter: Optional[str] = Query(None, description="Filter by team ID"),
    role_filter: Optional[str] = Query(None, description="Filter by role"),
    current_user_token: dict = Depends(
        AuthenticationMiddleware.require_any_role(["supervisor", "admin"])
    ),
    db: Session = Depends(get_db),
):
    """Get users with filters (supervisor/admin only)"""
    try:
        user_service = UserService(db)

        if company_filter:
            users = user_service.get_company_users(UUID(company_filter))
        elif team_filter:
            users = user_service.get_team_members(UUID(team_filter))
        elif role_filter:
            users = user_service.repository.get_by_role(role_filter)
        else:
            # Get all users - limit based on current user's company
            current_user_id = current_user_token.get("user_id")
            current_user = user_service.repository.get_or_raise(UUID(current_user_id))
            users = user_service.get_company_users(UUID(str(current_user.company_id)))

        # Convert to UserResponse with team_name and company_name
        user_responses = []
        for user in users:
            user_response = UserResponse(
                id=str(user.id),
                name=user.name,
                email=user.email,
                role=user.role,
                company_id=str(user.company_id),
                team_id=str(user.team_id) if user.team_id else None,
                is_active=True,  # Assuming active for now
                created_at=user.created_at.isoformat() if user.created_at else "",
                last_login=None,  # Not tracked in simple auth
                preferences=user.preferences
                if isinstance(user.preferences, dict)
                else None,
                team_name=user.team.name if user.team else None,
                company_name=user.company.name if user.company else None,
            )
            user_responses.append(user_response)

        return user_responses

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user_token: dict = Depends(
        AuthenticationMiddleware.require_any_role(["supervisor", "admin"])
    ),
    db: Session = Depends(get_db),
):
    """Get specific user (supervisor/admin only)"""
    try:
        user_service = UserService(db)
        user = user_service.repository.get_or_raise(user_id)

        return UserResponse.from_orm(user)

    except ViraException as e:
        raise HTTPException(
            status_code=404 if "not found" in e.message.lower() else 400,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.put("/{user_id}/team", response_model=UserResponse)
async def assign_user_to_team(
    user_id: UUID,
    team_id: UUID,
    current_user_token: dict = Depends(
        AuthenticationMiddleware.require_role("supervisor")
    ),
    db: Session = Depends(get_db),
):
    """Assign user to team (supervisor only)"""
    try:
        user_service = UserService(db)

        user = user_service.assign_user_to_team(
            user_id=user_id, team_id=team_id, requester_role="supervisor"
        )

        return UserResponse.from_orm(user)

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to assign user to team: {str(e)}"
        )


@router.put("/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    current_user_token: dict = Depends(
        AuthenticationMiddleware.require_role("supervisor")
    ),
    db: Session = Depends(get_db),
):
    """Deactivate user (supervisor only)"""
    try:
        user_service = UserService(db)

        user = user_service.deactivate_user(
            user_id=user_id, requester_role="supervisor"
        )

        return {"message": f"User {user.name} deactivated successfully"}

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to deactivate user: {str(e)}"
        )


@router.get("/search/query", response_model=List[UserResponse])
async def search_users(
    q: str = Query(..., description="Search query"),
    current_user_token: dict = Depends(
        AuthenticationMiddleware.require_any_role(["supervisor", "admin"])
    ),
    db: Session = Depends(get_db),
):
    """Search users by name or email (supervisor/admin only)"""
    try:
        user_service = UserService(db)

        # Limit search to current user's company
        current_user_id = current_user_token.get("user_id")
        current_user = user_service.repository.get_or_raise(UUID(current_user_id))

        users = user_service.search_users(query=q, company_id=current_user.company_id)

        return [UserResponse.from_orm(user) for user in users]

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search users: {str(e)}")


@router.post("/", response_model=UserResponse)
async def create_user(
    request: UserCreateRequest,
    current_user_token: dict = Depends(AuthenticationMiddleware.require_role("admin")),
    db: Session = Depends(get_db),
):
    """Create a new user (admin only)"""
    try:
        user_service = UserService(db)

        user = user_service.create_user(
            name=request.name,
            email=request.email,
            password=request.password,
            role=request.role,
            company_id=request.company_id,
            team_id=request.team_id,
            project_id=request.project_id,
            preferences=request.preferences,
        )

        return UserResponse.from_orm(user)

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    request: UserUpdateRequest,
    current_user_token: dict = Depends(
        AuthenticationMiddleware.require_any_role(["admin", "supervisor"])
    ),
    db: Session = Depends(get_db),
):
    """Update a user (admin/supervisor only)"""
    try:
        user_service = UserService(db)

        # Filter out None values
        update_data = {k: v for k, v in request.dict().items() if v is not None}

        user = user_service.update_user_profile(
            user_id=user_id,
            update_data=update_data,
            requester_role=current_user_token.get("role"),
        )

        return UserResponse.from_orm(user)

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user_token: dict = Depends(AuthenticationMiddleware.require_role("admin")),
    db: Session = Depends(get_db),
):
    """Delete a user (admin only)"""
    try:
        user_service = UserService(db)

        success = user_service.delete_user(user_id=user_id, requester_role="admin")

        return {"message": "User deleted successfully"}

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
