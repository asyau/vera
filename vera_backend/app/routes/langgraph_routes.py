"""
LangGraph Workflow API Routes
API endpoints for managing LangGraph workflows and integrated AI services
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.api_gateway import AuthenticationMiddleware
from app.core.dependencies import (
    AIServiceDep,
    CompanyDep,
    CurrentUserDep,
    RequestContextDep,
    WorkflowAccessDep,
    WorkflowServiceDep,
    require_authenticated,
    require_manager,
)
from app.database import get_db
from app.services.langgraph_integration import IntegratedAIService
from app.services.langgraph_workflows import WorkflowType

router = APIRouter()


# Background task functions
async def log_ai_request(
    user_id: uuid.UUID, company_id: uuid.UUID, request_type: str, message_length: int
):
    """Log AI request for analytics"""
    # This would typically log to analytics service
    print(
        f"AI Request: user={user_id}, company={company_id}, type={request_type}, length={message_length}"
    )


# Pydantic Models
class IntelligentRequestModel(BaseModel):
    message: str = Field(..., description="User message or request")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    force_workflow: Optional[str] = Field(
        None, description="Force specific workflow type"
    )
    max_iterations: Optional[int] = Field(10, description="Maximum workflow iterations")


class WorkflowContinuationModel(BaseModel):
    user_input: Optional[str] = Field(
        None, description="User input to continue workflow"
    )
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class WorkflowCreationModel(BaseModel):
    workflow_type: str = Field(..., description="Type of workflow to create")
    initial_data: Dict[str, Any] = Field(..., description="Initial workflow data")
    max_iterations: Optional[int] = Field(10, description="Maximum iterations")


class IntelligentResponse(BaseModel):
    response_type: str = Field(
        ..., description="Type of response (orchestrator or workflow)"
    )
    content: Optional[str] = Field(None, description="Response content")
    workflow_info: Optional[Dict[str, Any]] = Field(
        None, description="Workflow information"
    )
    intent_analysis: Optional[Dict[str, Any]] = Field(
        None, description="Intent analysis results"
    )
    message: str = Field(..., description="Human-readable message")
    next_steps: Optional[List[str]] = Field(None, description="Next steps in process")
    estimated_completion: Optional[Dict[str, Any]] = Field(
        None, description="Completion estimate"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    thread_id: str
    workflow_type: str
    state: Optional[Dict[str, Any]]
    progress: Dict[str, Any]
    can_continue: bool


class WorkflowListResponse(BaseModel):
    workflow_id: str
    workflow_type: str
    status: str
    created_at: str
    current_step: Optional[str]
    can_continue: bool
    workflow_description: str


# Main Intelligent AI Endpoint
@router.post("/intelligent", response_model=IntelligentResponse)
async def process_intelligent_request(
    request: IntelligentRequestModel,
    current_user: CurrentUserDep,
    company: CompanyDep,
    ai_service: AIServiceDep,
    context: RequestContextDep,
    background_tasks: BackgroundTasks,
):
    """
    Process user request with intelligent routing between orchestrator and workflows.
    Automatically determines whether to use simple orchestration or complex workflows.
    """
    try:
        # Parse force_workflow if provided
        force_workflow = None
        if request.force_workflow:
            try:
                force_workflow = WorkflowType(request.force_workflow)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid workflow type: {request.force_workflow}",
                )

        # Merge request context with dependency-injected context
        merged_context = {**context, **(request.context or {})}
        if request.max_iterations:
            merged_context["max_iterations"] = request.max_iterations

        # Add background task for analytics
        background_tasks.add_task(
            log_ai_request,
            user_id=current_user.id,
            company_id=company.id,
            request_type="intelligent",
            message_length=len(request.message),
        )

        # Process request with enhanced context
        result = await ai_service.process_intelligent_request(
            user_input=request.message,
            user_id=current_user.id,
            context=merged_context,
            force_workflow=force_workflow,
        )

        return IntelligentResponse(
            response_type=result.get("response_type", "orchestrator"),
            content=result.get("content"),
            workflow_info=result.get("workflow_info"),
            intent_analysis=result.get("intent_analysis"),
            message=result.get("message", result.get("content", "Request processed")),
            next_steps=result.get("next_steps"),
            estimated_completion=result.get("estimated_completion"),
            metadata=result.get("metadata"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Intelligent processing error: {str(e)}"
        )


# Workflow Management Endpoints
@router.post("/workflows", response_model=Dict[str, Any])
async def create_workflow(
    request: WorkflowCreationModel,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new workflow manually"""
    try:
        ai_service = IntegratedAIService(db)

        # Validate workflow type
        try:
            workflow_type = WorkflowType(request.workflow_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid workflow type: {request.workflow_type}",
            )

        # Add max_iterations to initial data
        initial_data = request.initial_data.copy()
        if request.max_iterations:
            initial_data["max_iterations"] = request.max_iterations

        # Create workflow
        result = await ai_service.workflow_service.start_workflow(
            workflow_type=workflow_type,
            user_id=uuid.UUID(current_user_id),
            initial_data=initial_data,
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Workflow creation error: {str(e)}"
        )


