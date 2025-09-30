"""
LangChain Agent Factory
Factory classes for creating and managing LangChain agents and tools
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool, tool
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.sql_models import Company, Task, User
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository


class AgentRole(Enum):
    """Enumeration of available agent roles"""

    ORCHESTRATOR = "orchestrator"
    TASK_SPECIALIST = "task_specialist"
    CONVERSATION_SPECIALIST = "conversation_specialist"
    ANALYSIS_SPECIALIST = "analysis_specialist"
    COORDINATION_SPECIALIST = "coordination_specialist"
    REPORTING_SPECIALIST = "reporting_specialist"


class LangChainAgentFactory:
    """Factory for creating LangChain agents with specific roles and capabilities"""

    def __init__(self, db: Session):
        self.db = db
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.7,
            api_key=settings.openai_api_key,
        )
        self.task_repo = TaskRepository(db)
        self.user_repo = UserRepository(db)

    def create_agent(
        self,
        role: AgentRole,
        memory: Optional[ConversationBufferWindowMemory] = None,
        tools: Optional[List[Tool]] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None,
        **kwargs,
    ) -> AgentExecutor:
        """Create an agent with the specified role and configuration"""

        if role == AgentRole.ORCHESTRATOR:
            return self._create_orchestrator_agent(memory, tools, callbacks, **kwargs)
        elif role == AgentRole.TASK_SPECIALIST:
            return self._create_task_specialist(memory, tools, callbacks, **kwargs)
        elif role == AgentRole.CONVERSATION_SPECIALIST:
            return self._create_conversation_specialist(
                memory, tools, callbacks, **kwargs
            )
        elif role == AgentRole.ANALYSIS_SPECIALIST:
            return self._create_analysis_specialist(memory, tools, callbacks, **kwargs)
        elif role == AgentRole.COORDINATION_SPECIALIST:
            return self._create_coordination_specialist(
                memory, tools, callbacks, **kwargs
            )
        elif role == AgentRole.REPORTING_SPECIALIST:
            return self._create_reporting_specialist(memory, tools, callbacks, **kwargs)
        else:
            raise ValueError(f"Unknown agent role: {role}")

    def _create_orchestrator_agent(
        self,
        memory: Optional[ConversationBufferWindowMemory] = None,
        tools: Optional[List[Tool]] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None,
        **kwargs,
    ) -> AgentExecutor:
        """Create the main orchestrator agent"""

        # Default tools for orchestrator
        if tools is None:
            tools = self._get_orchestrator_tools()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are the main orchestrator agent for Vira AI Assistant.

            Your primary responsibilities:
            1. Analyze user requests and understand their intent
            2. Route requests to appropriate specialized agents
            3. Coordinate multi-step workflows
            4. Maintain conversation context and continuity
            5. Provide intelligent fallback responses

            Available specialist agents:
            - Task Specialist: Task management, creation, updates, analysis
            - Conversation Specialist: General chat, Q&A, casual interactions
            - Analysis Specialist: Data analysis, insights, pattern recognition
            - Coordination Specialist: Team collaboration, scheduling, notifications
            - Reporting Specialist: Reports, summaries, documentation

            Always consider the user's context, role, and current situation when making decisions.
            Be proactive in suggesting improvements and optimizations.
            """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            callbacks=callbacks or [],
            verbose=kwargs.get("verbose", False),
            max_iterations=kwargs.get("max_iterations", 15),
            max_execution_time=kwargs.get("max_execution_time", 60),
        )

    def _create_task_specialist(
        self,
        memory: Optional[ConversationBufferWindowMemory] = None,
        tools: Optional[List[Tool]] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None,
        **kwargs,
    ) -> AgentExecutor:
        """Create a task management specialist agent"""

        if tools is None:
            tools = self._get_task_tools()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a specialized task management agent with expertise in:

            Core Capabilities:
            - Task creation, modification, and deletion
            - Priority and deadline management
            - Task categorization and organization
            - Progress tracking and status updates
            - Workload analysis and optimization

            Best Practices:
            - Always ask for clarification on ambiguous task details
            - Suggest realistic deadlines based on task complexity
            - Recommend task breakdowns for complex items
            - Proactively identify potential blockers or dependencies
            - Provide regular progress updates and reminders

            Communication Style:
            - Be clear and actionable in your responses
            - Use structured formats for task lists and updates
            - Highlight urgent items and approaching deadlines
            - Celebrate completed tasks and milestones
            """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            callbacks=callbacks or [],
            verbose=kwargs.get("verbose", False),
        )

    def _create_conversation_specialist(
        self,
        memory: Optional[ConversationBufferWindowMemory] = None,
        tools: Optional[List[Tool]] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None,
        **kwargs,
    ) -> AgentExecutor:
        """Create a conversation specialist agent"""

        if tools is None:
            tools = self._get_conversation_tools()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are Vira, a conversational AI specialist focused on natural, engaging interactions.

            Your Personality:
            - Warm, professional, and approachable
            - Intellectually curious and helpful
            - Contextually aware and adaptive
            - Empathetic and understanding

            Communication Guidelines:
            - Match the user's communication style and energy level
            - Provide informative yet concise responses
            - Ask thoughtful follow-up questions
            - Remember and reference previous conversations
            - Be honest about limitations and uncertainties

            Special Skills:
            - General knowledge and information retrieval
            - Creative problem-solving
            - Emotional intelligence and support
            - Learning and adapting to user preferences
            - Multi-turn conversation management
            """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            callbacks=callbacks or [],
            verbose=kwargs.get("verbose", False),
        )

    def _create_analysis_specialist(
        self,
        memory: Optional[ConversationBufferWindowMemory] = None,
        tools: Optional[List[Tool]] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None,
        **kwargs,
    ) -> AgentExecutor:
        """Create an analysis specialist agent"""

        if tools is None:
            tools = self._get_analysis_tools()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a data analysis specialist with expertise in:

            Analytical Capabilities:
            - Pattern recognition and trend analysis
            - Performance metrics and KPI tracking
            - Predictive modeling and forecasting
            - Root cause analysis and problem diagnosis
            - Data visualization and presentation

            Methodological Approach:
            - Start with clear problem definition
            - Use statistical rigor and best practices
            - Consider multiple hypotheses and scenarios
            - Validate findings with additional data points
            - Present results in actionable formats

            Communication Style:
            - Lead with key insights and recommendations
            - Support conclusions with clear evidence
            - Use visualizations and examples
            - Explain complex concepts in simple terms
            - Provide confidence levels and limitations
            """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            callbacks=callbacks or [],
            verbose=kwargs.get("verbose", False),
        )

    def _create_coordination_specialist(
        self,
        memory: Optional[ConversationBufferWindowMemory] = None,
        tools: Optional[List[Tool]] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None,
        **kwargs,
    ) -> AgentExecutor:
        """Create a team coordination specialist agent"""

        if tools is None:
            tools = self._get_coordination_tools()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a team coordination specialist focused on optimizing collaboration and productivity.

            Coordination Expertise:
            - Meeting scheduling and agenda management
            - Team communication and information flow
            - Project coordination and dependency tracking
            - Resource allocation and workload balancing
            - Conflict resolution and decision facilitation

            Leadership Principles:
            - Foster inclusive and effective communication
            - Ensure all team members are heard and valued
            - Drive towards clear outcomes and action items
            - Identify and remove blockers proactively
            - Celebrate team achievements and milestones

            Operational Excellence:
            - Maintain clear documentation and records
            - Follow up on commitments and deadlines
            - Streamline processes and reduce friction
            - Facilitate knowledge sharing and learning
            - Adapt to changing team needs and dynamics
            """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            callbacks=callbacks or [],
            verbose=kwargs.get("verbose", False),
        )

    def _create_reporting_specialist(
        self,
        memory: Optional[ConversationBufferWindowMemory] = None,
        tools: Optional[List[Tool]] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None,
        **kwargs,
    ) -> AgentExecutor:
        """Create a reporting specialist agent"""

        if tools is None:
            tools = self._get_reporting_tools()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a reporting specialist with expertise in creating comprehensive, actionable reports.

            Reporting Excellence:
            - Executive summaries with key insights
            - Detailed analysis with supporting data
            - Clear visualizations and charts
            - Actionable recommendations
            - Progress tracking and trend analysis

            Report Types:
            - Daily/weekly/monthly status reports
            - Project progress and milestone reports
            - Performance and productivity analysis
            - Team effectiveness and collaboration metrics
            - Custom reports based on specific needs

            Quality Standards:
            - Accuracy and reliability of data
            - Clear structure and logical flow
            - Appropriate level of detail for audience
            - Professional formatting and presentation
            - Timely delivery and regular updates
            """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            callbacks=callbacks or [],
            verbose=kwargs.get("verbose", False),
        )

    def _get_orchestrator_tools(self) -> List[Tool]:
        """Get tools for the orchestrator agent"""

        @tool
        def analyze_user_intent(user_input: str, user_context: str) -> str:
            """Analyze user intent and determine the best course of action."""
            return f"Intent analysis completed for: {user_input[:50]}..."

        @tool
        def route_to_specialist(specialist_type: str, request: str) -> str:
            """Route a request to the appropriate specialist agent."""
            return f"Request routed to {specialist_type}: {request[:50]}..."

        @tool
        def coordinate_multi_step_workflow(steps: str) -> str:
            """Coordinate a multi-step workflow across multiple agents."""
            return f"Workflow coordination initiated with steps: {steps[:50]}..."

        return [
            analyze_user_intent,
            route_to_specialist,
            coordinate_multi_step_workflow,
        ]

    def _get_task_tools(self) -> List[Tool]:
        """Get tools for the task specialist agent"""

        @tool
        def create_task_entry(
            title: str,
            description: str,
            priority: str = "medium",
            due_date: Optional[str] = None,
        ) -> str:
            """Create a new task with specified details."""
            try:
                # Integration point with TaskRepository
                return f"Task '{title}' created successfully"
            except Exception as e:
                return f"Error creating task: {str(e)}"

        @tool
        def update_task_status(task_id: str, new_status: str) -> str:
            """Update the status of an existing task."""
            try:
                # Integration point with TaskRepository
                return f"Task {task_id} status updated to {new_status}"
            except Exception as e:
                return f"Error updating task: {str(e)}"

        @tool
        def analyze_task_workload(user_id: str) -> str:
            """Analyze current task workload and provide insights."""
            try:
                # Integration point with TaskRepository for analysis
                return "Workload analysis completed with recommendations"
            except Exception as e:
                return f"Error analyzing workload: {str(e)}"

        @tool
        def extract_tasks_from_text(text: str) -> str:
            """Extract actionable tasks from unstructured text."""
            try:
                # Use NLP to extract tasks
                return "Tasks extracted and ready for creation"
            except Exception as e:
                return f"Error extracting tasks: {str(e)}"

        return [
            create_task_entry,
            update_task_status,
            analyze_task_workload,
            extract_tasks_from_text,
        ]

    def _get_conversation_tools(self) -> List[Tool]:
        """Get tools for the conversation specialist agent"""

        @tool
        def get_user_preferences(user_id: str) -> str:
            """Retrieve user preferences and personalization settings."""
            try:
                from uuid import UUID

                user = self.user_repo.get(UUID(user_id))
                if user and user.preferences:
                    return f"User preferences loaded: {user.preferences}"
                return "No specific preferences found, using defaults"
            except Exception as e:
                return f"Error getting preferences: {str(e)}"

        @tool
        def search_knowledge_base(query: str) -> str:
            """Search the knowledge base for relevant information."""
            try:
                # Integration point for knowledge base search
                return f"Knowledge base search completed for: {query}"
            except Exception as e:
                return f"Error searching knowledge base: {str(e)}"

        @tool
        def get_company_context(company_id: str) -> str:
            """Get company-specific context and information."""
            try:
                company = (
                    self.db.query(Company).filter(Company.id == company_id).first()
                )
                if company:
                    return f"Company context: {company.name} - {company.culture}"
                return "Company context not found"
            except Exception as e:
                return f"Error getting company context: {str(e)}"

        return [get_user_preferences, search_knowledge_base, get_company_context]

    def _get_analysis_tools(self) -> List[Tool]:
        """Get tools for the analysis specialist agent"""

        @tool
        def analyze_productivity_metrics(
            user_id: str, time_period: str = "week"
        ) -> str:
            """Analyze productivity metrics for the specified time period."""
            try:
                # Integration point for productivity analysis
                return f"Productivity analysis completed for {time_period}"
            except Exception as e:
                return f"Error analyzing productivity: {str(e)}"

        @tool
        def identify_patterns(data_type: str, user_id: str) -> str:
            """Identify patterns in user behavior or task completion."""
            try:
                # Integration point for pattern analysis
                return f"Pattern analysis completed for {data_type}"
            except Exception as e:
                return f"Error identifying patterns: {str(e)}"

        @tool
        def generate_insights(analysis_context: str) -> str:
            """Generate actionable insights from analysis results."""
            try:
                # Use LLM to generate insights
                return "Key insights generated with recommendations"
            except Exception as e:
                return f"Error generating insights: {str(e)}"

        return [analyze_productivity_metrics, identify_patterns, generate_insights]

    def _get_coordination_tools(self) -> List[Tool]:
        """Get tools for the coordination specialist agent"""

        @tool
        def schedule_team_meeting(
            participants: str, topic: str, duration: str = "30min"
        ) -> str:
            """Schedule a meeting with specified team members."""
            try:
                # Integration point for calendar/scheduling
                return f"Meeting scheduled: {topic} with {participants}"
            except Exception as e:
                return f"Error scheduling meeting: {str(e)}"

        @tool
        def send_team_notification(
            message: str, recipients: str, priority: str = "normal"
        ) -> str:
            """Send notification to team members."""
            try:
                # Integration point for notification system
                return f"Notification sent to {recipients}: {message[:30]}..."
            except Exception as e:
                return f"Error sending notification: {str(e)}"

        @tool
        def track_project_dependencies(project_id: str) -> str:
            """Track and analyze project dependencies and blockers."""
            try:
                # Integration point for project management
                return f"Dependencies tracked for project {project_id}"
            except Exception as e:
                return f"Error tracking dependencies: {str(e)}"

        return [
            schedule_team_meeting,
            send_team_notification,
            track_project_dependencies,
        ]

    def _get_reporting_tools(self) -> List[Tool]:
        """Get tools for the reporting specialist agent"""

        @tool
        def generate_status_report(
            report_type: str, time_period: str, user_id: str
        ) -> str:
            """Generate a status report for the specified parameters."""
            try:
                # Integration point for report generation
                return f"{report_type} report generated for {time_period}"
            except Exception as e:
                return f"Error generating report: {str(e)}"

        @tool
        def create_data_visualization(data_type: str, chart_type: str) -> str:
            """Create data visualizations and charts."""
            try:
                # Integration point for visualization tools
                return f"{chart_type} visualization created for {data_type}"
            except Exception as e:
                return f"Error creating visualization: {str(e)}"

        @tool
        def format_executive_summary(content: str) -> str:
            """Format content into an executive summary format."""
            try:
                # Use LLM to format executive summary
                return "Executive summary formatted successfully"
            except Exception as e:
                return f"Error formatting summary: {str(e)}"

        return [
            generate_status_report,
            create_data_visualization,
            format_executive_summary,
        ]


class AgentMemoryFactory:
    """Factory for creating different types of memory for agents"""

    @staticmethod
    def create_conversation_memory(
        k: int = 10, memory_key: str = "chat_history", return_messages: bool = True
    ) -> ConversationBufferWindowMemory:
        """Create conversation buffer window memory"""
        return ConversationBufferWindowMemory(
            k=k, memory_key=memory_key, return_messages=return_messages
        )


class AgentCallbackFactory:
    """Factory for creating callback handlers for agents"""

    @staticmethod
    def create_cost_tracking_callback() -> BaseCallbackHandler:
        """Create a callback handler for tracking API costs"""
        # This would implement cost tracking logic
        pass

    @staticmethod
    def create_performance_callback() -> BaseCallbackHandler:
        """Create a callback handler for performance monitoring"""
        # This would implement performance monitoring logic
        pass
