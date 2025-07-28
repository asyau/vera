from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime
import logging

from app.models.sql_models import User, Conversation, Message, Team
from app.models.pydantic_models import UserResponse, MessageResponse
from app.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Additional models for enhanced messaging features
class Contact(BaseModel):
    id: str
    name: str
    email: str
    role: str
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    company_name: Optional[str] = None
    is_online: bool = False
    last_seen: Optional[str] = None
    can_message: bool = True

class CreateConversationRequest(BaseModel):
    type: str  # 'direct' | 'group'
    name: Optional[str] = None
    participants: List[str]  # List of user IDs

class SendMessageRequest(BaseModel):
    conversation_id: str
    content: str
    attachments: Optional[List[dict]] = None

# Helper function to check hierarchy-based permissions
def can_message_user(current_user: User, target_user: User, db: Session) -> bool:
    """
    Check if current_user can message target_user based on hierarchy rules.
    
    Rules:
    - Employees can message their peers and direct supervisors
    - Supervisors can message anyone in their team and their own supervisors
    - Cannot message users higher up in hierarchy unless they're your direct supervisor
    """
    # Same user
    if current_user.id == target_user.id:
        return False
    
    # Same team - always allowed
    if current_user.team_id == target_user.team_id:
        return True
    
    # If current user is supervisor, they can message employees
    if current_user.role == 'supervisor' and target_user.role == 'employee':
        return True
    
    # If current user is employee, they can only message their direct supervisor
    if current_user.role == 'employee' and target_user.role == 'supervisor':
        # Check if target_user is the supervisor of current_user's team
        team = db.query(Team).filter(Team.id == current_user.team_id).first()
        if team and team.supervisor_id == target_user.id:
            return True
    
    return False

@router.get("/contacts", response_model=List[Contact])
async def get_contacts(current_user_id: str, db: Session = Depends(get_db)):
    """Get all users as contacts with hierarchy-based permissions."""
    try:
        # Get current user
        current_user = db.query(User).filter(User.id == uuid.UUID(current_user_id)).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get all users with their relationships
        users = db.query(User).options(
            joinedload(User.company),
            joinedload(User.team),
            joinedload(User.project)
        ).all()
        
        contacts = []
        for user in users:
            if user.id != current_user.id:  # Exclude self
                can_message = can_message_user(current_user, user, db)
                
                contact = Contact(
                    id=str(user.id),
                    name=user.name,
                    email=user.email,
                    role=user.role,
                    team_id=str(user.team_id) if user.team_id else None,
                    team_name=user.team.name if user.team else None,
                    company_name=user.company.name if user.company else None,
                    is_online=True,  # Mock online status for now
                    can_message=can_message
                )
                contacts.append(contact)
        
        return contacts
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
        
        return [MessageResponse.from_orm(message) for message in messages]
    except Exception as e:
        logger.error(f"Error fetching messages for conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str, 
    request: SendMessageRequest,
    current_user_id: str,
    db: Session = Depends(get_db)
):
    """Send a message to a conversation."""
    try:
        # Get current user
        current_user = db.query(User).filter(User.id == uuid.UUID(current_user_id)).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify the conversation exists
        conversation = db.query(Conversation).filter(Conversation.id == uuid.UUID(conversation_id)).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Create new message
        new_message = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id),
            sender_id=current_user.id,
            content=request.content,
            type="text",  # Default to text, could be enhanced to support other types
            is_read=False
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        # Update conversation's last_message_at
        conversation.last_message_at = new_message.timestamp
        db.commit()
        
        # Check for @Vira mentions and trigger AI response if needed
        if "@vira" in request.content.lower() or "@vira" in request.content:
            # TODO: Integrate with AI service to generate response
            # This would call the existing AI service endpoints
            pass
        
        return MessageResponse.from_orm(new_message)
    except Exception as e:
        logger.error(f"Error sending message to conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

@router.post("/conversations", response_model=dict)
async def create_conversation(
    request: CreateConversationRequest,
    current_user_id: str,
    db: Session = Depends(get_db)
):
    """Create a new conversation with hierarchy-based permissions."""
    try:
        # Get current user
        current_user = db.query(User).filter(User.id == uuid.UUID(current_user_id)).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate participants
        participant_uuids = []
        for participant_id in request.participants:
            try:
                participant_uuid = uuid.UUID(participant_id)
                user = db.query(User).filter(User.id == participant_uuid).first()
                if not user:
                    raise HTTPException(status_code=404, detail=f"User {participant_id} not found")
                
                # Check hierarchy permissions
                if not can_message_user(current_user, user, db):
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Cannot create conversation with {user.name} due to hierarchy restrictions"
                    )
                
                participant_uuids.append(participant_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid user ID format: {participant_id}")
        
        # Add current user to participants if not already included
        if current_user.id not in participant_uuids:
            participant_uuids.append(current_user.id)
        
        # Generate conversation name for direct messages
        conversation_name = request.name
        if request.type == "direct" and len(participant_uuids) == 2:
            other_user_id = next(pid for pid in participant_uuids if pid != current_user.id)
            other_user = db.query(User).filter(User.id == other_user_id).first()
            conversation_name = other_user.name if other_user else "Unknown User"
        elif not conversation_name:
            conversation_name = f"Group Chat ({len(participant_uuids)} members)"
        
        # Create conversation
        new_conversation = Conversation(
            id=uuid.uuid4(),
            type=request.type,
            participant_ids=participant_uuids,
            created_at=datetime.now(),
            last_message_at=datetime.now()
        )
        
        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)
        
        return {
            "id": str(new_conversation.id),
            "type": new_conversation.type,
            "name": conversation_name,
            "participants": [str(pid) for pid in participant_uuids],
            "created_at": new_conversation.created_at.isoformat(),
            "updated_at": new_conversation.last_message_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(e)}")

@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: str,
    current_user_id: str,
    db: Session = Depends(get_db)
):
    """Get messaging permissions for a specific user."""
    try:
        current_user = db.query(User).filter(User.id == uuid.UUID(current_user_id)).first()
        target_user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        
        if not current_user or not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        can_message = can_message_user(current_user, target_user, db)
        
        return {
            "can_message": can_message,
            "reason": "Hierarchy restrictions" if not can_message else "Allowed",
            "target_user": {
                "id": str(target_user.id),
                "name": target_user.name,
                "role": target_user.role,
                "team_name": target_user.team.name if target_user.team else None
            }
        }
    except Exception as e:
        logger.error(f"Error getting user permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting user permissions: {str(e)}") 