@router.get("/workflows", response_model=List[WorkflowListResponse])
async def list_workflows(
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """List all workflows for the current user"""
    try:
        ai_service = IntegratedAIService(db)
        workflows = await ai_service.list_user_workflows(uuid.UUID(current_user_id))

        return [
            WorkflowListResponse(
                workflow_id=w["workflow_id"],
                workflow_type=w["workflow_type"],
                status=w["status"],
                created_at=w["created_at"],
                current_step=w.get("current_step"),
                can_continue=w["can_continue"],
                workflow_description=w["workflow_description"],
            )
            for w in workflows
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list workflows: {str(e)}"
        )


@router.get("/workflows/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str = Path(..., description="Workflow ID"),
    thread_id: str = Query(..., description="Thread ID"),
    workflow_type: str = Query(..., description="Workflow type"),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get current status of a workflow"""
    try:
        ai_service = IntegratedAIService(db)

        # Validate workflow type
        try:
            wf_type = WorkflowType(workflow_type)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid workflow type: {workflow_type}"
            )

        status = await ai_service.get_workflow_status(workflow_id, thread_id, wf_type)

        return WorkflowStatusResponse(
            workflow_id=status["workflow_id"],
            thread_id=status["thread_id"],
            workflow_type=status["workflow_type"],
            state=status["state"],
            progress=status["progress"],
            can_continue=status["can_continue"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get workflow status: {str(e)}"
        )


@router.post("/workflows/{workflow_id}/continue", response_model=Dict[str, Any])
async def continue_workflow(
    workflow_id: str = Path(..., description="Workflow ID"),
    request: WorkflowContinuationModel = None,
    thread_id: str = Query(..., description="Thread ID"),
    workflow_type: str = Query(..., description="Workflow type"),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Continue an existing workflow"""
    try:
        ai_service = IntegratedAIService(db)

        # Validate workflow type
        try:
            wf_type = WorkflowType(workflow_type)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid workflow type: {workflow_type}"
            )

        # Continue workflow
        result = await ai_service.continue_workflow_session(
            workflow_id=workflow_id,
            thread_id=thread_id,
            workflow_type=wf_type,
            user_input=request.user_input if request else None,
            user_id=uuid.UUID(current_user_id),
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to continue workflow: {str(e)}"
        )


@router.delete("/workflows/{workflow_id}", response_model=Dict[str, Any])
async def cancel_workflow(
    workflow_id: str = Path(..., description="Workflow ID"),
    thread_id: str = Query(..., description="Thread ID"),
    workflow_type: str = Query(..., description="Workflow type"),
    reason: Optional[str] = Query(None, description="Cancellation reason"),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Cancel an active workflow"""
    try:
        ai_service = IntegratedAIService(db)

        # Validate workflow type
        try:
            wf_type = WorkflowType(workflow_type)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid workflow type: {workflow_type}"
            )

        result = await ai_service.cancel_workflow(
            workflow_id=workflow_id,
            thread_id=thread_id,
            workflow_type=wf_type,
            reason=reason,
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to cancel workflow: {str(e)}"
        )


# Information and Capabilities Endpoints
@router.get("/workflow-types", response_model=List[Dict[str, Any]])
async def get_workflow_types(
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get available workflow types and their descriptions"""
    try:
        ai_service = IntegratedAIService(db)
        return ai_service.workflow_service.get_workflow_types()

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get workflow types: {str(e)}"
        )


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_integration_capabilities(
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get capabilities of the integrated AI service"""
    try:
        ai_service = IntegratedAIService(db)
        return ai_service.get_integration_capabilities()

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get capabilities: {str(e)}"
        )


# Workflow Templates and Examples
@router.get("/workflow-templates", response_model=Dict[str, Any])
async def get_workflow_templates(
    workflow_type: Optional[str] = Query(None, description="Filter by workflow type"),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get workflow templates and examples"""

    templates = {
        "task_orchestration": {
            "name": "Task Orchestration",
            "description": "Create and manage multiple related tasks with dependencies",
            "example_requests": [
                "Create a project plan for launching our new product",
                "Break down the quarterly planning into manageable tasks",
                "Set up tasks for the website redesign project with proper dependencies",
            ],
            "template_data": {
                "task_requests": [
                    {
                        "title": "Research Phase",
                        "description": "Conduct market research and competitive analysis",
                        "priority": "high",
                        "estimated_duration": "1 week",
                    },
                    {
                        "title": "Design Phase",
                        "description": "Create wireframes and visual designs",
                        "priority": "medium",
                        "estimated_duration": "2 weeks",
                    },
                ],
                "assignees": ["research_team", "design_team"],
                "deadlines": ["2024-02-15", "2024-03-01"],
            },
        },
        "research_and_analysis": {
            "name": "Research & Analysis",
            "description": "Comprehensive research with parallel processing and synthesis",
            "example_requests": [
                "Research the latest trends in AI and machine learning",
                "Analyze our competitor's pricing strategies and market positioning",
                "Investigate the impact of remote work on team productivity",
            ],
            "template_data": {
                "research_query": "Latest trends in artificial intelligence and their business applications",
                "research_depth": "comprehensive",
                "include_analysis": True,
            },
        },
        "collaborative_planning": {
            "name": "Collaborative Planning",
            "description": "Multi-stakeholder planning with consensus building",
            "example_requests": [
                "Plan the company retreat with input from all departments",
                "Create a product roadmap involving engineering, marketing, and sales",
                "Develop a budget plan with stakeholder input",
            ],
            "template_data": {
                "planning_objective": "Plan Q2 product development priorities",
                "stakeholders": [
                    "product_manager",
                    "engineering_lead",
                    "marketing_director",
                ],
                "planning_horizon": "3_months",
            },
        },
        "iterative_refinement": {
            "name": "Iterative Refinement",
            "description": "Content improvement through quality gates and feedback loops",
            "example_requests": [
                "Write and refine a proposal for the new client project",
                "Create a high-quality blog post about our latest features",
                "Draft and improve the employee handbook section on remote work",
            ],
            "template_data": {
                "requirements": "Write a comprehensive guide for new team members",
                "content_type": "documentation",
                "quality_threshold": 8,
                "max_iterations": 5,
            },
        },
        "multi_step_automation": {
            "name": "Multi-Step Automation",
            "description": "Complex automation with step-by-step execution",
            "example_requests": [
                "Automate the onboarding process for new employees",
                "Set up automated reporting for monthly metrics",
                "Create an automated workflow for customer support tickets",
            ],
            "template_data": {
                "automation_request": "Automate the monthly report generation process",
                "execution_mode": "step_by_step",
                "verify_steps": True,
            },
        },
    }

    if workflow_type:
        if workflow_type in templates:
            return {workflow_type: templates[workflow_type]}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Template not found for workflow type: {workflow_type}",
            )

    return templates


# Health and Monitoring
@router.get("/health", response_model=Dict[str, Any])
async def get_service_health(
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get health status of LangGraph services"""
    try:
        ai_service = IntegratedAIService(db)

        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "orchestrator": "healthy",
                "workflow_service": "healthy",
                "database": "connected",
            },
            "workflow_types_available": len(
                ai_service.workflow_service.get_workflow_types()
            ),
            "integration_features_count": len(
                ai_service.get_integration_capabilities()["integration_features"]
            ),
        }

        return health_status

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


# Streaming endpoint for real-time workflow updates
@router.get("/workflows/{workflow_id}/stream")
async def stream_workflow_progress(
    workflow_id: str = Path(..., description="Workflow ID"),
    thread_id: str = Query(..., description="Thread ID"),
    workflow_type: str = Query(..., description="Workflow type"),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Stream real-time workflow progress updates (Server-Sent Events)"""

    # This would implement Server-Sent Events for real-time updates
    # For now, return a placeholder response

    return {
        "message": "Streaming endpoint placeholder",
        "note": "This would implement Server-Sent Events for real-time workflow progress updates",
        "workflow_id": workflow_id,
        "thread_id": thread_id,
        "workflow_type": workflow_type,
    }
