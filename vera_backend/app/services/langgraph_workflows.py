"""
LangGraph Workflows Service
Implements sophisticated stateful multi-agent workflows using LangGraph
"""
import json
import operator
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict
from uuid import UUID, uuid4

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command, Send
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AIServiceError, ValidationError
from app.models.sql_models import Company, Task, User
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


class WorkflowType(Enum):
    """Types of workflows available"""

    TASK_ORCHESTRATION = "task_orchestration"
    RESEARCH_AND_ANALYSIS = "research_and_analysis"
    COLLABORATIVE_PLANNING = "collaborative_planning"
    ITERATIVE_REFINEMENT = "iterative_refinement"
    MULTI_STEP_AUTOMATION = "multi_step_automation"


class WorkflowState(TypedDict):
    """Base state for all workflows"""

    workflow_id: str
    user_id: str
    messages: List[Dict[str, Any]]
    current_step: str
    completed_steps: List[str]
    workflow_data: Dict[str, Any]
    error_count: int
    max_iterations: int
    status: Literal["running", "completed", "failed", "paused"]


class TaskOrchestrationState(WorkflowState):
    """State for task orchestration workflows"""

    task_requests: List[Dict[str, Any]]
    created_tasks: Annotated[List[Dict[str, Any]], operator.add]
    assigned_users: List[str]
    dependencies: Dict[str, List[str]]
    priority_analysis: Optional[Dict[str, Any]]


class ResearchAnalysisState(WorkflowState):
    """State for research and analysis workflows"""

    research_query: str
    research_sections: List[Dict[str, Any]]
    completed_sections: Annotated[List[str], operator.add]
    analysis_results: Dict[str, Any]
    final_report: Optional[str]


class CollaborativePlanningState(WorkflowState):
    """State for collaborative planning workflows"""

    planning_objective: str
    stakeholders: List[str]
    plan_sections: List[Dict[str, Any]]
    feedback_rounds: Annotated[List[Dict[str, Any]], operator.add]
    consensus_items: List[str]
    final_plan: Optional[str]


