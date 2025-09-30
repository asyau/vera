import logging
import os
from datetime import datetime

import sentry_sdk
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# Load environment variables first
load_dotenv()

sentry_sdk.init(
    dsn="https://d436c015096491c747000cb1fd120cf3@o4509151357829120.ingest.de.sentry.io/4509151366676560",
    send_default_pii=True,
)

# Import after loading environment variables
from app.core.api_gateway import APIGateway
from app.core.config import settings
from app.routes import (
    company,
    conversation,
    integrations,
    langgraph_routes,
    messaging,
    openai_service,
    project,
    simple_auth,
    task,
    team,
    user,
)

# Create FastAPI app with enhanced configuration
app = FastAPI(
    title="Vira API Gateway",
    description="Microservices API Gateway for Vira AI Assistant Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize API Gateway
api_gateway = APIGateway(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Include routers with enhanced organization
# Core services
app.include_router(simple_auth.router, prefix="", tags=["Authentication"])
app.include_router(user.router, prefix="/api/users", tags=["User Management"])
app.include_router(company.router, prefix="/api/companies", tags=["Company Management"])
app.include_router(project.router, prefix="/api/projects", tags=["Project Management"])
app.include_router(team.router, prefix="/api/teams", tags=["Team Management"])

# Business logic services
app.include_router(task.router, prefix="/api/tasks", tags=["Task Management"])
app.include_router(
    conversation.router, prefix="/api/conversations", tags=["Communication"]
)
app.include_router(messaging.router, prefix="/api/messaging", tags=["Messaging"])

# AI services
app.include_router(openai_service.router, prefix="/api/ai", tags=["AI Orchestration"])
app.include_router(
    langgraph_routes.router, prefix="/api/workflows", tags=["LangGraph Workflows"]
)

# Integration services
app.include_router(
    integrations.router, prefix="/api/integrations", tags=["Third-party Integrations"]
)


# Health and status endpoints
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Welcome to Vira API Gateway",
        "version": "2.0.0",
        "architecture": "microservices",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Comprehensive health check including service dependencies"""
    from app.core.api_gateway import service_router

    # Check service health
    service_health = await service_router.get_healthy_services()

    overall_health = "healthy" if all(service_health.values()) else "degraded"

    return {
        "status": overall_health,
        "message": "API Gateway is running",
        "services": service_health,
        "timestamp": str(datetime.utcnow()),
    }


@app.get("/services", tags=["Health"])
async def service_status():
    """Get detailed service registry information"""
    from app.core.api_gateway import service_router

    return {
        "services": service_router.service_registry,
        "health_status": await service_router.get_healthy_services(),
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
