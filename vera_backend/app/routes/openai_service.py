from fastapi import APIRouter, HTTPException, Depends, Body, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime
import tempfile
import os

from app.services.openai_service import get_completion, get_summary, transcribe_audio

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

class TeamChatMessageRequest(BaseModel):
    conversation_id: str
    messages: List[dict]  # List of previous messages
    new_message: MessageRequest
    is_at_ai: bool = False  # Whether the message contains @AI

class SummaryRequest(BaseModel):
    messages: List[dict]  # List of messages to summarize
    max_tokens: int = 200

class BriefingExplanationRequest(BaseModel):
    completed_tasks: List[dict]
    delayed_tasks: List[dict]
    upcoming_tasks: List[dict]
    tomorrow_tasks: List[dict]

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

@router.post("/ai/team-chat-respond", response_model=MessageResponse)
async def team_chat_respond(request: TeamChatMessageRequest):
    """Process a Team Chat message and generate AI response if @AI is mentioned"""
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

@router.post("/ai/team-chat-respond", response_model=MessageResponse)
async def team_chat_respond(request: dict):
    """Process team chat messages and generate AI response"""
    try:
        messages = request.get("messages", [])
        
        # Format the messages for processing
        messages_for_context = []
        for msg in messages:
            role = "user"
            if msg.get("role") == "assistant":
                role = "assistant"
                
            messages_for_context.append({
                "role": role,
                "content": msg.get("content", "")
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

@router.post("/ai/transcribe")
async def transcribe_audio_file(file: UploadFile = File(...)):
    """Transcribe audio using OpenAI's Whisper API"""
    try:
        # Create a temporary file to store the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Transcribe the audio file
            transcription = await transcribe_audio(temp_file_path)
            return {"text": transcription}
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")

@router.post("/ai/explain-briefing")
async def explain_briefing(request: BriefingExplanationRequest):
    """Generate a detailed explanation of the daily briefing"""
    try:
        # Format the briefing data for the AI
        briefing_context = f"""
        Today's briefing includes:
        
        Completed Tasks ({len(request.completed_tasks)}):
        {format_tasks(request.completed_tasks)}
        
        Delayed Tasks ({len(request.delayed_tasks)}):
        {format_tasks(request.delayed_tasks)}
        
        Upcoming Tasks ({len(request.upcoming_tasks)}):
        {format_tasks(request.upcoming_tasks)}
        
        Tomorrow's Tasks ({len(request.tomorrow_tasks)}):
        {format_tasks(request.tomorrow_tasks)}
        """
        
        # Create a prompt for detailed explanation
        prompt = f"""
        Please provide a detailed, conversational explanation of this daily briefing.
        Focus on:
        1. Overall progress and achievements
        2. Areas needing attention
        3. Priority tasks for today
        4. Potential challenges and suggestions
        5. Team workload distribution
        
        Make it sound natural and engaging, as if you're explaining it to a team member.
        
        Briefing Data:
        {briefing_context}
        """
        
        # Get the explanation from OpenAI
        explanation = await get_completion(
            prompt=prompt,
            model="gpt-4",
            max_tokens=1000
        )
        
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")

def format_tasks(tasks: List[dict]) -> str:
    """Format tasks for the AI prompt"""
    return "\n".join([
        f"- {task['name']} (Assigned to: {task['assignedTo']}" + 
        (f", Due: {task['dueDate']}" if task.get('dueDate') else "") + ")"
        for task in tasks
    ]) 