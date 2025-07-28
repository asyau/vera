from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List
import uuid
import logging

from app.models.sql_models import Project, Company
from app.models.pydantic_models import ProjectCreate, ProjectResponse, ProjectUpdate, ProjectListResponse
from app.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/projects", response_model=ProjectListResponse)
async def get_projects(db: Session = Depends(get_db)):
    """Get all projects."""
    try:
        projects = db.query(Project).options(joinedload(Project.company)).all()
        return ProjectListResponse(
            projects=[ProjectResponse.from_orm(project) for project in projects],
            total=len(projects)
        )
    except Exception as e:
        logger.error(f"Error fetching projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching projects: {str(e)}")

@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a specific project by ID."""
    try:
        project = db.query(Project).options(joinedload(Project.company)).filter(Project.id == uuid.UUID(project_id)).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return ProjectResponse.from_orm(project)
    except Exception as e:
        logger.error(f"Error fetching project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching project: {str(e)}")

@router.get("/companies/{company_id}/projects", response_model=ProjectListResponse)
async def get_company_projects(company_id: str, db: Session = Depends(get_db)):
    """Get all projects for a specific company."""
    try:
        projects = db.query(Project).options(joinedload(Project.company)).filter(Project.company_id == uuid.UUID(company_id)).all()
        return ProjectListResponse(
            projects=[ProjectResponse.from_orm(project) for project in projects],
            total=len(projects)
        )
    except Exception as e:
        logger.error(f"Error fetching projects for company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching projects: {str(e)}")

@router.post("/projects", response_model=ProjectResponse)
async def create_project(project_info: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    try:
        # Verify company exists
        company = db.query(Company).filter(Company.id == project_info.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        project = Project(
            id=uuid.uuid4(),
            name=project_info.name,
            description=project_info.description,
            company_id=project_info.company_id
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Load company info for response
        project = db.query(Project).options(joinedload(Project.company)).filter(Project.id == project.id).first()
        
        logger.info(f"Created project: {project.name} with ID: {project.id}")
        return ProjectResponse.from_orm(project)
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")

@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project_update: ProjectUpdate, db: Session = Depends(get_db)):
    """Update a project."""
    try:
        project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update fields if provided
        if project_update.name is not None:
            project.name = project_update.name
        if project_update.description is not None:
            project.description = project_update.description
        if project_update.company_id is not None:
            # Verify new company exists
            company = db.query(Company).filter(Company.id == project_update.company_id).first()
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")
            project.company_id = project_update.company_id
        
        db.commit()
        db.refresh(project)
        
        # Load company info for response
        project = db.query(Project).options(joinedload(Project.company)).filter(Project.id == project.id).first()
        
        return ProjectResponse.from_orm(project)
        
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating project: {str(e)}")

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project."""
    try:
        project = db.query(Project).filter(Project.id == uuid.UUID(project_id)).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        db.delete(project)
        db.commit()
        
        return {"message": "Project deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting project: {str(e)}") 