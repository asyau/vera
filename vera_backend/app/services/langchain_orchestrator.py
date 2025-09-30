"""
LangChain-based AI Orchestrator Service
Implements an intelligent orchestrator agent that understands user intent
and delegates tasks to specialized agents
"""
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.callbacks import get_openai_callback
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import Tool, tool
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AIServiceError, ValidationError
from app.models.sql_models import Company, Task, User
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


class IntentType(Enum):
    """Types of user intents the orchestrator can handle"""

    TASK_MANAGEMENT = "task_management"
    CONVERSATION = "conversation"
    INFORMATION_RETRIEVAL = "information_retrieval"
    ANALYSIS = "analysis"
    WORKFLOW_AUTOMATION = "workflow_automation"
    TEAM_COORDINATION = "team_coordination"
    REPORTING = "reporting"


class SpecializedAgentType(Enum):
    """Types of specialized agents available"""

    TASK_AGENT = "task_agent"
    CONVERSATION_AGENT = "conversation_agent"
    ANALYSIS_AGENT = "analysis_agent"
    COORDINATION_AGENT = "coordination_agent"
    REPORTING_AGENT = "reporting_agent"


class LangChainOrchestrator(BaseService):
    """
    LangChain-based orchestrator that acts as the main AI agent coordinator.
    It analyzes user intent and delegates tasks to specialized agents.
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.7,
            api_key=settings.openai_api_key,
        )

        # Initialize repositories
        self.task_repo = TaskRepository(db)
        self.user_repo = UserRepository(db)

        # Initialize memory for conversation context
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10,  # Keep last 10 exchanges
        )

        # Initialize specialized agents
        self.specialized_agents = self._initialize_specialized_agents()

        # Create the main orchestrator agent
        self.orchestrator_agent = self._create_orchestrator_agent()

    async def process_user_request(
        self, user_input: str, user_id: UUID, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing user requests.
        Analyzes intent and delegates to appropriate specialized agents.
        """
        try:
            # Get user context
            user_context = await self._get_user_context(user_id)

            # Analyze user intent
            intent_analysis = await self._analyze_user_intent(user_input, user_context)

            # Route to appropriate specialized agent
            response = await self._route_to_specialized_agent(
                intent_analysis, user_input, user_id, context
            )

            # Store interaction in memory
            self.memory.chat_memory.add_user_message(user_input)
            self.memory.chat_memory.add_ai_message(response.get("content", ""))

            return {
                "content": response.get("content", ""),
                "intent": intent_analysis,
                "agent_used": response.get("agent_used", ""),
                "metadata": response.get("metadata", {}),
                "cost_info": response.get("cost_info", {}),
            }

        except Exception as e:
            raise AIServiceError(f"Failed to process user request: {str(e)}")

    async def _analyze_user_intent(
        self, user_input: str, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze user intent using the orchestrator LLM"""

        intent_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an AI intent analyzer. Analyze the user's input and determine:
            1. Primary intent type (task_management, conversation, information_retrieval, analysis, workflow_automation, team_coordination, reporting)
            2. Confidence level (0.0-1.0)
            3. Key entities mentioned (people, dates, tasks, projects)
            4. Required actions
            5. Context dependencies

            User Context:
            - Name: {user_name}
            - Role: {user_role}
            - Team: {user_team}
            - Company: {company_name}

            Return your analysis as a JSON object with the following structure:
            {{
                "primary_intent": "intent_type",
                "confidence": 0.0-1.0,
                "entities": {{
                    "people": [],
                    "dates": [],
                    "tasks": [],
                    "projects": []
                }},
                "required_actions": [],
                "context_dependencies": [],
                "complexity": "low|medium|high",
                "estimated_steps": 1-10
            }}""",
                ),
                ("human", "{user_input}"),
            ]
        )

        try:
            with get_openai_callback() as cb:
                response = await self.llm.ainvoke(
                    intent_prompt.format_messages(
                        user_input=user_input,
                        user_name=user_context.get("name", "User"),
                        user_role=user_context.get("role", "Unknown"),
                        user_team=user_context.get("team", "Unknown"),
                        company_name=user_context.get("company_name", "Unknown"),
                    )
                )

            # Parse the JSON response
            intent_data = json.loads(response.content.strip())
            intent_data["cost_info"] = {
                "total_tokens": cb.total_tokens,
                "total_cost": cb.total_cost,
            }

            return intent_data

        except json.JSONDecodeError:
            # Fallback to basic intent classification
            return {
                "primary_intent": "conversation",
                "confidence": 0.5,
                "entities": {"people": [], "dates": [], "tasks": [], "projects": []},
                "required_actions": ["respond"],
                "context_dependencies": [],
                "complexity": "low",
                "estimated_steps": 1,
            }

    async def _route_to_specialized_agent(
        self,
        intent_analysis: Dict[str, Any],
        user_input: str,
        user_id: UUID,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Route the request to the appropriate specialized agent"""

        primary_intent = intent_analysis.get("primary_intent", "conversation")

        # Route based on intent
        if primary_intent == "task_management":
            return await self._handle_task_management(
                user_input, user_id, intent_analysis, context
            )
        elif primary_intent == "team_coordination":
            return await self._handle_team_coordination(
                user_input, user_id, intent_analysis, context
            )
        elif primary_intent == "analysis":
            return await self._handle_analysis(
                user_input, user_id, intent_analysis, context
            )
        elif primary_intent == "reporting":
            return await self._handle_reporting(
                user_input, user_id, intent_analysis, context
            )
        elif primary_intent == "workflow_automation":
            return await self._handle_workflow_automation(
                user_input, user_id, intent_analysis, context
            )
        else:
            # Default to conversation agent
            return await self._handle_conversation(
                user_input, user_id, intent_analysis, context
            )

    async def _handle_task_management(
        self,
        user_input: str,
        user_id: UUID,
        intent_analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle task management requests using the task agent"""

        task_agent = self.specialized_agents[SpecializedAgentType.TASK_AGENT]

        # Get user's tasks for context
        user_tasks = self.task_repo.get_by_assignee_id(user_id)
        task_context = [
            {
                "id": str(task.id),
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            }
            for task in user_tasks[:10]  # Limit to recent tasks
        ]

        try:
            with get_openai_callback() as cb:
                response = await task_agent.ainvoke(
                    {
                        "input": user_input,
                        "user_id": str(user_id),
                        "current_tasks": json.dumps(task_context),
                        "intent_analysis": json.dumps(intent_analysis),
                        "chat_history": self.memory.chat_memory.messages,
                    }
                )

            return {
                "content": response.get("output", ""),
                "agent_used": "task_agent",
                "metadata": {
                    "tasks_processed": len(task_context),
                    "intent_confidence": intent_analysis.get("confidence", 0.0),
                },
                "cost_info": {
                    "total_tokens": cb.total_tokens,
                    "total_cost": cb.total_cost,
                },
            }

        except Exception as e:
            return {
                "content": f"I encountered an error while processing your task request: {str(e)}",
                "agent_used": "error_fallback",
                "metadata": {"error": str(e)},
            }

    async def _handle_conversation(
        self,
        user_input: str,
        user_id: UUID,
        intent_analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle general conversation requests"""

        conversation_agent = self.specialized_agents[
            SpecializedAgentType.CONVERSATION_AGENT
        ]
        user_context = await self._get_user_context(user_id)

        try:
            with get_openai_callback() as cb:
                response = await conversation_agent.ainvoke(
                    {
                        "input": user_input,
                        "user_context": json.dumps(user_context),
                        "intent_analysis": json.dumps(intent_analysis),
                        "chat_history": self.memory.chat_memory.messages,
                    }
                )

            return {
                "content": response.get("output", ""),
                "agent_used": "conversation_agent",
                "metadata": {
                    "intent_confidence": intent_analysis.get("confidence", 0.0)
                },
                "cost_info": {
                    "total_tokens": cb.total_tokens,
                    "total_cost": cb.total_cost,
                },
            }

        except Exception as e:
            return {
                "content": f"I'm having trouble understanding your request. Could you please rephrase it?",
                "agent_used": "error_fallback",
                "metadata": {"error": str(e)},
            }

    async def _handle_team_coordination(
        self,
        user_input: str,
        user_id: UUID,
        intent_analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle team coordination and collaboration requests"""

        coordination_agent = self.specialized_agents[
            SpecializedAgentType.COORDINATION_AGENT
        ]

        # Get team context
        user = self.user_repo.get_or_raise(user_id)
        team_members = self.user_repo.get_by_team(user.team_id) if user.team_id else []

        team_context = [
            {
                "id": str(member.id),
                "name": member.name,
                "role": member.role,
                "email": member.email,
            }
            for member in team_members[:20]  # Limit team size
        ]

        try:
            with get_openai_callback() as cb:
                response = await coordination_agent.ainvoke(
                    {
                        "input": user_input,
                        "user_id": str(user_id),
                        "team_context": json.dumps(team_context),
                        "intent_analysis": json.dumps(intent_analysis),
                        "chat_history": self.memory.chat_memory.messages,
                    }
                )

            return {
                "content": response.get("output", ""),
                "agent_used": "coordination_agent",
                "metadata": {
                    "team_size": len(team_context),
                    "intent_confidence": intent_analysis.get("confidence", 0.0),
                },
                "cost_info": {
                    "total_tokens": cb.total_tokens,
                    "total_cost": cb.total_cost,
                },
            }

        except Exception as e:
            return {
                "content": f"I encountered an error while processing your team coordination request: {str(e)}",
                "agent_used": "error_fallback",
                "metadata": {"error": str(e)},
            }

    async def _handle_analysis(
        self,
        user_input: str,
        user_id: UUID,
        intent_analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle data analysis and insights requests"""

        analysis_agent = self.specialized_agents[SpecializedAgentType.ANALYSIS_AGENT]

        # Get relevant data for analysis
        user_tasks = self.task_repo.get_by_assignee_id(user_id)
        analysis_context = {
            "task_count": len(user_tasks),
            "completed_tasks": len([t for t in user_tasks if t.status == "completed"]),
            "pending_tasks": len(
                [t for t in user_tasks if t.status in ["todo", "in_progress"]]
            ),
            "overdue_tasks": len(
                [
                    t
                    for t in user_tasks
                    if t.due_date
                    and t.due_date < datetime.now()
                    and t.status != "completed"
                ]
            ),
        }

        try:
            with get_openai_callback() as cb:
                response = await analysis_agent.ainvoke(
                    {
                        "input": user_input,
                        "user_id": str(user_id),
                        "analysis_context": json.dumps(analysis_context),
                        "intent_analysis": json.dumps(intent_analysis),
                        "chat_history": self.memory.chat_memory.messages,
                    }
                )

            return {
                "content": response.get("output", ""),
                "agent_used": "analysis_agent",
                "metadata": {
                    "data_points_analyzed": sum(analysis_context.values()),
                    "intent_confidence": intent_analysis.get("confidence", 0.0),
                },
                "cost_info": {
                    "total_tokens": cb.total_tokens,
                    "total_cost": cb.total_cost,
                },
            }

        except Exception as e:
            return {
                "content": f"I encountered an error while performing the analysis: {str(e)}",
                "agent_used": "error_fallback",
                "metadata": {"error": str(e)},
            }

    async def _handle_reporting(
        self,
        user_input: str,
        user_id: UUID,
        intent_analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle reporting and summary generation requests"""

        reporting_agent = self.specialized_agents[SpecializedAgentType.REPORTING_AGENT]

        # Get reporting data
        user_tasks = self.task_repo.get_by_assignee_id(user_id)
        reporting_context = {
            "total_tasks": len(user_tasks),
            "task_breakdown": {
                "completed": len([t for t in user_tasks if t.status == "completed"]),
                "in_progress": len(
                    [t for t in user_tasks if t.status == "in_progress"]
                ),
                "todo": len([t for t in user_tasks if t.status == "todo"]),
                "cancelled": len([t for t in user_tasks if t.status == "cancelled"]),
            },
            "priority_breakdown": {
                "high": len([t for t in user_tasks if t.priority == "high"]),
                "medium": len([t for t in user_tasks if t.priority == "medium"]),
                "low": len([t for t in user_tasks if t.priority == "low"]),
            },
        }

        try:
            with get_openai_callback() as cb:
                response = await reporting_agent.ainvoke(
                    {
                        "input": user_input,
                        "user_id": str(user_id),
                        "reporting_context": json.dumps(reporting_context),
                        "intent_analysis": json.dumps(intent_analysis),
                        "chat_history": self.memory.chat_memory.messages,
                    }
                )

            return {
                "content": response.get("output", ""),
                "agent_used": "reporting_agent",
                "metadata": {
                    "report_data_points": reporting_context["total_tasks"],
                    "intent_confidence": intent_analysis.get("confidence", 0.0),
                },
                "cost_info": {
                    "total_tokens": cb.total_tokens,
                    "total_cost": cb.total_cost,
                },
            }

        except Exception as e:
            return {
                "content": f"I encountered an error while generating the report: {str(e)}",
                "agent_used": "error_fallback",
                "metadata": {"error": str(e)},
            }

    async def _handle_workflow_automation(
        self,
        user_input: str,
        user_id: UUID,
        intent_analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle workflow automation requests"""

        # For now, delegate to conversation agent with automation context
        conversation_agent = self.specialized_agents[
            SpecializedAgentType.CONVERSATION_AGENT
        ]

        automation_context = {
            "automation_request": True,
            "available_workflows": [
                "task_creation",
                "status_updates",
                "notifications",
                "reporting",
            ],
            "user_permissions": "standard",  # Could be enhanced with actual permission checking
        }

        try:
            with get_openai_callback() as cb:
                response = await conversation_agent.ainvoke(
                    {
                        "input": f"AUTOMATION REQUEST: {user_input}",
                        "user_id": str(user_id),
                        "automation_context": json.dumps(automation_context),
                        "intent_analysis": json.dumps(intent_analysis),
                        "chat_history": self.memory.chat_memory.messages,
                    }
                )

            return {
                "content": response.get("output", ""),
                "agent_used": "workflow_automation",
                "metadata": {
                    "automation_type": "workflow",
                    "intent_confidence": intent_analysis.get("confidence", 0.0),
                },
                "cost_info": {
                    "total_tokens": cb.total_tokens,
                    "total_cost": cb.total_cost,
                },
            }

        except Exception as e:
            return {
                "content": f"I encountered an error while processing your automation request: {str(e)}",
                "agent_used": "error_fallback",
                "metadata": {"error": str(e)},
            }

    def _initialize_specialized_agents(
        self,
    ) -> Dict[SpecializedAgentType, AgentExecutor]:
        """Initialize all specialized agents"""
        agents = {}

        # Task Management Agent
        agents[SpecializedAgentType.TASK_AGENT] = self._create_task_agent()

        # Conversation Agent
        agents[
            SpecializedAgentType.CONVERSATION_AGENT
        ] = self._create_conversation_agent()

        # Analysis Agent
        agents[SpecializedAgentType.ANALYSIS_AGENT] = self._create_analysis_agent()

        # Coordination Agent
        agents[
            SpecializedAgentType.COORDINATION_AGENT
        ] = self._create_coordination_agent()

        # Reporting Agent
        agents[SpecializedAgentType.REPORTING_AGENT] = self._create_reporting_agent()

        return agents

    def _create_task_agent(self) -> AgentExecutor:
        """Create a specialized agent for task management"""

        @tool
        def create_task(
            title: str,
            description: str,
            priority: str = "medium",
            due_date: Optional[str] = None,
        ) -> str:
            """Create a new task with the given details."""
            try:
                # This would integrate with your task creation logic
                return f"Task '{title}' created successfully with priority {priority}"
            except Exception as e:
                return f"Error creating task: {str(e)}"

        @tool
        def update_task_status(task_id: str, status: str) -> str:
            """Update the status of an existing task."""
            try:
                # This would integrate with your task update logic
                return f"Task {task_id} status updated to {status}"
            except Exception as e:
                return f"Error updating task: {str(e)}"

        @tool
        def list_tasks(status_filter: Optional[str] = None) -> str:
            """List tasks, optionally filtered by status."""
            try:
                # This would integrate with your task listing logic
                return "Here are your current tasks..."
            except Exception as e:
                return f"Error listing tasks: {str(e)}"

        tools = [create_task, update_task_status, list_tasks]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a specialized task management agent. Your role is to help users:
            - Create, update, and manage tasks
            - Analyze task priorities and deadlines
            - Provide task-related insights and recommendations
            - Extract actionable items from conversations

            Always be proactive in suggesting task organization improvements.
            Use the available tools to perform task operations when needed.

            Current user context: {user_id}
            Current tasks: {current_tasks}
            Intent analysis: {intent_analysis}
            """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False)

    def _create_conversation_agent(self) -> AgentExecutor:
        """Create a specialized agent for general conversation"""

        @tool
        def get_user_preferences(user_id: str) -> str:
            """Get user preferences and personalization settings."""
            try:
                # This would fetch user preferences from the database
                return "User prefers concise responses and professional tone"
            except Exception as e:
                return f"Error getting preferences: {str(e)}"

        tools = [get_user_preferences]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are Vira, a helpful AI assistant specializing in conversational interactions.
            Your role is to:
            - Engage in natural, helpful conversations
            - Provide information and answer questions
            - Maintain context and personality
            - Adapt your communication style to the user

            Be warm, professional, and contextually aware.
            Use the user context to personalize your responses.

            User context: {user_context}
            Intent analysis: {intent_analysis}
            """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False)

    def _create_analysis_agent(self) -> AgentExecutor:
        """Create a specialized agent for data analysis"""

        @tool
        def analyze_task_patterns(user_id: str) -> str:
            """Analyze task completion patterns and productivity metrics."""
            try:
                # This would perform actual analysis
                return "Analysis shows improved task completion rate this week"
            except Exception as e:
                return f"Error analyzing patterns: {str(e)}"

        @tool
        def generate_insights(data_context: str) -> str:
            """Generate insights from the provided data context."""
            try:
                # This would generate insights based on data
                return "Key insight: Peak productivity occurs in morning hours"
            except Exception as e:
                return f"Error generating insights: {str(e)}"

        tools = [analyze_task_patterns, generate_insights]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a specialized data analysis agent. Your role is to:
            - Analyze user data and identify patterns
            - Generate actionable insights
            - Create visualizations and summaries
            - Provide data-driven recommendations

            Focus on providing clear, actionable insights that help users improve their productivity.

            Analysis context: {analysis_context}
            Intent analysis: {intent_analysis}
            """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False)

    def _create_coordination_agent(self) -> AgentExecutor:
        """Create a specialized agent for team coordination"""

        @tool
        def schedule_meeting(
            participants: str, topic: str, duration: str = "30 minutes"
        ) -> str:
            """Schedule a meeting with team members."""
            try:
                # This would integrate with calendar/scheduling system
                return f"Meeting scheduled for {topic} with {participants}"
            except Exception as e:
                return f"Error scheduling meeting: {str(e)}"

        @tool
        def send_team_notification(message: str, recipients: str = "team") -> str:
            """Send a notification to team members."""
            try:
                # This would integrate with notification system
                return f"Notification sent to {recipients}: {message}"
            except Exception as e:
                return f"Error sending notification: {str(e)}"

        tools = [schedule_meeting, send_team_notification]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a specialized team coordination agent. Your role is to:
            - Facilitate team communication and collaboration
            - Schedule meetings and coordinate activities
            - Manage team workflows and dependencies
            - Provide team-related insights and recommendations

            Focus on improving team efficiency and communication.

            Team context: {team_context}
            Intent analysis: {intent_analysis}
            """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False)

    def _create_reporting_agent(self) -> AgentExecutor:
        """Create a specialized agent for reporting and summaries"""

        @tool
        def generate_status_report(time_period: str = "week") -> str:
            """Generate a status report for the specified time period."""
            try:
                # This would generate actual reports
                return (
                    f"Status report for the past {time_period} generated successfully"
                )
            except Exception as e:
                return f"Error generating report: {str(e)}"

        @tool
        def create_summary(content_type: str, details: str) -> str:
            """Create a summary of the specified content."""
            try:
                # This would create summaries
                return f"Summary of {content_type} created successfully"
            except Exception as e:
                return f"Error creating summary: {str(e)}"

        tools = [generate_status_report, create_summary]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a specialized reporting agent. Your role is to:
            - Generate comprehensive reports and summaries
            - Create visualizations and dashboards
            - Provide executive-level insights
            - Format information for different audiences

            Focus on creating clear, actionable reports that provide value to decision-makers.

            Reporting context: {reporting_context}
            Intent analysis: {intent_analysis}
            """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False)

    def _create_orchestrator_agent(self) -> AgentExecutor:
        """Create the main orchestrator agent"""

        @tool
        def delegate_to_specialist(agent_type: str, request: str) -> str:
            """Delegate a request to a specialized agent."""
            try:
                return f"Request delegated to {agent_type} specialist: {request}"
            except Exception as e:
                return f"Error delegating request: {str(e)}"

        tools = [delegate_to_specialist]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are the main orchestrator agent for Vira AI Assistant.
            Your role is to analyze user requests, understand their intent, and coordinate with specialized agents.

            You have access to the following specialized agents:
            - Task Agent: For task management, creation, and organization
            - Conversation Agent: For general chat and information
            - Analysis Agent: For data analysis and insights
            - Coordination Agent: For team collaboration and scheduling
            - Reporting Agent: For reports and summaries

            Analyze each request carefully and route it to the most appropriate specialist.
            Always maintain context and ensure smooth handoffs between agents.
            """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False)

    async def _get_user_context(self, user_id: UUID) -> Dict[str, Any]:
        """Get comprehensive user context for personalization"""
        try:
            user = self.user_repo.get_or_raise(user_id)
            company = (
                self.db.query(Company).filter(Company.id == user.company_id).first()
            )

            return {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "team": user.team_id,
                "company_name": company.name if company else "Unknown",
                "preferences": user.preferences or {},
            }
        except Exception as e:
            return {
                "id": str(user_id),
                "name": "User",
                "role": "Unknown",
                "company_name": "Unknown",
            }

    async def get_conversation_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history"""
        messages = self.memory.chat_memory.messages[
            -limit * 2 :
        ]  # Get last N exchanges

        history = []
        for message in messages:
            if isinstance(message, HumanMessage):
                history.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                history.append({"role": "assistant", "content": message.content})

        return history

    async def clear_conversation_history(self):
        """Clear the conversation history"""
        self.memory.clear()

    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics about agent usage and performance"""
        return {
            "specialized_agents_count": len(self.specialized_agents),
            "available_agents": [
                agent_type.value for agent_type in SpecializedAgentType
            ],
            "memory_size": len(self.memory.chat_memory.messages),
            "supported_intents": [intent.value for intent in IntentType],
        }
