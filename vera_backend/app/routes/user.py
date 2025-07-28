from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List
import uuid
import logging

from app.models.sql_models import User, Company, Team, Project
from app.models.pydantic_models import UserCreate, UserResponse, UserUpdate, UserListResponse
from app.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/users", response_model=UserListResponse)
async def get_users(db: Session = Depends(get_db)):
    """Get all users."""
    try:
        users = db.query(User).options(
            joinedload(User.company),
            joinedload(User.team),
            joinedload(User.project)
        ).all()
        return UserListResponse(
            users=[UserResponse.from_orm(user) for user in users],
            total=len(users)
        )
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get a specific user by ID."""
    try:
        user = db.query(User).options(
            joinedload(User.company),
            joinedload(User.team),
            joinedload(User.project)
        ).filter(User.id == uuid.UUID(user_id)).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse.from_orm(user)
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

@router.get("/companies/{company_id}/users", response_model=UserListResponse)
async def get_company_users(company_id: str, db: Session = Depends(get_db)):
    """Get all users for a specific company."""
    try:
        users = db.query(User).options(
            joinedload(User.company),
            joinedload(User.team),
            joinedload(User.project)
        ).filter(User.company_id == uuid.UUID(company_id)).all()
        return UserListResponse(
            users=[UserResponse.from_orm(user) for user in users],
            total=len(users)
        )
    except Exception as e:
        logger.error(f"Error fetching users for company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@router.get("/teams/{team_id}/users", response_model=UserListResponse)
async def get_team_users(team_id: str, db: Session = Depends(get_db)):
    """Get all users for a specific team."""
    try:
        users = db.query(User).options(
            joinedload(User.company),
            joinedload(User.team),
            joinedload(User.project)
        ).filter(User.team_id == uuid.UUID(team_id)).all()
        return UserListResponse(
            users=[UserResponse.from_orm(user) for user in users],
            total=len(users)
        )
    except Exception as e:
        logger.error(f"Error fetching users for team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@router.get("/projects/{project_id}/users", response_model=UserListResponse)
async def get_project_users(project_id: str, db: Session = Depends(get_db)):
    """Get all users for a specific project."""
    try:
        users = db.query(User).options(
            joinedload(User.company),
            joinedload(User.team),
            joinedload(User.project)
        ).filter(User.project_id == uuid.UUID(project_id)).all()
        return UserListResponse(
            users=[UserResponse.from_orm(user) for user in users],
            total=len(users)
        )
    except Exception as e:
        logger.error(f"Error fetching users for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@router.post("/users", response_model=UserResponse)
async def create_user(user_info: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    try:
        # Verify company exists
        company = db.query(Company).filter(Company.id == user_info.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Verify team exists if provided
        if user_info.team_id:
            team = db.query(Team).filter(Team.id == user_info.team_id).first()
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")
        
        # Verify project exists if provided
        if user_info.project_id:
            project = db.query(Project).filter(Project.id == user_info.project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == user_info.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        user = User(
            id=uuid.uuid4(),
            name=user_info.name,
            email=user_info.email,
            role=user_info.role,
            company_id=user_info.company_id,
            team_id=user_info.team_id,
            project_id=user_info.project_id,
            preferences=user_info.preferences
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Load related data for response
        user = db.query(User).options(
            joinedload(User.company),
            joinedload(User.team),
            joinedload(User.project)
        ).filter(User.id == user.id).first()
        
        logger.info(f"Created user: {user.name} with ID: {user.id}")
        return UserResponse.from_orm(user)
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate, db: Session = Depends(get_db)):
    """Update a user."""
    try:
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update fields if provided
        if user_update.name is not None:
            user.name = user_update.name
        if user_update.email is not None:
            # Check if email already exists for another user
            existing_user = db.query(User).filter(
                User.email == user_update.email,
                User.id != uuid.UUID(user_id)
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="User with this email already exists")
            user.email = user_update.email
        if user_update.role is not None:
            user.role = user_update.role
        if user_update.company_id is not None:
            # Verify new company exists
            company = db.query(Company).filter(Company.id == user_update.company_id).first()
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")
            user.company_id = user_update.company_id
        if user_update.team_id is not None:
            # Verify new team exists
            team = db.query(Team).filter(Team.id == user_update.team_id).first()
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")
            user.team_id = user_update.team_id
        if user_update.project_id is not None:
            # Verify new project exists
            project = db.query(Project).filter(Project.id == user_update.project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            user.project_id = user_update.project_id
        if user_update.preferences is not None:
            user.preferences = user_update.preferences
        
        db.commit()
        db.refresh(user)
        
        # Load related data for response
        user = db.query(User).options(
            joinedload(User.company),
            joinedload(User.team),
            joinedload(User.project)
        ).filter(User.id == user.id).first()
        
        return UserResponse.from_orm(user)
        
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    """Delete a user."""
    try:
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.delete(user)
        db.commit()
        
        return {"message": "User deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}") 