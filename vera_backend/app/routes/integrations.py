"""
Integration API Routes
FastAPI endpoints for managing third-party integrations
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import CompanyDep, CurrentUserDep
from app.database import get_db
from app.models.pydantic_models import (
    IntegrationCreate,
    IntegrationResponse,
    IntegrationUpdate,
)
from app.services.integrations.base_integration import (
    IntegrationStatus,
    IntegrationType,
)
from app.services.integrations.integration_manager import IntegrationManager

router = APIRouter()

# Request/Response Models


class IntegrationAuthUrlRequest(BaseModel):
    """Request model for getting OAuth authorization URL"""

    integration_type: str = Field(
        ..., description="Type of integration (slack, jira, etc.)"
    )
    redirect_uri: str = Field(..., description="OAuth redirect URI")
    auth_method: Optional[str] = Field(
        None, description="Authentication method (oauth, api_token, etc.)"
    )


class IntegrationAuthUrlResponse(BaseModel):
    """Response model for OAuth authorization URL"""

    success: bool
    authorization_url: Optional[str] = None
    setup_instructions: Optional[str] = None
    error: Optional[str] = None


class IntegrationCallbackRequest(BaseModel):
    """Request model for OAuth callback"""

    integration_type: str = Field(..., description="Type of integration")
    code: Optional[str] = Field(None, description="OAuth authorization code")
    state: Optional[str] = Field(None, description="OAuth state parameter")
    # Additional fields for API token setup
    email: Optional[str] = Field(None, description="Email for API token auth")
    api_token: Optional[str] = Field(None, description="API token")
    server_url: Optional[str] = Field(
        None, description="Server URL for self-hosted services"
    )
    auth_method: Optional[str] = Field(None, description="Authentication method")


class IntegrationSyncRequest(BaseModel):
    """Request model for integration sync"""

    sync_type: str = Field(
        "incremental", description="Type of sync (full, incremental)"
    )


class IntegrationConfigUpdateRequest(BaseModel):
    """Request model for updating integration configuration"""

    config_updates: Dict[str, Any] = Field(..., description="Configuration updates")


class WebhookRequest(BaseModel):
    """Generic webhook request model"""

    integration_type: str = Field(..., description="Type of integration")
    integration_id: uuid.UUID = Field(..., description="Integration ID")


# Integration Management Endpoints


@router.get("/available", response_model=List[Dict[str, Any]])
async def get_available_integrations(
    company: CompanyDep, db: Session = Depends(get_db)
):
    """Get list of all available integration types"""
    try:
        integration_manager = IntegrationManager(db)
        return integration_manager.get_available_integrations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[Dict[str, Any]])
async def list_company_integrations(company: CompanyDep, db: Session = Depends(get_db)):
    """Get all integrations for the current company"""
    try:
        integration_manager = IntegrationManager(db)
        return integration_manager.get_company_integrations(company.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Dict[str, Any])
async def get_integration_stats(company: CompanyDep, db: Session = Depends(get_db)):
    """Get integration statistics for the company"""
    try:
        integration_manager = IntegrationManager(db)
        return integration_manager.get_integration_stats(company.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth-url", response_model=IntegrationAuthUrlResponse)
async def get_authorization_url(
    request: IntegrationAuthUrlRequest,
    current_user: CurrentUserDep,
    company: CompanyDep,
    db: Session = Depends(get_db),
):
    """Get OAuth authorization URL for an integration"""
    try:
        # Validate integration type
        try:
            integration_type = IntegrationType(request.integration_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid integration type: {request.integration_type}",
            )

        integration_manager = IntegrationManager(db)
        result = integration_manager.get_authorization_url(
            integration_type=integration_type,
            company_id=company.id,
            user_id=current_user.id,
            redirect_uri=request.redirect_uri,
            auth_method=request.auth_method,
        )

        if result.get("success"):
            return IntegrationAuthUrlResponse(
                success=True, authorization_url=result.get("authorization_url")
            )
        else:
            return IntegrationAuthUrlResponse(success=False, error=result.get("error"))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/callback", response_model=Dict[str, Any])
async def handle_oauth_callback(
    request: IntegrationCallbackRequest, db: Session = Depends(get_db)
):
    """Handle OAuth callback for integration setup"""
    try:
        # Validate integration type
        try:
            integration_type = IntegrationType(request.integration_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid integration type: {request.integration_type}",
            )

        integration_manager = IntegrationManager(db)

        # Prepare kwargs for the callback handler
        kwargs = {
            "auth_method": request.auth_method,
            "email": request.email,
            "api_token": request.api_token,
            "server_url": request.server_url,
        }

        # Remove None values
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        result = integration_manager.handle_oauth_callback(
            integration_type=integration_type,
            code=request.code or "",
            state=request.state or "",
            **kwargs,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{integration_id}", response_model=Dict[str, Any])
async def get_integration(
    company: CompanyDep,
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    db: Session = Depends(get_db),
):
    """Get details for a specific integration"""
    try:
        integration_manager = IntegrationManager(db)

        # Get integration and verify it belongs to the company
        integrations = integration_manager.get_company_integrations(company.id)
        integration = next(
            (i for i in integrations if i["id"] == str(integration_id)), None
        )

        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")

        return integration

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/test", response_model=Dict[str, Any])
async def test_integration(
    company: CompanyDep,
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    db: Session = Depends(get_db),
):
    """Test an integration connection"""
    try:
        integration_manager = IntegrationManager(db)
        result = integration_manager.test_integration(integration_id)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/refresh", response_model=Dict[str, Any])
async def refresh_integration_credentials(
    company: CompanyDep,
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    db: Session = Depends(get_db),
):
    """Refresh integration credentials"""
    try:
        integration_manager = IntegrationManager(db)
        result = integration_manager.refresh_integration_credentials(integration_id)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/sync", response_model=Dict[str, Any])
async def sync_integration_data(
    request: IntegrationSyncRequest,
    company: CompanyDep,
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """Sync data for an integration"""
    try:
        integration_manager = IntegrationManager(db)

        # For full sync, run in background
        if request.sync_type == "full":
            background_tasks.add_task(
                _background_sync_integration, integration_id, request.sync_type, db
            )
            return {
                "success": True,
                "message": "Full sync started in background",
                "sync_type": request.sync_type,
            }
        else:
            # For incremental sync, run synchronously
            result = integration_manager.sync_integration_data(
                integration_id, request.sync_type
            )
            return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/disconnect", response_model=Dict[str, Any])
async def disconnect_integration(
    company: CompanyDep,
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    db: Session = Depends(get_db),
):
    """Disconnect an integration"""
    try:
        integration_manager = IntegrationManager(db)
        result = integration_manager.disconnect_integration(integration_id)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{integration_id}/config", response_model=Dict[str, Any])
async def update_integration_config(
    request: IntegrationConfigUpdateRequest,
    company: CompanyDep,
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    db: Session = Depends(get_db),
):
    """Update integration configuration"""
    try:
        integration_manager = IntegrationManager(db)
        result = integration_manager.update_integration_config(
            integration_id, request.config_updates
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{integration_id}/events", response_model=Dict[str, Any])
async def get_integration_events(
    company: CompanyDep,
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of events to return"),
    db: Session = Depends(get_db),
):
    """Get recent events for an integration"""
    try:
        integration_manager = IntegrationManager(db)
        result = integration_manager.get_integration_events(integration_id, limit)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Bulk Operations


@router.post("/sync-all", response_model=Dict[str, Any])
async def sync_all_integrations(
    request: IntegrationSyncRequest,
    company: CompanyDep,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Sync all integrations for the company"""
    try:
        integration_manager = IntegrationManager(db)

        # Always run bulk sync in background
        background_tasks.add_task(
            _background_sync_all_integrations, company.id, request.sync_type, db
        )

        return {
            "success": True,
            "message": f"Bulk {request.sync_type} sync started in background",
            "sync_type": request.sync_type,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Webhook Endpoints


@router.post("/webhooks/slack/{integration_id}")
async def handle_slack_webhook(
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Handle Slack webhook"""
    try:
        # Get request body and headers
        payload = await request.json()
        headers = dict(request.headers)

        integration_manager = IntegrationManager(db)
        result = integration_manager.handle_webhook(
            IntegrationType.SLACK, integration_id, payload, headers
        )

        # Slack expects specific response format for some events
        if payload.get("type") == "url_verification":
            return {"challenge": payload.get("challenge")}

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/jira/{integration_id}")
async def handle_jira_webhook(
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Handle Jira webhook"""
    try:
        payload = await request.json()
        headers = dict(request.headers)

        integration_manager = IntegrationManager(db)
        result = integration_manager.handle_webhook(
            IntegrationType.JIRA, integration_id, payload, headers
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/google/{integration_id}")
async def handle_google_webhook(
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Handle Google Calendar webhook"""
    try:
        # Google Calendar sends notifications as headers, not JSON body
        headers = dict(request.headers)
        payload = {}

        # Try to get JSON body if present
        try:
            payload = await request.json()
        except:
            pass

        integration_manager = IntegrationManager(db)
        result = integration_manager.handle_webhook(
            IntegrationType.GOOGLE_CALENDAR, integration_id, payload, headers
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/microsoft/{integration_id}")
async def handle_microsoft_webhook(
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Handle Microsoft Graph webhook"""
    try:
        payload = await request.json()
        headers = dict(request.headers)

        # Handle subscription validation
        validation_token = headers.get("validationtoken")
        if validation_token:
            return {"validationResponse": validation_token}

        integration_manager = IntegrationManager(db)
        result = integration_manager.handle_webhook(
            IntegrationType.MICROSOFT_TEAMS, integration_id, payload, headers
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Service-Specific Endpoints


@router.get("/slack/{integration_id}/channels", response_model=Dict[str, Any])
async def get_slack_channels(
    company: CompanyDep,
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    db: Session = Depends(get_db),
):
    """Get Slack channels for an integration"""
    try:
        integration_manager = IntegrationManager(db)
        service = integration_manager.get_service(IntegrationType.SLACK)

        if not service:
            raise HTTPException(status_code=404, detail="Slack service not available")

        # Check if service has the method
        if not hasattr(service, "get_channels"):
            raise HTTPException(
                status_code=501, detail="Method not implemented for this service"
            )

        result = service.get_channels(integration_id)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jira/{integration_id}/projects", response_model=Dict[str, Any])
async def get_jira_projects(
    company: CompanyDep,
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    db: Session = Depends(get_db),
):
    """Get Jira projects for an integration"""
    try:
        integration_manager = IntegrationManager(db)
        service = integration_manager.get_service(IntegrationType.JIRA)

        if not service:
            raise HTTPException(status_code=404, detail="Jira service not available")

        # Check if service has the method
        if not hasattr(service, "get_projects"):
            raise HTTPException(
                status_code=501, detail="Method not implemented for this service"
            )

        result = service.get_projects(integration_id)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google/{integration_id}/calendars", response_model=Dict[str, Any])
async def get_google_calendars(
    company: CompanyDep,
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    db: Session = Depends(get_db),
):
    """Get Google calendars for an integration"""
    try:
        integration_manager = IntegrationManager(db)
        service = integration_manager.get_service(IntegrationType.GOOGLE_CALENDAR)

        if not service:
            raise HTTPException(status_code=404, detail="Google service not available")

        # Check if service has the method
        if not hasattr(service, "get_calendars"):
            raise HTTPException(
                status_code=501, detail="Method not implemented for this service"
            )

        result = service.get_calendars(integration_id)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google/{integration_id}/events", response_model=Dict[str, Any])
async def get_google_calendar_events(
    company: CompanyDep,
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    start_date: Optional[str] = Query(None, description="Start date in ISO format"),
    end_date: Optional[str] = Query(None, description="End date in ISO format"),
    db: Session = Depends(get_db),
):
    """Get Google Calendar events for an integration"""
    try:
        integration_manager = IntegrationManager(db)
        service = integration_manager.get_service(IntegrationType.GOOGLE_CALENDAR)

        if not service:
            raise HTTPException(
                status_code=404, detail="Google Calendar service not available"
            )

        # Check if service has the method
        if not hasattr(service, "get_calendar_events"):
            raise HTTPException(
                status_code=501, detail="Method not implemented for this service"
            )

        result = service.get_calendar_events(integration_id, start_date, end_date)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/microsoft/{integration_id}/teams", response_model=Dict[str, Any])
async def get_microsoft_teams(
    company: CompanyDep,
    integration_id: uuid.UUID = Path(..., description="Integration ID"),
    db: Session = Depends(get_db),
):
    """Get Microsoft Teams for an integration"""
    try:
        integration_manager = IntegrationManager(db)
        service = integration_manager.get_service(IntegrationType.MICROSOFT_TEAMS)

        if not service:
            raise HTTPException(
                status_code=404, detail="Microsoft service not available"
            )

        # Check if service has the method
        if not hasattr(service, "get_teams"):
            raise HTTPException(
                status_code=501, detail="Method not implemented for this service"
            )

        result = service.get_teams(integration_id)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Background Task Functions


async def _background_sync_integration(
    integration_id: uuid.UUID, sync_type: str, db: Session
):
    """Background task for syncing a single integration"""
    try:
        integration_manager = IntegrationManager(db)
        result = integration_manager.sync_integration_data(integration_id, sync_type)

        # Log the result (in production, you might want to store this in a job queue/database)
        print(f"Background sync completed for integration {integration_id}: {result}")

    except Exception as e:
        print(f"Background sync failed for integration {integration_id}: {str(e)}")


async def _background_sync_all_integrations(
    company_id: uuid.UUID, sync_type: str, db: Session
):
    """Background task for syncing all company integrations"""
    try:
        integration_manager = IntegrationManager(db)
        result = integration_manager.sync_all_company_integrations(
            company_id, sync_type
        )

        # Log the result
        print(f"Background sync all completed for company {company_id}: {result}")

    except Exception as e:
        print(f"Background sync all failed for company {company_id}: {str(e)}")
