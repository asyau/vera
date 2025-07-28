from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List
import uuid
import logging

from app.models.sql_models import Team, Company, Project, User
from app.models.pydantic_models import TeamCreate, TeamResponse, TeamUpdate, TeamListResponse
from app.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/teams", response_model=TeamListResponse)
async def get_teams(db: Session = Depends(get_db)):
    """Get all teams."""
    try:
        teams = db.query(Team).options(
            joinedload(Team.company),
            joinedload(Team.project),
            joinedload(Team.supervisor),
            joinedload(Team.users)
        ).all()
        return TeamListResponse(
            teams=[TeamResponse.from_orm(team) for team in teams],
            total=len(teams)
        )
    except Exception as e:
        logger.error(f"Error fetching teams: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching teams: {str(e)}")

@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(team_id: str, db: Session = Depends(get_db)):
    """Get a specific team by ID."""
    try:
        team = db.query(Team).options(
            joinedload(Team.company),
            joinedload(Team.project),
            joinedload(Team.supervisor),
            joinedload(Team.users)
        ).filter(Team.id == uuid.UUID(team_id)).first()
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        return TeamResponse.from_orm(team)
    except Exception as e:
        logger.error(f"Error fetching team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching team: {str(e)}")

@router.get("/companies/{company_id}/teams", response_model=TeamListResponse)
async def get_company_teams(company_id: str, db: Session = Depends(get_db)):
    """Get all teams for a specific company."""
    try:
        teams = db.query(Team).options(
            joinedload(Team.company),
            joinedload(Team.project),
            joinedload(Team.supervisor),
            joinedload(Team.users)
        ).filter(Team.company_id == uuid.UUID(company_id)).all()
        return TeamListResponse(
            teams=[TeamResponse.from_orm(team) for team in teams],
            total=len(teams)
        )
    except Exception as e:
        logger.error(f"Error fetching teams for company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching teams: {str(e)}")

@router.get("/projects/{project_id}/teams", response_model=TeamListResponse)
async def get_project_teams(project_id: str, db: Session = Depends(get_db)):
    """Get all teams for a specific project."""
    try:
        teams = db.query(Team).options(
            joinedload(Team.company),
            joinedload(Team.project),
            joinedload(Team.supervisor),
            joinedload(Team.users)
        ).filter(Team.project_id == uuid.UUID(project_id)).all()
        return TeamListResponse(
            teams=[TeamResponse.from_orm(team) for team in teams],
            total=len(teams)
        )
    except Exception as e:
        logger.error(f"Error fetching teams for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching teams: {str(e)}")

@router.post("/teams", response_model=TeamResponse)
async def create_team(team_info: TeamCreate, db: Session = Depends(get_db)):
    """Create a new team."""
    try:
        # Verify company exists
        company = db.query(Company).filter(Company.id == team_info.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Verify project exists if provided
        if team_info.project_id:
            project = db.query(Project).filter(Project.id == team_info.project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
        
        # Verify supervisor exists if provided
        if team_info.supervisor_id:
            supervisor = db.query(User).filter(User.id == team_info.supervisor_id).first()
            if not supervisor:
                raise HTTPException(status_code=404, detail="Supervisor not found")
        
        team = Team(
            id=uuid.uuid4(),
            name=team_info.name,
            company_id=team_info.company_id,
            project_id=team_info.project_id,
            supervisor_id=team_info.supervisor_id
        )
        
        db.add(team)
        db.commit()
        db.refresh(team)
        
        # Load related data for response
        team = db.query(Team).options(
            joinedload(Team.company),
            joinedload(Team.project),
            joinedload(Team.supervisor),
            joinedload(Team.users)
        ).filter(Team.id == team.id).first()
        
        logger.info(f"Created team: {team.name} with ID: {team.id}")
        return TeamResponse.from_orm(team)
        
    except Exception as e:
        logger.error(f"Error creating team: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating team: {str(e)}")

@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(team_id: str, team_update: TeamUpdate, db: Session = Depends(get_db)):
    """Update a team."""
    try:
        team = db.query(Team).filter(Team.id == uuid.UUID(team_id)).first()
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Update fields if provided
        if team_update.name is not None:
            team.name = team_update.name
        if team_update.company_id is not None:
            # Verify new company exists
            company = db.query(Company).filter(Company.id == team_update.company_id).first()
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")
            team.company_id = team_update.company_id
        if team_update.project_id is not None:
            # Verify new project exists
            project = db.query(Project).filter(Project.id == team_update.project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            team.project_id = team_update.project_id
        if team_update.supervisor_id is not None:
            # Verify new supervisor exists
            supervisor = db.query(User).filter(User.id == team_update.supervisor_id).first()
            if not supervisor:
                raise HTTPException(status_code=404, detail="Supervisor not found")
            team.supervisor_id = team_update.supervisor_id
        
        db.commit()
        db.refresh(team)
        
        # Load related data for response
        team = db.query(Team).options(
            joinedload(Team.company),
            joinedload(Team.project),
            joinedload(Team.supervisor),
            joinedload(Team.users)
        ).filter(Team.id == team.id).first()
        
        return TeamResponse.from_orm(team)
        
    except Exception as e:
        logger.error(f"Error updating team {team_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating team: {str(e)}")

@router.delete("/teams/{team_id}")
async def delete_team(team_id: str, db: Session = Depends(get_db)):
    """Delete a team."""
    try:
        team = db.query(Team).filter(Team.id == uuid.UUID(team_id)).first()
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        db.delete(team)
        db.commit()
        
        return {"message": "Team deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting team {team_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting team: {str(e)}") 