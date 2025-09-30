"""
AI Orchestration Service - Central hub for all AI operations
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import openai
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AIServiceError, ValidationError
from app.factories.ai_factory import AIRequestFactoryProvider, PromptTemplateFactory
from app.models.sql_models import Company, MemoryVector, User
from app.services.base import BaseService


class AIOrchestrationService(BaseService):
    """Central service for orchestrating all AI operations"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.factory = AIRequestFactoryProvider()

    async def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        user_id: UUID,
        conversation_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate personalized chat response using GPT-4o"""

        try:
            # Get user and company context for personalization
            user_context, company_context = await self._get_user_company_context(
                user_id
            )

            # Apply Model-Context-Protocol (MCP) for context construction
            enhanced_messages = await self._apply_mcp_context(
                messages, user_context, company_context, conversation_context
            )

            # Create chat completion request
            request_config = self.factory.create_chat_request(
                messages=enhanced_messages, max_tokens=1500, temperature=0.7
            )

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(**request_config)

            # Extract and return response
            ai_response = response.choices[0].message.content

            # Store interaction in memory for future context
            await self._store_interaction_memory(
                user_id, messages[-1]["content"], ai_response
            )

            return ai_response

        except Exception as e:
            raise AIServiceError(f"Failed to generate chat response: {str(e)}")

    async def extract_tasks_from_conversation(
        self, conversation: str, requester_id: UUID
    ) -> List[Dict[str, Any]]:
        """Extract actionable tasks from conversation text"""

        try:
            current_time = datetime.utcnow()
            system_prompt = f"""Extract task information from the following message.
            Return a JSON array of task objects with the following fields:
            - title: A short title for the task
            - description: A detailed description of the task
            - status: One of 'todo', 'assigned', 'in_progress', 'completed', 'cancelled'
            - priority: One of 'low', 'medium', 'high', 'urgent'
            - due_date: Today is {current_time.strftime('%Y-%m-%d %H:%M:%S')}. Use this information for calculating due date. The due date in YYYY-MM-DD format (if mentioned)
            - assignee_name: The name of the person to assign the task to (only if a specific person is mentioned, otherwise null)
            - tags: Array of relevant tags for the task
            Return ONLY the JSON array, nothing else.
            """

            # Create request
            request_config = self.factory.create_chat_request(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": conversation},
                ],
                max_tokens=1000,
                temperature=0.3,  # Lower temperature for more consistent extraction
            )

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(**request_config)
            ai_response = response.choices[0].message.content.strip()

            # Remove any markdown code block syntax if present
            ai_response = ai_response.replace("```json", "").replace("```", "").strip()

            # Parse JSON response
            try:
                tasks = json.loads(ai_response)

                # Ensure we have a list
                if isinstance(tasks, dict):
                    tasks = tasks.get("tasks", [])

                # Process each task to add missing fields and resolve assignee names to IDs
                processed_tasks = []
                for task in tasks:
                    # Resolve assignee name to ID
                    assignee_id = None
                    assignee_name = task.get("assignee_name")
                    if assignee_name:
                        assignee_id = await self._resolve_assignee_name_to_id(
                            assignee_name, requester_id
                        )

                    processed_task = {
                        "title": task.get("title", "Untitled Task"),
                        "description": task.get("description", ""),
                        "status": task.get("status", "todo"),
                        "priority": task.get("priority", "medium"),
                        "due_date": task.get("due_date"),
                        "assignee_name": assignee_name,  # Keep original name for reference
                        "assignee_id": assignee_id,  # Add resolved ID
                        "tags": task.get("tags", []),
                        "creator_id": str(requester_id),
                    }
                    processed_tasks.append(processed_task)

                return processed_tasks

            except json.JSONDecodeError:
                # Fallback: try to extract tasks from text response
                return self._parse_tasks_from_text(ai_response)

        except Exception as e:
            raise AIServiceError(f"Failed to extract tasks: {str(e)}")

    async def generate_daily_summary(
        self,
        user_id: UUID,
        tasks: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate personalized daily summary"""

        try:
            # Get user context for personalization
            user_context, company_context = await self._get_user_company_context(
                user_id
            )

            # Prepare summary content
            summary_content = self._prepare_daily_summary_content(
                tasks, messages, additional_context
            )

            # Create personalized summary prompt
            prompt = PromptTemplateFactory.create_personalization_prompt(
                user_context,
                company_context,
                f"Create a daily briefing summary:\n{summary_content}",
            )

            # Generate summary
            request_config = self.factory.create_chat_request(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.5,
            )

            response = self.openai_client.chat.completions.create(**request_config)
            return response.choices[0].message.content

        except Exception as e:
            raise AIServiceError(f"Failed to generate daily summary: {str(e)}")

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for text content"""

        try:
            embeddings = []

            for text in texts:
                request_config = self.factory.create_embedding_request(input_text=text)
                response = self.openai_client.embeddings.create(**request_config)
                embeddings.append(response.data[0].embedding)

            return embeddings

        except Exception as e:
            raise AIServiceError(f"Failed to create embeddings: {str(e)}")

    async def query_memory(
        self, user_id: UUID, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Query user's memory using vector similarity search"""

        try:
            # Create query embedding
            query_embedding = await self.create_embeddings([query])
            query_vector = query_embedding[0]

            # Query similar memories using pgvector
            similar_memories = (
                self.db.query(MemoryVector)
                .filter(MemoryVector.user_id == user_id)
                .order_by(MemoryVector.embedding.cosine_distance(query_vector))
                .limit(limit)
                .all()
            )

            return [
                {
                    "content": memory.content,
                    "metadata": memory.metadata,
                    "similarity": 1 - memory.embedding.cosine_distance(query_vector),
                    "created_at": memory.created_at,
                }
                for memory in similar_memories
            ]

        except Exception as e:
            raise AIServiceError(f"Failed to query memory: {str(e)}")

    async def handle_trichat_context(
        self,
        participants: List[UUID],
        messages: List[Dict[str, str]],
        current_user_id: UUID,
    ) -> str:
        """Handle multi-user chat context with MCP"""

        try:
            # Get context for all participants
            participant_contexts = []
            for participant_id in participants:
                user_context, company_context = await self._get_user_company_context(
                    participant_id
                )
                participant_contexts.append(
                    {
                        "user_id": str(participant_id),
                        "context": user_context,
                        "company": company_context,
                    }
                )

            # Create enhanced system prompt for multi-user context
            system_prompt = self._create_trichat_system_prompt(
                participant_contexts, current_user_id
            )

            # Generate response with multi-user awareness
            request_config = self.factory.create_chat_request(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=1200,
                temperature=0.8,
            )

            response = self.openai_client.chat.completions.create(**request_config)
            return response.choices[0].message.content

        except Exception as e:
            raise AIServiceError(f"Failed to handle TriChat context: {str(e)}")

    async def convert_text_to_speech(self, text: str, voice: str = "alloy") -> bytes:
        """Convert text to speech using OpenAI TTS"""

        try:
            request_config = self.factory.create_tts_request(
                text=text, voice=voice, model="tts-1"
            )

            response = self.openai_client.audio.speech.create(**request_config)
            return response.content

        except Exception as e:
            raise AIServiceError(f"Failed to convert text to speech: {str(e)}")

    async def convert_speech_to_text(self, audio_file) -> str:
        """Convert speech to text using Whisper"""

        try:
            request_config = self.factory.create_stt_request(audio_file=audio_file)
            response = self.openai_client.audio.transcriptions.create(**request_config)
            return response.text

        except Exception as e:
            raise AIServiceError(f"Failed to convert speech to text: {str(e)}")

    async def _get_user_company_context(
        self, user_id: UUID
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Get user and company context for personalization"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValidationError("User not found")

        company = self.db.query(Company).filter(Company.id == user.company_id).first()

        user_context = {
            "name": user.name,
            "role": user.role,
            "team": user.team_id,
            "preferences": user.preferences or {},
        }

        company_context = {
            "name": company.name if company else "Unknown",
            "culture": company.culture if company else "professional",
            "communication_style": company.communication_style if company else "formal",
        }

        return user_context, company_context

    async def _apply_mcp_context(
        self,
        messages: List[Dict[str, str]],
        user_context: Dict[str, Any],
        company_context: Dict[str, Any],
        conversation_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, str]]:
        """Apply Model-Context-Protocol for enhanced context"""

        # Create system message with MCP context
        mcp_system_prompt = f"""
        You are Vira, an AI assistant for {company_context['name']}.

        Current user: {user_context['name']} ({user_context['role']})
        Company culture: {company_context['culture']}
        Communication style: {company_context['communication_style']}

        Guidelines:
        1. Adapt your tone to match the company culture
        2. Consider the user's role when providing suggestions
        3. Be helpful, professional, and contextually aware
        4. If discussing tasks, consider the user's responsibilities
        """

        # Add conversation context if available
        if conversation_context:
            mcp_system_prompt += f"\nConversation context: {conversation_context}"

        # Prepend system message
        enhanced_messages = [{"role": "system", "content": mcp_system_prompt}]
        enhanced_messages.extend(messages)

        return enhanced_messages

    async def _store_interaction_memory(
        self, user_id: UUID, user_message: str, ai_response: str
    ) -> None:
        """Store conversation interaction in memory for future context"""

        try:
            # Create memory content
            memory_content = f"User: {user_message}\nVira: {ai_response}"

            # Create embedding
            embedding = await self.create_embeddings([memory_content])

            # Store in database
            memory_vector = MemoryVector(
                user_id=user_id,
                content=memory_content,
                embedding=embedding[0],
                metadata={"type": "conversation", "timestamp": str(datetime.utcnow())},
            )

            self.db.add(memory_vector)
            self.db.commit()

        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Failed to store interaction memory: {str(e)}")

    def _prepare_daily_summary_content(
        self,
        tasks: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Prepare content for daily summary generation"""

        content_parts = []

        if tasks:
            content_parts.append(f"Tasks: {json.dumps(tasks, indent=2)}")

        if messages:
            content_parts.append(
                f"Recent conversations: {json.dumps(messages, indent=2)}"
            )

        if additional_context:
            content_parts.append(
                f"Additional context: {json.dumps(additional_context, indent=2)}"
            )

        return "\n\n".join(content_parts)

    def _create_trichat_system_prompt(
        self, participant_contexts: List[Dict[str, Any]], current_user_id: UUID
    ) -> str:
        """Create system prompt for TriChat multi-user context"""

        prompt = (
            "You are Vira, facilitating a multi-user conversation.\n\nParticipants:\n"
        )

        for context in participant_contexts:
            user_info = context["context"]
            prompt += f"- {user_info['name']} ({user_info['role']})\n"

        prompt += "\nGuidelines:\n"
        prompt += "1. Address users by name when relevant\n"
        prompt += "2. Consider each user's role and context\n"
        prompt += "3. Facilitate productive collaboration\n"
        prompt += "4. Summarize or clarify when needed\n"

        return prompt

    async def _resolve_assignee_name_to_id(
        self, assignee_name: str, requester_id: UUID
    ) -> Optional[UUID]:
        """
        Resolve a human-readable assignee name to a user ID.
        Searches within the requester's company/team for matching users.
        """
        try:
            from app.repositories.user_repository import UserRepository

            user_repo = UserRepository(self.db)

            # Get the requester's company_id to limit search scope
            requester = user_repo.get_or_raise(requester_id)
            company_id = requester.company_id

            # Search for users in the same company by name (case-insensitive)
            # This handles variations like "John", "john", "John Smith", etc.
            assignee_name_lower = assignee_name.lower().strip()

            # Use the search_by_name method for more efficient searching
            matching_users = user_repo.search_by_name(assignee_name, str(company_id))

            if matching_users:
                # Try exact name match first
                for user in matching_users:
                    if user.name.lower() == assignee_name_lower:
                        return user.id

                # Try first name match
                for user in matching_users:
                    first_name = (
                        user.name.lower().split()[0]
                        if user.name.lower().split()
                        else user.name.lower()
                    )
                    if first_name == assignee_name_lower:
                        return user.id

                # Return the first match if no exact match found
                return matching_users[0].id

            # No match found
            return None

        except Exception as e:
            # Log the error but don't fail the entire task extraction
            print(f"Error resolving assignee name '{assignee_name}': {str(e)}")
            return None

    def _parse_tasks_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Fallback method to parse tasks from text response"""
        # Simple text parsing as fallback
        # This would be enhanced with more sophisticated parsing logic
        return [{"title": "Manual review needed", "description": text}]
