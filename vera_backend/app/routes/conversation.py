from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime

router = APIRouter()

# Models
class Message(BaseModel):
    id: str
    content: str
    type: str  # 'user' | 'ai' | 'employee'
    name: Optional[str] = None
    timestamp: str

class Conversation(BaseModel):
    id: str
    messages: List[Message]
    created_at: str
    updated_at: str

# In-memory storage (replace with database later)
conversations: Dict[str, Conversation] = {}

# Routes
@router.post("/conversation", status_code=201)
async def create_conversation():
    """Create a new conversation"""
    conversation_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    # Create initial conversation with AI welcome message
    conversations[conversation_id] = Conversation(
        id=conversation_id,
        messages=[
            Message(
                id=str(uuid.uuid4()),
                content="Hello! I'm Vira, your AI assistant. How can I help you today?",
                type="ai",
                name="Vira",
                timestamp=now
            )
        ],
        created_at=now,
        updated_at=now
    )
    
    return conversations[conversation_id]

@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a specific conversation by ID"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversations[conversation_id]

@router.get("/conversations")
async def list_conversations():
    """List all conversations"""
    return list(conversations.values())

@router.post("/conversation/{conversation_id}/message")
async def add_message(conversation_id: str, message: Message):
    """Add a message to a conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Add the message to the conversation
    conversation = conversations[conversation_id]
    conversation.messages.append(message)
    conversation.updated_at = datetime.now().isoformat()
    
    return {"status": "success", "message": "Message added"} 