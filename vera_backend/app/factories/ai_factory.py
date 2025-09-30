"""
Factory classes for AI service components
Implements the Factory pattern for AI request creation
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.config import settings


class AIModelType(Enum):
    """Enumeration of supported AI model types"""

    CHAT_COMPLETION = "chat_completion"
    EMBEDDING = "embedding"
    TTS = "text_to_speech"
    STT = "speech_to_text"


class AIRequestFactory(ABC):
    """Abstract factory for creating AI requests"""

    @abstractmethod
    def create_request(self, **kwargs) -> Dict[str, Any]:
        """Create an AI request configuration"""
        pass


class ChatCompletionFactory(AIRequestFactory):
    """Factory for creating OpenAI chat completion requests"""

    def create_request(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a chat completion request"""

        # Use default model if not specified
        if not model:
            model = settings.openai_model

        # Prepare messages with system prompt if provided
        request_messages = []
        if system_prompt:
            request_messages.append({"role": "system", "content": system_prompt})

        request_messages.extend(messages)

        return {
            "model": model,
            "messages": request_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }


class EmbeddingFactory(AIRequestFactory):
    """Factory for creating OpenAI embedding requests"""

    def create_request(
        self, input_text: str, model: str = "text-embedding-ada-002", **kwargs
    ) -> Dict[str, Any]:
        """Create an embedding request"""

        return {"model": model, "input": input_text, **kwargs}


class TTSFactory(AIRequestFactory):
    """Factory for creating Text-to-Speech requests"""

    def create_request(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1",
        response_format: str = "mp3",
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a TTS request"""

        return {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": response_format,
            **kwargs,
        }


class STTFactory(AIRequestFactory):
    """Factory for creating Speech-to-Text requests"""

    def create_request(
        self,
        audio_file,
        model: str = "whisper-1",
        language: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create an STT request"""

        request = {"model": model, "file": audio_file, **kwargs}

        if language:
            request["language"] = language

        return request


class AIRequestFactoryProvider:
    """Provider class for getting appropriate AI request factories"""

    _factories = {
        AIModelType.CHAT_COMPLETION: ChatCompletionFactory(),
        AIModelType.EMBEDDING: EmbeddingFactory(),
        AIModelType.TTS: TTSFactory(),
        AIModelType.STT: STTFactory(),
    }

    @classmethod
    def get_factory(cls, model_type: AIModelType) -> AIRequestFactory:
        """Get the appropriate factory for the model type"""
        factory = cls._factories.get(model_type)
        if not factory:
            raise ValueError(f"No factory available for model type: {model_type}")
        return factory

    @classmethod
    def create_chat_request(cls, **kwargs) -> Dict[str, Any]:
        """Convenience method for creating chat completion requests"""
        factory = cls.get_factory(AIModelType.CHAT_COMPLETION)
        return factory.create_request(**kwargs)

    @classmethod
    def create_embedding_request(cls, **kwargs) -> Dict[str, Any]:
        """Convenience method for creating embedding requests"""
        factory = cls.get_factory(AIModelType.EMBEDDING)
        return factory.create_request(**kwargs)

    @classmethod
    def create_tts_request(cls, **kwargs) -> Dict[str, Any]:
        """Convenience method for creating TTS requests"""
        factory = cls.get_factory(AIModelType.TTS)
        return factory.create_request(**kwargs)

    @classmethod
    def create_stt_request(cls, **kwargs) -> Dict[str, Any]:
        """Convenience method for creating STT requests"""
        factory = cls.get_factory(AIModelType.STT)
        return factory.create_request(**kwargs)


class PromptTemplateFactory:
    """Factory for creating standardized prompt templates"""

    @staticmethod
    def create_task_extraction_prompt(conversation: str) -> str:
        """Create prompt for task extraction from conversation"""
        return f"""
        Analyze the following conversation and extract any actionable tasks or assignments.

        Conversation:
        {conversation}

        For each task, provide:
        - Title: Brief description of the task
        - Description: Detailed explanation
        - Assignee: Who should complete the task (if mentioned)
        - Due date: When it should be completed (if mentioned)
        - Priority: low, medium, high, or urgent

        Return the response in JSON format with an array of tasks.
        """

    @staticmethod
    def create_summarization_prompt(content: str, summary_type: str = "general") -> str:
        """Create prompt for content summarization"""
        templates = {
            "general": "Summarize the following content in a clear and concise manner:",
            "meeting": "Summarize this meeting transcript, highlighting key decisions and action items:",
            "daily": "Create a daily briefing summary from the following information:",
            "project": "Summarize the project status and key updates:",
        }

        template = templates.get(summary_type, templates["general"])
        return f"{template}\n\n{content}"

    @staticmethod
    def create_personalization_prompt(
        user_context: Dict[str, Any], company_context: Dict[str, Any], query: str
    ) -> str:
        """Create personalized response prompt based on context"""
        return f"""
        You are Vira, an AI assistant for {company_context.get('name', 'the company')}.

        User Context:
        - Name: {user_context.get('name')}
        - Role: {user_context.get('role')}
        - Team: {user_context.get('team')}

        Company Context:
        - Culture: {company_context.get('culture', 'professional')}
        - Communication Style: {company_context.get('communication_style', 'formal')}

        Please respond to the following query in a manner that fits the company culture and the user's role:

        {query}
        """
