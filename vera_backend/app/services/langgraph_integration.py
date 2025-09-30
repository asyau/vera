"""
LangGraph Integration Service
Integrates LangGraph workflows with the existing LangChain orchestrator
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AIServiceError, ValidationError
from app.models.sql_models import User
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService
from app.services.langchain_orchestrator import IntentType, LangChainOrchestrator
from app.services.langgraph_workflows import (
    LangGraphWorkflowService,
    WorkflowState,
    WorkflowType,
)


class WorkflowTrigger(Enum):
    """Triggers that can initiate workflows"""

    COMPLEX_TASK_REQUEST = "complex_task_request"
    RESEARCH_QUERY = "research_query"
    PLANNING_REQUEST = "planning_request"
    CONTENT_CREATION = "content_creation"
    AUTOMATION_REQUEST = "automation_request"
    MULTI_AGENT_COLLABORATION = "multi_agent_collaboration"


class IntegratedAIService(BaseService):
    """
    Integrated AI service that combines LangChain orchestration with LangGraph workflows
    """

    def __init__(self, db: Session):
        super().__init__(db)

        # Initialize core services
        self.orchestrator = LangChainOrchestrator(db)
        self.workflow_service = LangGraphWorkflowService(db)
        self.user_repo = UserRepository(db)

        # Workflow trigger mappings
        self.workflow_triggers = self._initialize_workflow_triggers()

    def _initialize_workflow_triggers(self) -> Dict[WorkflowTrigger, Dict[str, Any]]:
        """Initialize workflow trigger configurations"""

        return {
            WorkflowTrigger.COMPLEX_TASK_REQUEST: {
                "workflow_type": WorkflowType.TASK_ORCHESTRATION,
                "intent_patterns": [
                    "create multiple tasks",
                    "complex project",
                    "task dependencies",
                ],
                "confidence_threshold": 0.8,
                "keywords": [
                    "multiple",
                    "complex",
                    "dependencies",
                    "project",
                    "breakdown",
                ],
            },
            WorkflowTrigger.RESEARCH_QUERY: {
                "workflow_type": WorkflowType.RESEARCH_AND_ANALYSIS,
                "intent_patterns": [
                    "research",
                    "analyze",
                    "investigate",
                    "comprehensive study",
                ],
                "confidence_threshold": 0.7,
                "keywords": [
                    "research",
                    "analyze",
                    "study",
                    "investigate",
                    "report",
                    "findings",
                ],
            },
            WorkflowTrigger.PLANNING_REQUEST: {
                "workflow_type": WorkflowType.COLLABORATIVE_PLANNING,
                "intent_patterns": ["plan", "strategy", "roadmap", "collaborate"],
                "confidence_threshold": 0.75,
                "keywords": [
                    "plan",
                    "strategy",
                    "roadmap",
                    "team",
                    "collaborate",
                    "stakeholders",
                ],
            },
            WorkflowTrigger.CONTENT_CREATION: {
                "workflow_type": WorkflowType.ITERATIVE_REFINEMENT,
                "intent_patterns": ["create", "write", "draft", "improve", "refine"],
                "confidence_threshold": 0.7,
                "keywords": [
                    "create",
                    "write",
                    "draft",
                    "document",
                    "improve",
                    "refine",
                    "quality",
                ],
            },
            WorkflowTrigger.AUTOMATION_REQUEST: {
                "workflow_type": WorkflowType.MULTI_STEP_AUTOMATION,
                "intent_patterns": ["automate", "process", "workflow", "steps"],
                "confidence_threshold": 0.8,
                "keywords": [
                    "automate",
                    "process",
                    "workflow",
                    "steps",
                    "sequence",
                    "execute",
                ],
            },
        }

    async def process_intelligent_request(
        self,
        user_input: str,
        user_id: UUID,
        context: Optional[Dict[str, Any]] = None,
        force_workflow: Optional[WorkflowType] = None,
    ) -> Dict[str, Any]:
        """
        Process user request with intelligent routing between orchestrator and workflows
        """

        try:
            # First, analyze intent using the orchestrator
            user_context = await self.orchestrator._get_user_context(user_id)
            intent_analysis = await self.orchestrator._analyze_user_intent(
                user_input, user_context
            )

            # Determine if this should trigger a workflow
            workflow_decision = await self._should_trigger_workflow(
                user_input, intent_analysis, force_workflow
            )

            if workflow_decision["trigger_workflow"]:
                # Start appropriate workflow
                return await self._initiate_workflow(
                    workflow_decision["workflow_type"],
                    user_input,
                    user_id,
                    intent_analysis,
                    context,
                )
            else:
                # Use standard orchestrator
                return await self.orchestrator.process_user_request(
                    user_input, user_id, context
                )

        except Exception as e:
            raise AIServiceError(f"Failed to process intelligent request: {str(e)}")

    async def _should_trigger_workflow(
        self,
        user_input: str,
        intent_analysis: Dict[str, Any],
        force_workflow: Optional[WorkflowType] = None,
    ) -> Dict[str, Any]:
        """Determine if user request should trigger a workflow"""

        if force_workflow:
            return {
                "trigger_workflow": True,
                "workflow_type": force_workflow,
                "confidence": 1.0,
                "reason": "forced_workflow",
            }

        # Analyze complexity and workflow indicators
        complexity = intent_analysis.get("complexity", "low")
        estimated_steps = intent_analysis.get("estimated_steps", 1)
        entities = intent_analysis.get("entities", {})

        # Check for workflow trigger patterns
        user_input_lower = user_input.lower()

        best_match = None
        best_score = 0

        for trigger, config in self.workflow_triggers.items():
            score = 0

            # Check keyword matches
            keyword_matches = sum(
                1 for keyword in config["keywords"] if keyword in user_input_lower
            )
            score += keyword_matches * 0.3

            # Check pattern matches
            pattern_matches = sum(
                1
                for pattern in config["intent_patterns"]
                if pattern in user_input_lower
            )
            score += pattern_matches * 0.4

            # Complexity bonus
            if complexity in ["high", "medium"] and estimated_steps > 3:
                score += 0.2

            # Entity complexity bonus
            if (
                len(entities.get("tasks", [])) > 1
                or len(entities.get("people", [])) > 2
            ):
                score += 0.1

            if score > best_score and score >= config["confidence_threshold"]:
                best_score = score
                best_match = {
                    "trigger": trigger,
                    "workflow_type": config["workflow_type"],
                    "confidence": score,
                }

        if best_match:
            return {
                "trigger_workflow": True,
                "workflow_type": best_match["workflow_type"],
                "confidence": best_match["confidence"],
                "reason": f"matched_trigger_{best_match['trigger'].value}",
            }

        return {
            "trigger_workflow": False,
            "workflow_type": None,
            "confidence": 0.0,
            "reason": "no_workflow_trigger_detected",
        }

    async def _initiate_workflow(
        self,
        workflow_type: WorkflowType,
        user_input: str,
        user_id: UUID,
        intent_analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Initiate appropriate workflow based on type"""

        # Prepare workflow-specific initial data
        initial_data = await self._prepare_workflow_data(
            workflow_type, user_input, intent_analysis, context
        )

        # Start workflow
        workflow_result = await self.workflow_service.start_workflow(
            workflow_type=workflow_type, user_id=user_id, initial_data=initial_data
        )

        # Return integrated response
        return {
            "response_type": "workflow_initiated",
            "workflow_info": workflow_result,
            "intent_analysis": intent_analysis,
            "message": f"I've initiated a {workflow_type.value.replace('_', ' ')} workflow to handle your request comprehensively.",
            "next_steps": await self._get_workflow_next_steps(workflow_type),
            "estimated_completion": await self._estimate_workflow_completion(
                workflow_type, initial_data
            ),
        }

    async def _prepare_workflow_data(
        self,
        workflow_type: WorkflowType,
        user_input: str,
        intent_analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Prepare initial data for workflow based on type"""

        base_data = {
            "original_request": user_input,
            "intent_analysis": intent_analysis,
            "context": context or {},
            "max_iterations": 10,
        }

        if workflow_type == WorkflowType.TASK_ORCHESTRATION:
            # Extract task requests from input
            entities = intent_analysis.get("entities", {})
            tasks = entities.get("tasks", [])

            if not tasks:
                # Use LLM to extract tasks
                tasks = await self._extract_task_requests(user_input)

            base_data.update(
                {
                    "task_requests": tasks,
                    "assignees": entities.get("people", []),
                    "deadlines": entities.get("dates", []),
                }
            )

        elif workflow_type == WorkflowType.RESEARCH_AND_ANALYSIS:
            base_data.update(
                {
                    "research_query": user_input,
                    "research_depth": "comprehensive",
                    "include_analysis": True,
                }
            )

        elif workflow_type == WorkflowType.COLLABORATIVE_PLANNING:
            # Extract stakeholders and planning objective
            entities = intent_analysis.get("entities", {})
            stakeholders = entities.get("people", ["team_lead", "project_manager"])

            base_data.update(
                {
                    "planning_objective": user_input,
                    "stakeholders": stakeholders,
                    "planning_horizon": context.get("planning_horizon", "3_months"),
                }
            )

        elif workflow_type == WorkflowType.ITERATIVE_REFINEMENT:
            base_data.update(
                {
                    "requirements": user_input,
                    "content_type": context.get("content_type", "document"),
                    "quality_threshold": 8,
                    "max_iterations": 5,
                }
            )

        elif workflow_type == WorkflowType.MULTI_STEP_AUTOMATION:
            base_data.update(
                {
                    "automation_request": user_input,
                    "execution_mode": "step_by_step",
                    "verify_steps": True,
                }
            )

        return base_data

    async def _extract_task_requests(self, user_input: str) -> List[Dict[str, Any]]:
        """Extract task requests from user input using LLM"""

        # Use the orchestrator's LLM to extract tasks
        messages = [
            {
                "role": "system",
                "content": """Extract task requests from the user input.
            Return a JSON array of task objects with: title, description, priority, estimated_duration.
            If input doesn't contain clear tasks, create logical task breakdown.""",
            },
            {"role": "user", "content": user_input},
        ]

        try:
            response = await self.orchestrator.llm.ainvoke(
                [{"role": msg["role"], "content": msg["content"]} for msg in messages]
            )

            import json

            tasks = json.loads(response.content)
            return tasks if isinstance(tasks, list) else [tasks]

        except Exception:
            # Fallback to single task
            return [
                {
                    "title": "Main Task",
                    "description": user_input,
                    "priority": "medium",
                    "estimated_duration": "2 hours",
                }
            ]

    async def _get_workflow_next_steps(self, workflow_type: WorkflowType) -> List[str]:
        """Get next steps description for workflow type"""

        next_steps = {
            WorkflowType.TASK_ORCHESTRATION: [
                "Analyzing task complexity and dependencies",
                "Creating optimized task breakdown",
                "Assigning tasks to appropriate team members",
                "Setting up progress tracking",
            ],
            WorkflowType.RESEARCH_AND_ANALYSIS: [
                "Planning comprehensive research approach",
                "Conducting parallel research across key areas",
                "Analyzing findings and identifying patterns",
                "Synthesizing results into actionable insights",
            ],
            WorkflowType.COLLABORATIVE_PLANNING: [
                "Setting up planning framework",
                "Gathering input from all stakeholders",
                "Identifying consensus areas and conflicts",
                "Creating unified collaborative plan",
            ],
            WorkflowType.ITERATIVE_REFINEMENT: [
                "Generating initial content draft",
                "Evaluating quality against requirements",
                "Iteratively refining based on feedback",
                "Finalizing high-quality output",
            ],
            WorkflowType.MULTI_STEP_AUTOMATION: [
                "Analyzing automation requirements",
                "Creating step-by-step execution plan",
                "Executing each step with verification",
                "Providing comprehensive results summary",
            ],
        }

        return next_steps.get(workflow_type, ["Processing your request..."])

    async def _estimate_workflow_completion(
        self, workflow_type: WorkflowType, initial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate workflow completion time"""

        base_estimates = {
            WorkflowType.TASK_ORCHESTRATION: {"min": 2, "max": 10, "unit": "minutes"},
            WorkflowType.RESEARCH_AND_ANALYSIS: {
                "min": 5,
                "max": 20,
                "unit": "minutes",
            },
            WorkflowType.COLLABORATIVE_PLANNING: {
                "min": 10,
                "max": 30,
                "unit": "minutes",
            },
            WorkflowType.ITERATIVE_REFINEMENT: {"min": 3, "max": 15, "unit": "minutes"},
            WorkflowType.MULTI_STEP_AUTOMATION: {
                "min": 5,
                "max": 25,
                "unit": "minutes",
            },
        }

        estimate = base_estimates.get(
            workflow_type, {"min": 5, "max": 15, "unit": "minutes"}
        )

        # Adjust based on complexity
        complexity_multiplier = 1.0
        if initial_data.get("max_iterations", 0) > 10:
            complexity_multiplier = 1.5

        return {
            "estimated_min": int(estimate["min"] * complexity_multiplier),
            "estimated_max": int(estimate["max"] * complexity_multiplier),
            "unit": estimate["unit"],
            "note": "Estimates may vary based on complexity and external dependencies",
        }

    async def continue_workflow_session(
        self,
        workflow_id: str,
        thread_id: str,
        workflow_type: WorkflowType,
        user_input: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Continue an existing workflow session"""

        try:
            # Prepare user input for workflow continuation
            continuation_data = {}
            if user_input:
                continuation_data = {
                    "user_input": user_input,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Continue workflow
            result = await self.workflow_service.continue_workflow(
                workflow_id=workflow_id,
                thread_id=thread_id,
                workflow_type=workflow_type,
                user_input=continuation_data,
            )

            return {
                "response_type": "workflow_continued",
                "workflow_info": result,
                "status": result.get("status"),
                "current_step": result.get("current_step"),
            }

        except Exception as e:
            raise AIServiceError(f"Failed to continue workflow session: {str(e)}")

    async def get_workflow_status(
        self, workflow_id: str, thread_id: str, workflow_type: WorkflowType
    ) -> Dict[str, Any]:
        """Get current workflow status and state"""

        try:
            state = await self.workflow_service.get_workflow_state(
                thread_id, workflow_type
            )

            return {
                "workflow_id": workflow_id,
                "thread_id": thread_id,
                "workflow_type": workflow_type.value,
                "state": state,
                "progress": self._calculate_workflow_progress(state),
                "can_continue": state.get("state", {}).get("status") == "running",
            }

        except Exception as e:
            raise AIServiceError(f"Failed to get workflow status: {str(e)}")

    def _calculate_workflow_progress(
        self, state_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate workflow progress percentage"""

        state = state_info.get("state", {})
        completed_steps = state.get("completed_steps", [])
        current_step = state.get("current_step", "")

        # Estimate total steps based on workflow type
        total_steps_estimate = {
            "task_orchestration": 4,
            "research_and_analysis": 5,
            "collaborative_planning": 4,
            "iterative_refinement": 6,
            "multi_step_automation": 5,
        }

        workflow_type = state_info.get("workflow_type", "unknown")
        total_steps = total_steps_estimate.get(workflow_type, 5)

        progress_percentage = min(100, (len(completed_steps) / total_steps) * 100)

        return {
            "percentage": round(progress_percentage, 1),
            "completed_steps": len(completed_steps),
            "total_estimated_steps": total_steps,
            "current_step": current_step,
            "status": state.get("status", "unknown"),
        }

    async def list_user_workflows(self, user_id: UUID) -> List[Dict[str, Any]]:
        """List all workflows for a user"""

        try:
            # Get workflows from workflow service
            workflows = await self.workflow_service.list_active_workflows(user_id)

            # Enhance with additional information
            enhanced_workflows = []
            for workflow in workflows:
                enhanced = {
                    **workflow,
                    "can_continue": workflow.get("status") == "running",
                    "workflow_description": self._get_workflow_description(
                        workflow.get("workflow_type")
                    ),
                }
                enhanced_workflows.append(enhanced)

            return enhanced_workflows

        except Exception as e:
            raise AIServiceError(f"Failed to list user workflows: {str(e)}")

    def _get_workflow_description(self, workflow_type: str) -> str:
        """Get human-readable description of workflow type"""

        descriptions = {
            "task_orchestration": "Intelligent task creation and management with dependency analysis",
            "research_and_analysis": "Comprehensive research with parallel processing and synthesis",
            "collaborative_planning": "Multi-stakeholder planning with consensus building",
            "iterative_refinement": "Content improvement through quality gates and feedback loops",
            "multi_step_automation": "Complex automation with step-by-step execution and verification",
        }

        return descriptions.get(workflow_type, "Advanced AI workflow")

    async def cancel_workflow(
        self,
        workflow_id: str,
        thread_id: str,
        workflow_type: WorkflowType,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Cancel an active workflow"""

        try:
            result = await self.workflow_service.cancel_workflow(
                workflow_id=workflow_id,
                thread_id=thread_id,
                workflow_type=workflow_type,
            )

            return {
                "response_type": "workflow_cancelled",
                "workflow_info": result,
                "reason": reason or "User requested cancellation",
                "cancelled_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            raise AIServiceError(f"Failed to cancel workflow: {str(e)}")

    def get_integration_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of the integrated AI service"""

        return {
            "orchestrator_capabilities": self.orchestrator.get_agent_stats(),
            "workflow_types": self.workflow_service.get_workflow_types(),
            "integration_features": [
                "intelligent_workflow_routing",
                "seamless_orchestrator_fallback",
                "stateful_workflow_management",
                "multi_agent_collaboration",
                "parallel_processing",
                "iterative_refinement",
                "progress_tracking",
                "workflow_resumption",
            ],
            "supported_triggers": [trigger.value for trigger in WorkflowTrigger],
            "max_concurrent_workflows": 10,
            "persistence_enabled": True,
        }
