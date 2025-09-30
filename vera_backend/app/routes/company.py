import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.pydantic_models import (
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
)
from app.models.sql_models import Company

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/companies", response_model=CompanyListResponse)
async def get_companies(db: Session = Depends(get_db)):
    """Get all companies."""
    try:
        companies = db.query(Company).all()
        return CompanyListResponse(
            companies=[CompanyResponse.from_orm(company) for company in companies],
            total=len(companies),
        )
    except Exception as e:
        logger.error(f"Error fetching companies: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching companies: {str(e)}"
        )


@router.get("/companies/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str, db: Session = Depends(get_db)):
    """Get a specific company by ID."""
    try:
        company = db.query(Company).filter(Company.id == uuid.UUID(company_id)).first()

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        return CompanyResponse.from_orm(company)
    except Exception as e:
        logger.error(f"Error fetching company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching company: {str(e)}")


@router.post("/companies", response_model=CompanyResponse)
async def create_company(company_info: CompanyCreate, db: Session = Depends(get_db)):
    """Create a new company."""
    try:
        company = Company(
            id=uuid.uuid4(),
            name=company_info.name,
            company_profile=company_info.company_profile,
        )

        db.add(company)
        db.commit()
        db.refresh(company)

        logger.info(f"Created company: {company.name} with ID: {company.id}")
        return CompanyResponse.from_orm(company)

    except Exception as e:
        logger.error(f"Error creating company: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating company: {str(e)}")


@router.put("/companies/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str, company_update: CompanyUpdate, db: Session = Depends(get_db)
):
    """Update a company."""
    try:
        company = db.query(Company).filter(Company.id == uuid.UUID(company_id)).first()

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Update fields if provided
        if company_update.name is not None:
            company.name = company_update.name
        if company_update.company_profile is not None:
            company.company_profile = company_update.company_profile

        db.commit()
        db.refresh(company)

        return CompanyResponse.from_orm(company)

    except Exception as e:
        logger.error(f"Error updating company {company_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating company: {str(e)}")


@router.delete("/companies/{company_id}")
async def delete_company(company_id: str, db: Session = Depends(get_db)):
    """Delete a company."""
    try:
        company = db.query(Company).filter(Company.id == uuid.UUID(company_id)).first()

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        db.delete(company)
        db.commit()

        return {"message": "Company deleted successfully"}

    except Exception as e:
        logger.error(f"Error deleting company {company_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting company: {str(e)}")
