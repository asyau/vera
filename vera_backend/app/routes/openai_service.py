from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime

from app.services.openai_service import get_completion, get_summary

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

class SummaryRequest(BaseModel):
    messages: List[dict]  # List of messages to summarize
    max_tokens: int = 200

# Routes
@router.post("/ai/respond", response_model=MessageResponse)
async def ai_respond(request: MessageRequest):
    """Generate an AI response to a user message"""
    try:
        # Send the user's message to OpenAI
        ai_response = await get_completion(request.content)
        
        # Create and return the AI response
        return MessageResponse(
            id=str(uuid.uuid4()),
            content=ai_response,
            type="ai",
            name="Vira",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

@router.post("/ai/trichat-respond", response_model=MessageResponse)
async def trichat_respond(request: TriChatMessageRequest):
    """Process a TriChat message and generate AI response if @AI is mentioned"""
    if not request.is_at_ai:
        # If @AI is not mentioned, just return an empty response
        return None
    
    try:
        # Format the messages for processing
        messages_for_context = []
        for msg in request.messages:
            role = "user"
            if msg.get("type") == "ai":
                role = "assistant"
            elif msg.get("type") == "employee":
                role = "user" # Employee is also a user in OpenAI's context
                
            messages_for_context.append({
                "role": role,
                "content": f"{msg.get('name', '')}: {msg.get('content', '')}"
            })
        
        # Add the new message
        new_msg_role = "user" if request.new_message.type in ["user", "employee"] else "assistant"
        messages_for_context.append({
            "role": new_msg_role,
            "content": f"{request.new_message.name or ''}: {request.new_message.content}"
        })
        
        # Get AI response
        ai_response = await get_completion(
            prompt="",  # No additional prompt needed
            messages=messages_for_context
        )
        
        # Create and return the AI response
        return MessageResponse(
            id=str(uuid.uuid4()),
            content=ai_response,
            type="ai",
            name="Vira",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

@router.post("/ai/summarize", response_model=str)
async def summarize_conversation(request: SummaryRequest):
    """Summarize a conversation"""
    try:
        # Format the messages for summarization
        messages_for_summary = []
        for msg in request.messages:
            messages_for_summary.append(
                f"{msg.get('name', '')}: {msg.get('content', '')}"
            )
        
        # Get the summary
        summary = await get_summary(
            messages=messages_for_summary,
            max_tokens=request.max_tokens
        )
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}") 