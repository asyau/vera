from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List
import uuid
import logging

from app.models.sql_models import User, Conversation, Message
from app.models.pydantic_models import UserResponse
from app.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/contacts")
async def get_contacts(db: Session = Depends(get_db)):
    """Get all users as contacts."""
    try:
        users = db.query(User).options(
            joinedload(User.company),
            joinedload(User.team),
            joinedload(User.project)
        ).all()
        return [UserResponse.from_orm(user) for user in users]
    except Exception as e:
        logger.error(f"Error fetching contacts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching contacts: {str(e)}")

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, db: Session = Depends(get_db)):
    """Get all messages for a conversation."""
    try:
        # First verify the conversation exists
        conversation = db.query(Conversation).filter(Conversation.id == uuid.UUID(conversation_id)).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = db.query(Message).options(
            joinedload(Message.sender),
            joinedload(Message.conversation)
        ).filter(Message.conversation_id == uuid.UUID(conversation_id)).order_by(Message.timestamp).all()
        
        return messages
    except Exception as e:
        logger.error(f"Error fetching messages for conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str, 
    message_data: dict, 
    db: Session = Depends(get_db)
):
    """Send a message to a conversation."""
    try:
        # Verify the conversation exists
        conversation = db.query(Conversation).filter(Conversation.id == uuid.UUID(conversation_id)).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Create new message
        new_message = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id),
            sender_id=uuid.UUID(message_data.get("sender_id")),
            content=message_data.get("content"),
            type=message_data.get("type", "text"),
            is_read=False
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        # Update conversation's last_message_at
        conversation.last_message_at = new_message.timestamp
        db.commit()
        
        return new_message
    except Exception as e:
        logger.error(f"Error sending message to conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}") 