class LangGraphWorkflowService(BaseService):
    """Service for managing LangGraph-based workflows"""

    def __init__(self, db: Session, checkpointer: Optional[Any] = None):
        super().__init__(db)
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.7,
            api_key=settings.openai_api_key,
        )

        # Use PostgreSQL checkpointer if available, otherwise memory
        self.checkpointer = checkpointer or MemorySaver()

        # Initialize repositories
        self.task_repo = TaskRepository(db)
        self.user_repo = UserRepository(db)

        # Initialize workflow graphs
        self.workflows = self._initialize_workflows()

    def _initialize_workflows(self) -> Dict[WorkflowType, Any]:
        """Initialize all workflow graphs"""
        workflows = {}

        # Task Orchestration Workflow
        workflows[
            WorkflowType.TASK_ORCHESTRATION
        ] = self._create_task_orchestration_workflow()

        # Research and Analysis Workflow
        workflows[
            WorkflowType.RESEARCH_AND_ANALYSIS
        ] = self._create_research_analysis_workflow()

        # Collaborative Planning Workflow
        workflows[
            WorkflowType.COLLABORATIVE_PLANNING
        ] = self._create_collaborative_planning_workflow()

        # Iterative Refinement Workflow
        workflows[
            WorkflowType.ITERATIVE_REFINEMENT
        ] = self._create_iterative_refinement_workflow()

        # Multi-step Automation Workflow
        workflows[
            WorkflowType.MULTI_STEP_AUTOMATION
        ] = self._create_multi_step_automation_workflow()

        return workflows

    async def start_workflow(
        self,
        workflow_type: WorkflowType,
        user_id: UUID,
        initial_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Start a new workflow"""

        try:
            workflow_id = str(uuid4())
            thread_id = f"workflow_{workflow_id}"

            # Get workflow graph
            workflow_graph = self.workflows[workflow_type]

            # Prepare initial state based on workflow type
            initial_state = await self._prepare_initial_state(
                workflow_type, workflow_id, user_id, initial_data
            )

            # Configure workflow execution
            workflow_config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": initial_data.get("max_iterations", 50),
            }
            if config:
                workflow_config.update(config)

            # Start workflow execution
            result = await workflow_graph.ainvoke(initial_state, config=workflow_config)

            return {
                "workflow_id": workflow_id,
                "thread_id": thread_id,
                "workflow_type": workflow_type.value,
                "status": result.get("status", "running"),
                "current_step": result.get("current_step"),
                "result": result,
            }

        except Exception as e:
            raise AIServiceError(f"Failed to start workflow: {str(e)}")

    async def continue_workflow(
        self,
        workflow_id: str,
        thread_id: str,
        workflow_type: WorkflowType,
        user_input: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Continue an existing workflow"""

        try:
            workflow_graph = self.workflows[workflow_type]

            # Configure workflow execution
            workflow_config = {"configurable": {"thread_id": thread_id}}
            if config:
                workflow_config.update(config)

            # Continue workflow with user input if provided
            if user_input:
                result = await workflow_graph.ainvoke(
                    user_input, config=workflow_config
                )
            else:
                # Resume from checkpoint
                result = await workflow_graph.ainvoke(None, config=workflow_config)

            return {
                "workflow_id": workflow_id,
                "thread_id": thread_id,
                "workflow_type": workflow_type.value,
                "status": result.get("status", "running"),
                "current_step": result.get("current_step"),
                "result": result,
            }

        except Exception as e:
            raise AIServiceError(f"Failed to continue workflow: {str(e)}")

    async def get_workflow_state(
        self, thread_id: str, workflow_type: WorkflowType
    ) -> Dict[str, Any]:
        """Get current workflow state"""

        try:
            workflow_graph = self.workflows[workflow_type]

            # Get state from checkpointer
            config = {"configurable": {"thread_id": thread_id}}
            state = await workflow_graph.aget_state(config)

            return {
                "thread_id": thread_id,
                "workflow_type": workflow_type.value,
                "state": state.values if state else None,
                "next_steps": state.next if state else [],
                "checkpoint": state.config if state else None,
            }

        except Exception as e:
            raise AIServiceError(f"Failed to get workflow state: {str(e)}")

    def _create_task_orchestration_workflow(self) -> Any:
        """Create task orchestration workflow with parallel task creation and dependency management"""

        def analyze_task_requests(
            state: TaskOrchestrationState,
        ) -> TaskOrchestrationState:
            """Analyze incoming task requests and determine optimal structure"""

            messages = [
                SystemMessage(
                    content="""You are a task orchestration specialist. Analyze task requests and:
                1. Break down complex tasks into manageable subtasks
                2. Identify dependencies between tasks
                3. Suggest optimal priority levels
                4. Recommend appropriate assignees based on skills

                Return structured analysis with clear task breakdown."""
                ),
                HumanMessage(
                    content=f"Task requests: {json.dumps(state['task_requests'])}"
                ),
            ]

            response = self.llm.invoke(messages)

            try:
                # Parse structured response
                analysis = json.loads(response.content)
                return {
                    **state,
                    "priority_analysis": analysis,
                    "current_step": "create_tasks",
                    "completed_steps": state["completed_steps"]
                    + ["analyze_task_requests"],
                }
            except json.JSONDecodeError:
                return {
                    **state,
                    "priority_analysis": {"raw_analysis": response.content},
                    "current_step": "create_tasks",
                    "completed_steps": state["completed_steps"]
                    + ["analyze_task_requests"],
                }

        def create_task_batch(state: TaskOrchestrationState) -> TaskOrchestrationState:
            """Create tasks in parallel based on analysis"""

            if not state.get("priority_analysis"):
                return {
                    **state,
                    "status": "failed",
                    "error_count": state["error_count"] + 1,
                }

            # Simulate task creation (integrate with actual TaskRepository)
            created_tasks = []
            for i, task_request in enumerate(state["task_requests"]):
                task_data = {
                    "id": str(uuid4()),
                    "title": task_request.get("title", f"Task {i+1}"),
                    "description": task_request.get("description", ""),
                    "priority": task_request.get("priority", "medium"),
                    "status": "created",
                    "created_at": datetime.utcnow().isoformat(),
                }
                created_tasks.append(task_data)

            return {
                **state,
                "created_tasks": created_tasks,
                "current_step": "assign_tasks",
                "completed_steps": state["completed_steps"] + ["create_task_batch"],
            }

        def assign_and_notify(state: TaskOrchestrationState) -> TaskOrchestrationState:
            """Assign tasks to users and send notifications"""

            # Simulate task assignment
            assignments = []
            for task in state["created_tasks"]:
                assignment = {
                    "task_id": task["id"],
                    "assigned_to": state["user_id"],  # Simplified assignment
                    "notification_sent": True,
                    "assigned_at": datetime.utcnow().isoformat(),
                }
                assignments.append(assignment)

            return {
                **state,
                "assigned_users": [
                    assignment["assigned_to"] for assignment in assignments
                ],
                "current_step": "completed",
                "completed_steps": state["completed_steps"] + ["assign_and_notify"],
                "status": "completed",
            }

        # Build task orchestration workflow
        builder = StateGraph(TaskOrchestrationState)

        builder.add_node("analyze_task_requests", analyze_task_requests)
        builder.add_node("create_task_batch", create_task_batch)
        builder.add_node("assign_and_notify", assign_and_notify)

        builder.add_edge(START, "analyze_task_requests")
        builder.add_edge("analyze_task_requests", "create_task_batch")
        builder.add_edge("create_task_batch", "assign_and_notify")
        builder.add_edge("assign_and_notify", END)

        return builder.compile(checkpointer=self.checkpointer)

    def _create_research_analysis_workflow(self) -> Any:
        """Create research and analysis workflow with parallel section processing"""

        def plan_research(state: ResearchAnalysisState) -> ResearchAnalysisState:
            """Plan research sections and approach"""

            messages = [
                SystemMessage(
                    content="""You are a research planning specialist. Create a comprehensive research plan with:
                1. Key research sections to investigate
                2. Specific questions for each section
                3. Research methodology for each area
                4. Expected deliverables

                Return a structured plan as JSON."""
                ),
                HumanMessage(content=f"Research query: {state['research_query']}"),
            ]

            response = self.llm.invoke(messages)

            try:
                plan = json.loads(response.content)
                sections = plan.get("sections", [])
            except json.JSONDecodeError:
                # Fallback to basic sections
                sections = [
                    {
                        "name": "Background Research",
                        "description": "Gather background information",
                    },
                    {"name": "Data Analysis", "description": "Analyze relevant data"},
                    {
                        "name": "Insights Generation",
                        "description": "Generate key insights",
                    },
                ]

            return {
                **state,
                "research_sections": sections,
                "current_step": "conduct_research",
                "completed_steps": state["completed_steps"] + ["plan_research"],
            }

        def conduct_section_research(section_data: Dict[str, Any]) -> Dict[str, Any]:
            """Conduct research for a specific section"""

            messages = [
                SystemMessage(
                    content=f"""You are researching: {section_data['name']}
                Description: {section_data['description']}

                Provide comprehensive research findings with:
                1. Key findings
                2. Supporting data
                3. Implications
                4. Recommendations"""
                ),
                HumanMessage(content="Conduct thorough research on this section."),
            ]

            response = self.llm.invoke(messages)

            return {
                "section_name": section_data["name"],
                "content": response.content,
                "completed_at": datetime.utcnow().isoformat(),
            }

        def assign_research_workers(state: ResearchAnalysisState) -> List[Send]:
            """Assign research workers to each section"""

            return [
                Send("conduct_section_research", {"section": section})
                for section in state["research_sections"]
            ]

        def synthesize_research(state: ResearchAnalysisState) -> ResearchAnalysisState:
            """Synthesize all research sections into final report"""

            if not state["completed_sections"]:
                return {
                    **state,
                    "status": "failed",
                    "error_count": state["error_count"] + 1,
                }

            # Combine all research sections
            combined_research = "\n\n".join(
                [
                    f"## {section}\n{content}"
                    for section, content in zip(
                        [s["name"] for s in state["research_sections"]],
                        state["completed_sections"],
                    )
                ]
            )

            messages = [
                SystemMessage(
                    content="""You are a research synthesizer. Create a comprehensive final report that:
                1. Summarizes key findings from all sections
                2. Identifies patterns and connections
                3. Provides actionable insights
                4. Makes clear recommendations"""
                ),
                HumanMessage(
                    content=f"Research sections to synthesize:\n\n{combined_research}"
                ),
            ]

            response = self.llm.invoke(messages)

            return {
                **state,
                "final_report": response.content,
                "analysis_results": {
                    "sections_completed": len(state["completed_sections"]),
                    "total_sections": len(state["research_sections"]),
                    "synthesis_completed_at": datetime.utcnow().isoformat(),
                },
                "current_step": "completed",
                "completed_steps": state["completed_steps"] + ["synthesize_research"],
                "status": "completed",
            }

        # Build research workflow
        builder = StateGraph(ResearchAnalysisState)

        builder.add_node("plan_research", plan_research)
        builder.add_node("conduct_section_research", conduct_section_research)
        builder.add_node("synthesize_research", synthesize_research)

        builder.add_edge(START, "plan_research")
        builder.add_conditional_edges(
            "plan_research", assign_research_workers, ["conduct_section_research"]
        )
        builder.add_edge("conduct_section_research", "synthesize_research")
        builder.add_edge("synthesize_research", END)

        return builder.compile(checkpointer=self.checkpointer)

    def _create_collaborative_planning_workflow(self) -> Any:
        """Create collaborative planning workflow with multi-stakeholder input"""

        def initialize_planning(
            state: CollaborativePlanningState,
        ) -> CollaborativePlanningState:
            """Initialize collaborative planning process"""

            messages = [
                SystemMessage(
                    content="""You are a collaborative planning facilitator. Create an initial planning framework:
                1. Break down the objective into key areas
                2. Identify stakeholder roles and responsibilities
                3. Define planning phases and milestones
                4. Set collaboration guidelines"""
                ),
                HumanMessage(
                    content=f"Planning objective: {state['planning_objective']}\nStakeholders: {', '.join(state['stakeholders'])}"
                ),
            ]

            response = self.llm.invoke(messages)

            # Create plan sections
            plan_sections = [
                {"name": "Scope Definition", "owner": "all", "status": "pending"},
                {"name": "Resource Planning", "owner": "leads", "status": "pending"},
                {
                    "name": "Timeline Development",
                    "owner": "coordinators",
                    "status": "pending",
                },
                {
                    "name": "Risk Assessment",
                    "owner": "specialists",
                    "status": "pending",
                },
            ]

            return {
                **state,
                "plan_sections": plan_sections,
                "current_step": "gather_input",
                "completed_steps": state["completed_steps"] + ["initialize_planning"],
                "workflow_data": {"initial_framework": response.content},
            }

        def gather_stakeholder_input(
            state: CollaborativePlanningState,
        ) -> CollaborativePlanningState:
            """Simulate gathering input from stakeholders"""

            # In a real implementation, this would collect actual stakeholder input
            # For now, simulate with LLM-generated perspectives

            stakeholder_inputs = []
            for stakeholder in state["stakeholders"]:
                messages = [
                    SystemMessage(
                        content=f"""You are representing the perspective of: {stakeholder}
                    Provide input on the planning objective from your role's viewpoint.
                    Consider: priorities, constraints, resources, timeline, risks."""
                    ),
                    HumanMessage(
                        content=f"Planning objective: {state['planning_objective']}"
                    ),
                ]

                response = self.llm.invoke(messages)
                stakeholder_inputs.append(
                    {
                        "stakeholder": stakeholder,
                        "input": response.content,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            return {
                **state,
                "feedback_rounds": stakeholder_inputs,
                "current_step": "synthesize_plan",
                "completed_steps": state["completed_steps"]
                + ["gather_stakeholder_input"],
            }

        def synthesize_collaborative_plan(
            state: CollaborativePlanningState,
        ) -> CollaborativePlanningState:
            """Synthesize all stakeholder input into unified plan"""

            all_input = "\n\n".join(
                [
                    f"**{feedback['stakeholder']}:**\n{feedback['input']}"
                    for feedback in state["feedback_rounds"]
                ]
            )

            messages = [
                SystemMessage(
                    content="""You are a plan synthesizer. Create a unified collaborative plan that:
                1. Incorporates all stakeholder perspectives
                2. Balances competing priorities
                3. Identifies consensus areas and conflicts
                4. Provides clear next steps and responsibilities"""
                ),
                HumanMessage(
                    content=f"Objective: {state['planning_objective']}\n\nStakeholder Input:\n{all_input}"
                ),
            ]

            response = self.llm.invoke(messages)

            return {
                **state,
                "final_plan": response.content,
                "consensus_items": ["scope", "timeline", "resources"],  # Simplified
                "current_step": "completed",
                "completed_steps": state["completed_steps"]
                + ["synthesize_collaborative_plan"],
                "status": "completed",
            }

        # Build collaborative planning workflow
        builder = StateGraph(CollaborativePlanningState)

        builder.add_node("initialize_planning", initialize_planning)
        builder.add_node("gather_stakeholder_input", gather_stakeholder_input)
        builder.add_node("synthesize_collaborative_plan", synthesize_collaborative_plan)

        builder.add_edge(START, "initialize_planning")
        builder.add_edge("initialize_planning", "gather_stakeholder_input")
        builder.add_edge("gather_stakeholder_input", "synthesize_collaborative_plan")
        builder.add_edge("synthesize_collaborative_plan", END)

        return builder.compile(checkpointer=self.checkpointer)

    def _create_iterative_refinement_workflow(self) -> Any:
        """Create iterative refinement workflow with feedback loops"""

        def generate_initial_content(state: WorkflowState) -> WorkflowState:
            """Generate initial content based on requirements"""

            requirements = state["workflow_data"].get("requirements", "")
            content_type = state["workflow_data"].get("content_type", "general")

            messages = [
                SystemMessage(
                    content=f"""You are a content creator specializing in {content_type}.
                Create high-quality content that meets the specified requirements.
                Focus on clarity, completeness, and user value."""
                ),
                HumanMessage(content=f"Requirements: {requirements}"),
            ]

            response = self.llm.invoke(messages)

            return {
                **state,
                "workflow_data": {
                    **state["workflow_data"],
                    "current_content": response.content,
                    "iteration": 1,
                },
                "current_step": "evaluate_content",
                "completed_steps": state["completed_steps"]
                + ["generate_initial_content"],
            }

        def evaluate_content(state: WorkflowState) -> WorkflowState:
            """Evaluate content quality and provide feedback"""

            current_content = state["workflow_data"].get("current_content", "")
            requirements = state["workflow_data"].get("requirements", "")

            messages = [
                SystemMessage(
                    content="""You are a content evaluator. Assess the content against requirements:
                1. Rate quality (1-10)
                2. Identify strengths and weaknesses
                3. Provide specific improvement suggestions
                4. Determine if content meets standards (quality >= 8)

                Return evaluation as JSON with: {"quality_score": X, "meets_standards": true/false, "feedback": "..."}"""
                ),
                HumanMessage(
                    content=f"Requirements: {requirements}\n\nContent to evaluate:\n{current_content}"
                ),
            ]

            response = self.llm.invoke(messages)

            try:
                evaluation = json.loads(response.content)
            except json.JSONDecodeError:
                evaluation = {
                    "quality_score": 5,
                    "meets_standards": False,
                    "feedback": response.content,
                }

            return {
                **state,
                "workflow_data": {**state["workflow_data"], "evaluation": evaluation},
                "current_step": "check_quality",
                "completed_steps": state["completed_steps"] + ["evaluate_content"],
            }

        def check_quality_gate(state: WorkflowState) -> str:
            """Check if content meets quality standards"""

            evaluation = state["workflow_data"].get("evaluation", {})
            iteration = state["workflow_data"].get("iteration", 1)
            max_iterations = state.get("max_iterations", 3)

            meets_standards = evaluation.get("meets_standards", False)

            if meets_standards or iteration >= max_iterations:
                return "finalize_content"
            else:
                return "refine_content"

        def refine_content(state: WorkflowState) -> WorkflowState:
            """Refine content based on feedback"""

            current_content = state["workflow_data"].get("current_content", "")
            evaluation = state["workflow_data"].get("evaluation", {})
            feedback = evaluation.get("feedback", "")

            messages = [
                SystemMessage(
                    content="""You are a content refiner. Improve the content based on feedback:
                1. Address specific issues mentioned in feedback
                2. Enhance clarity and completeness
                3. Maintain the original intent and requirements
                4. Make targeted improvements rather than complete rewrites"""
                ),
                HumanMessage(
                    content=f"Current content:\n{current_content}\n\nFeedback:\n{feedback}"
                ),
            ]

            response = self.llm.invoke(messages)

            iteration = state["workflow_data"].get("iteration", 1) + 1

            return {
                **state,
                "workflow_data": {
                    **state["workflow_data"],
                    "current_content": response.content,
                    "iteration": iteration,
                    "refinement_history": state["workflow_data"].get(
                        "refinement_history", []
                    )
                    + [feedback],
                },
                "current_step": "evaluate_content",
                "completed_steps": state["completed_steps"] + ["refine_content"],
            }

        def finalize_content(state: WorkflowState) -> WorkflowState:
            """Finalize the refined content"""

            return {
                **state,
                "workflow_data": {
                    **state["workflow_data"],
                    "final_content": state["workflow_data"].get("current_content"),
                    "finalized_at": datetime.utcnow().isoformat(),
                },
                "current_step": "completed",
                "completed_steps": state["completed_steps"] + ["finalize_content"],
                "status": "completed",
            }

        # Build iterative refinement workflow
        builder = StateGraph(WorkflowState)

        builder.add_node("generate_initial_content", generate_initial_content)
        builder.add_node("evaluate_content", evaluate_content)
        builder.add_node("refine_content", refine_content)
        builder.add_node("finalize_content", finalize_content)

        builder.add_edge(START, "generate_initial_content")
        builder.add_edge("generate_initial_content", "evaluate_content")
        builder.add_conditional_edges(
            "evaluate_content",
            check_quality_gate,
            {
                "refine_content": "refine_content",
                "finalize_content": "finalize_content",
            },
        )
        builder.add_edge("refine_content", "evaluate_content")
        builder.add_edge("finalize_content", END)

        return builder.compile(checkpointer=self.checkpointer)

    def _create_multi_step_automation_workflow(self) -> Any:
        """Create multi-step automation workflow for complex processes"""

        def analyze_automation_request(state: WorkflowState) -> WorkflowState:
            """Analyze automation request and create execution plan"""

            request = state["workflow_data"].get("automation_request", "")

            messages = [
                SystemMessage(
                    content="""You are an automation planner. Analyze the request and create a step-by-step execution plan:
                1. Break down the request into discrete steps
                2. Identify required resources and permissions
                3. Determine step dependencies and order
                4. Estimate execution time and complexity

                Return plan as JSON with steps array."""
                ),
                HumanMessage(content=f"Automation request: {request}"),
            ]

            response = self.llm.invoke(messages)

            try:
                plan = json.loads(response.content)
                steps = plan.get("steps", [])
            except json.JSONDecodeError:
                # Fallback to basic steps
                steps = [
                    {
                        "name": "Validate Request",
                        "type": "validation",
                        "estimated_time": "1min",
                    },
                    {
                        "name": "Execute Action",
                        "type": "execution",
                        "estimated_time": "5min",
                    },
                    {
                        "name": "Verify Results",
                        "type": "verification",
                        "estimated_time": "2min",
                    },
                ]

            return {
                **state,
                "workflow_data": {
                    **state["workflow_data"],
                    "execution_plan": steps,
                    "current_step_index": 0,
                },
                "current_step": "execute_automation_step",
                "completed_steps": state["completed_steps"]
                + ["analyze_automation_request"],
            }

        def execute_automation_step(state: WorkflowState) -> WorkflowState:
            """Execute current automation step"""

            execution_plan = state["workflow_data"].get("execution_plan", [])
            step_index = state["workflow_data"].get("current_step_index", 0)

            if step_index >= len(execution_plan):
                return {
                    **state,
                    "current_step": "complete_automation",
                    "status": "completed",
                }

            current_step = execution_plan[step_index]
            step_name = current_step.get("name", f"Step {step_index + 1}")
            step_type = current_step.get("type", "general")

            messages = [
                SystemMessage(
                    content=f"""You are executing automation step: {step_name}
                Step type: {step_type}

                Execute this step and report:
                1. Actions taken
                2. Results achieved
                3. Any issues encountered
                4. Next step readiness"""
                ),
                HumanMessage(content=f"Execute step: {step_name}"),
            ]

            response = self.llm.invoke(messages)

            # Record step execution
            step_results = state["workflow_data"].get("step_results", [])
            step_results.append(
                {
                    "step_index": step_index,
                    "step_name": step_name,
                    "result": response.content,
                    "executed_at": datetime.utcnow().isoformat(),
                }
            )

            return {
                **state,
                "workflow_data": {
                    **state["workflow_data"],
                    "current_step_index": step_index + 1,
                    "step_results": step_results,
                },
                "current_step": "execute_automation_step",
                "completed_steps": state["completed_steps"]
                + [f"execute_step_{step_index}"],
            }

        def complete_automation(state: WorkflowState) -> WorkflowState:
            """Complete automation workflow and summarize results"""

            step_results = state["workflow_data"].get("step_results", [])
            execution_plan = state["workflow_data"].get("execution_plan", [])

            summary = f"Automation completed successfully!\n\n"
            summary += f"Total steps executed: {len(step_results)}\n"
            summary += f"Planned steps: {len(execution_plan)}\n\n"

            for result in step_results:
                summary += f"**{result['step_name']}:**\n{result['result']}\n\n"

            return {
                **state,
                "workflow_data": {
                    **state["workflow_data"],
                    "automation_summary": summary,
                    "completed_at": datetime.utcnow().isoformat(),
                },
                "current_step": "completed",
                "completed_steps": state["completed_steps"] + ["complete_automation"],
                "status": "completed",
            }

        def should_continue_automation(state: WorkflowState) -> str:
            """Determine if automation should continue"""

            execution_plan = state["workflow_data"].get("execution_plan", [])
            step_index = state["workflow_data"].get("current_step_index", 0)

            if step_index >= len(execution_plan):
                return "complete_automation"
            else:
                return "execute_automation_step"

        # Build multi-step automation workflow
        builder = StateGraph(WorkflowState)

        builder.add_node("analyze_automation_request", analyze_automation_request)
        builder.add_node("execute_automation_step", execute_automation_step)
        builder.add_node("complete_automation", complete_automation)

        builder.add_edge(START, "analyze_automation_request")
        builder.add_edge("analyze_automation_request", "execute_automation_step")
        builder.add_conditional_edges(
            "execute_automation_step",
            should_continue_automation,
            {
                "execute_automation_step": "execute_automation_step",
                "complete_automation": "complete_automation",
            },
        )
        builder.add_edge("complete_automation", END)

        return builder.compile(checkpointer=self.checkpointer)

    async def _prepare_initial_state(
        self,
        workflow_type: WorkflowType,
        workflow_id: str,
        user_id: UUID,
        initial_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare initial state for workflow"""

        base_state = {
            "workflow_id": workflow_id,
            "user_id": str(user_id),
            "messages": [],
            "current_step": "starting",
            "completed_steps": [],
            "workflow_data": initial_data,
            "error_count": 0,
            "max_iterations": initial_data.get("max_iterations", 10),
            "status": "running",
        }

        # Add workflow-specific state
        if workflow_type == WorkflowType.TASK_ORCHESTRATION:
            base_state.update(
                {
                    "task_requests": initial_data.get("task_requests", []),
                    "created_tasks": [],
                    "assigned_users": [],
                    "dependencies": {},
                    "priority_analysis": None,
                }
            )

        elif workflow_type == WorkflowType.RESEARCH_AND_ANALYSIS:
            base_state.update(
                {
                    "research_query": initial_data.get("research_query", ""),
                    "research_sections": [],
                    "completed_sections": [],
                    "analysis_results": {},
                    "final_report": None,
                }
            )

        elif workflow_type == WorkflowType.COLLABORATIVE_PLANNING:
            base_state.update(
                {
                    "planning_objective": initial_data.get("planning_objective", ""),
                    "stakeholders": initial_data.get("stakeholders", []),
                    "plan_sections": [],
                    "feedback_rounds": [],
                    "consensus_items": [],
                    "final_plan": None,
                }
            )

        return base_state

    async def list_active_workflows(self, user_id: UUID) -> List[Dict[str, Any]]:
        """List active workflows for a user"""

        # This would typically query a database of active workflows
        # For now, return a placeholder implementation
        return [
            {
                "workflow_id": "example_1",
                "workflow_type": "task_orchestration",
                "status": "running",
                "created_at": datetime.utcnow().isoformat(),
                "current_step": "create_tasks",
            }
        ]

    async def cancel_workflow(
        self, workflow_id: str, thread_id: str, workflow_type: WorkflowType
    ) -> Dict[str, Any]:
        """Cancel an active workflow"""

        try:
            # Update workflow state to cancelled
            # This would typically update the database and cleanup resources

            return {
                "workflow_id": workflow_id,
                "thread_id": thread_id,
                "workflow_type": workflow_type.value,
                "status": "cancelled",
                "cancelled_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            raise AIServiceError(f"Failed to cancel workflow: {str(e)}")

    def get_workflow_types(self) -> List[Dict[str, Any]]:
        """Get available workflow types and their descriptions"""

        return [
            {
                "type": WorkflowType.TASK_ORCHESTRATION.value,
                "name": "Task Orchestration",
                "description": "Intelligent task creation, assignment, and dependency management",
                "capabilities": [
                    "parallel_task_creation",
                    "dependency_analysis",
                    "smart_assignment",
                ],
            },
            {
                "type": WorkflowType.RESEARCH_AND_ANALYSIS.value,
                "name": "Research & Analysis",
                "description": "Comprehensive research with parallel section processing and synthesis",
                "capabilities": [
                    "parallel_research",
                    "section_synthesis",
                    "insight_generation",
                ],
            },
            {
                "type": WorkflowType.COLLABORATIVE_PLANNING.value,
                "name": "Collaborative Planning",
                "description": "Multi-stakeholder planning with consensus building",
                "capabilities": [
                    "stakeholder_input",
                    "consensus_building",
                    "conflict_resolution",
                ],
            },
            {
                "type": WorkflowType.ITERATIVE_REFINEMENT.value,
                "name": "Iterative Refinement",
                "description": "Content improvement through feedback loops and quality gates",
                "capabilities": [
                    "quality_evaluation",
                    "iterative_improvement",
                    "feedback_loops",
                ],
            },
            {
                "type": WorkflowType.MULTI_STEP_AUTOMATION.value,
                "name": "Multi-Step Automation",
                "description": "Complex automation workflows with step-by-step execution",
                "capabilities": [
                    "step_planning",
                    "sequential_execution",
                    "result_verification",
                ],
            },
        ]
