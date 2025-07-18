from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List
import logging

from app.models.sql_models import User, Team, Company
from app.models.pydantic_models import UserBase
from app.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/users", response_model=List[UserBase])
async def get_users(db: Session = Depends(get_db)):
    """Get all users with their roles and contact information."""
    try:
        # Query users with team and company information
        users = db.query(User).options(
            joinedload(User.team).joinedload(Team.company)
        ).all()
        
        return [
            UserBase(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
                team_id=user.team_id,
                team_name=user.team.name if user.team else None,
                company_name=user.team.company.name if user.team and user.team.company else None
            )
            for user in users
        ]
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")

@router.get("/users/{user_id}", response_model=UserBase)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get a specific user by ID."""
    try:
        user = db.query(User).options(
            joinedload(User.team).joinedload(Team.company)
        ).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserBase(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            team_id=user.team_id,
            team_name=user.team.name if user.team else None,
            company_name=user.team.company.name if user.team and user.team.company else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch user: {str(e)}")

@router.get("/teams", response_model=List[dict])
async def get_teams(db: Session = Depends(get_db)):
    """Get all teams with their company information."""
    try:
        teams = db.query(Team).options(joinedload(Team.company)).all()
        
        return [
            {
                "id": team.id,
                "name": team.name,
                "company_id": team.company_id,
                "company_name": team.company.name if team.company else None,
                "user_count": len(team.users) if team.users else 0
            }
            for team in teams
        ]
    except Exception as e:
        logger.error(f"Error fetching teams: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch teams: {str(e)}")

@router.get("/companies", response_model=List[dict])
async def get_companies(db: Session = Depends(get_db)):
    """Get all companies with their team and user counts."""
    try:
        companies = db.query(Company).options(joinedload(Company.teams)).all()
        
        return [
            {
                "id": company.id,
                "name": company.name,
                "team_count": len(company.teams) if company.teams else 0,
                "user_count": sum(len(team.users) if team.users else 0 for team in company.teams) if company.teams else 0
            }
            for company in companies
        ]
    except Exception as e:
        logger.error(f"Error fetching companies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch companies: {str(e)}") 