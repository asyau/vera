"""
Enhanced AI Service Routes using LangChain Orchestrator
"""
import os
import tempfile
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api_gateway import AuthenticationMiddleware
from app.database import get_db
from app.services.ai_orchestration_service import AIOrchestrationService
from app.services.langchain_orchestrator import LangChainOrchestrator

router = APIRouter()


# Models
class MessageRequest(BaseModel):
    content: str
    type: str  # 'user' | 'ai' | 'employee'
    name: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    content: str
    type: str
    name: Optional[str] = None
    timestamp: str


class TriChatMessageRequest(BaseModel):
    conversation_id: str
    messages: List[dict]  # List of previous messages
    new_message: MessageRequest
    is_at_ai: bool = False  # Whether the message contains @AI


class TaskExtractionRequest(BaseModel):
    conversation: str


class SummaryRequest(BaseModel):
    content: str
    summary_type: str = "general"


class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy"


class LangChainRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


class LangChainResponse(BaseModel):
    content: str
    intent: Dict[str, Any]
    agent_used: str
    metadata: Dict[str, Any]
    cost_info: Optional[Dict[str, Any]] = None


# Routes
@router.post("/langchain", response_model=LangChainResponse)
async def langchain_orchestrator(
    request: LangChainRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Process user request through LangChain orchestrator"""
    try:
        orchestrator = LangChainOrchestrator(db)

        # Process user request with intelligent routing
        response = await orchestrator.process_user_request(
            user_input=request.message,
            user_id=uuid.UUID(current_user_id),
            context=request.context,
        )

        return LangChainResponse(
            content=response["content"],
            intent=response["intent"],
            agent_used=response["agent_used"],
            metadata=response["metadata"],
            cost_info=response.get("cost_info"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"LangChain orchestrator error: {str(e)}"
        )


@router.post("/chat", response_model=MessageResponse)
async def chat_completion(
    request: MessageRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Generate AI chat response (Legacy endpoint - routes to LangChain)"""
    try:
        # Route to LangChain orchestrator for enhanced capabilities
        orchestrator = LangChainOrchestrator(db)

        response = await orchestrator.process_user_request(
            user_input=request.content, user_id=uuid.UUID(current_user_id)
        )

        return MessageResponse(
            id=str(uuid.uuid4()),
            content=response["content"],
            type="ai",
            name="Vira",
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        # Fallback to original service if LangChain fails
        try:
            ai_service = AIOrchestrationService(db)
            messages = [{"role": "user", "content": request.content}]
            ai_response = await ai_service.generate_chat_response(
                messages=messages, user_id=uuid.UUID(current_user_id)
            )

            return MessageResponse(
                id=str(uuid.uuid4()),
                content=ai_response,
                type="ai",
                name="Vira",
                timestamp=datetime.utcnow().isoformat(),
            )
        except Exception as fallback_error:
            raise HTTPException(
                status_code=500,
                detail=f"AI chat error: {str(e)}, Fallback error: {str(fallback_error)}",
            )


@router.post("/trichat-respond", response_model=MessageResponse)
async def trichat_respond(
    request: TriChatMessageRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Process a TriChat message and generate AI response if @AI is mentioned"""
    if not request.is_at_ai:
        return None

    try:
        ai_service = AIOrchestrationService(db)

        # Format messages for context
        formatted_messages = []
        for msg in request.messages:
            role = "assistant" if msg.get("type") == "ai" else "user"
            content = f"{msg.get('name', '')}: {msg.get('content', '')}"
            formatted_messages.append({"role": role, "content": content})

        # Add the new message
        new_msg_content = (
            f"{request.new_message.name or ''}: {request.new_message.content}"
        )
        formatted_messages.append({"role": "user", "content": new_msg_content})

        # Extract participant IDs (mock for now)
        participant_ids = [
            uuid.UUID(current_user_id)
        ]  # Add other participants as needed

        # Generate TriChat response
        ai_response = await ai_service.handle_trichat_context(
            participants=participant_ids,
            messages=formatted_messages,
            current_user_id=uuid.UUID(current_user_id),
        )

        return MessageResponse(
            id=str(uuid.uuid4()),
            content=ai_response,
            type="ai",
            name="Vira",
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TriChat error: {str(e)}")


@router.post("/extract-tasks")
async def extract_tasks(
    request: TaskExtractionRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Extract tasks from conversation text"""
    try:
        ai_service = AIOrchestrationService(db)

        tasks = await ai_service.extract_tasks_from_conversation(
            conversation=request.conversation, requester_id=uuid.UUID(current_user_id)
        )

        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task extraction error: {str(e)}")


@router.post("/summary")
async def generate_summary(
    request: SummaryRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Generate content summary"""
    try:
        ai_service = AIOrchestrationService(db)

        # Mock data for daily summary
        tasks = []  # Would be fetched from task service
        messages = []  # Would be fetched from conversation service

        summary = await ai_service.generate_daily_summary(
            user_id=uuid.UUID(current_user_id), tasks=tasks, messages=messages
        )

        return {"summary": summary}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Summary generation error: {str(e)}"
        )


@router.post("/speech")
async def text_to_speech(
    request: TTSRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Convert text to speech"""
    try:
        ai_service = AIOrchestrationService(db)

        audio_content = await ai_service.convert_text_to_speech(
            text=request.text, voice=request.voice
        )

        return {"audio_data": audio_content, "content_type": "audio/mp3"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")


@router.post("/transcribe")
async def speech_to_text(
    audio: UploadFile = File(...),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Convert speech to text"""
    try:
        ai_service = AIOrchestrationService(db)

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Transcribe audio
            with open(temp_file_path, "rb") as audio_file:
                transcription = await ai_service.convert_speech_to_text(audio_file)

            return {"transcription": transcription}
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {str(e)}")


@router.get("/daily-summary")
async def get_daily_summary(
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get personalized daily summary"""
    try:
        ai_service = AIOrchestrationService(db)

        # Mock data - in real implementation, fetch from respective services
        tasks = []  # Fetch from task service
        messages = []  # Fetch from conversation service

        summary = await ai_service.generate_daily_summary(
            user_id=uuid.UUID(current_user_id), tasks=tasks, messages=messages
        )

        return {"summary": summary, "generated_at": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Daily summary error: {str(e)}")


@router.post("/memory/query")
async def query_memory(
    query: str = Body(..., embed=True),
    limit: int = Body(5, embed=True),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Query user's AI memory"""
    try:
        ai_service = AIOrchestrationService(db)

        memories = await ai_service.query_memory(
            user_id=uuid.UUID(current_user_id), query=query, limit=limit
        )

        return {"memories": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory query error: {str(e)}")


# LangChain Orchestrator Management Endpoints


@router.get("/langchain/stats")
async def get_orchestrator_stats(
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get orchestrator statistics and capabilities"""
    try:
        orchestrator = LangChainOrchestrator(db)
        stats = orchestrator.get_agent_stats()

        return {
            "status": "active",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")


@router.get("/langchain/conversation-history")
async def get_conversation_history(
    limit: int = 10,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get recent conversation history from orchestrator"""
    try:
        orchestrator = LangChainOrchestrator(db)
        history = await orchestrator.get_conversation_history(limit=limit)

        return {
            "history": history,
            "count": len(history),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History error: {str(e)}")


@router.post("/langchain/clear-history")
async def clear_conversation_history(
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Clear conversation history for the orchestrator"""
    try:
        orchestrator = LangChainOrchestrator(db)
        await orchestrator.clear_conversation_history()

        return {
            "message": "Conversation history cleared successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear history error: {str(e)}")


@router.post("/langchain/analyze-intent")
async def analyze_intent_only(
    request: LangChainRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Analyze user intent without executing the request"""
    try:
        orchestrator = LangChainOrchestrator(db)
        user_context = await orchestrator._get_user_context(uuid.UUID(current_user_id))

        intent_analysis = await orchestrator._analyze_user_intent(
            request.message, user_context
        )

        return {
            "intent_analysis": intent_analysis,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent analysis error: {str(e)}")
