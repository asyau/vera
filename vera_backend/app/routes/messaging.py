"""
Enhanced Messaging Routes using Communication Service
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.api_gateway import AuthenticationMiddleware
from app.core.exceptions import ViraException
from app.database import get_db
from app.services.communication_service import CommunicationService

router = APIRouter()


# Additional models for messaging features
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


# Request/Response Models
class CreateConversationRequest(BaseModel):
    title: str
    type: str = "direct"  # direct, group, trichat
    participants: Optional[List[str]] = None


class SendMessageRequest(BaseModel):
    content: str
    type: str = "text"
    metadata: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    type: str
    creator_id: str
    participants: List[str]
    last_message_at: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: str
    type: str
    timestamp: str
    is_read: bool
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


# Helper function for contact permissions
def can_message_user(current_user, target_user) -> bool:
    """Check if current user can message target user based on hierarchy"""
    if current_user.id == target_user.id:
        return False

    # Same team - always allowed
    if current_user.team_id == target_user.team_id:
        return True

    # Supervisor can message employees
    if current_user.role == "supervisor" and target_user.role == "employee":
        return True

    # Employee can message their supervisor
    if current_user.role == "employee" and target_user.role == "supervisor":
        return True

    return False


# Routes
@router.get("/contacts", response_model=List[Contact])
async def get_contacts(
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get all users as contacts with hierarchy-based permissions"""
    try:
        from sqlalchemy.orm import joinedload

        from app.models.sql_models import User

        # Get current user
        current_user = db.query(User).filter(User.id == UUID(current_user_id)).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get all users with their relationships
        users = (
            db.query(User)
            .options(joinedload(User.company), joinedload(User.team))
            .all()
        )

        contacts = []
        for user in users:
            if user.id != current_user.id:  # Exclude self
                can_message = can_message_user(current_user, user)

                contact = Contact(
                    id=str(user.id),
                    name=user.name,
                    email=user.email,
                    role=user.role,
                    team_id=str(user.team_id) if user.team_id else None,
                    team_name=user.team.name if user.team else None,
                    company_name=user.company.name if user.company else None,
                    is_online=True,  # Mock online status for now
                    can_message=can_message,
                )
                contacts.append(contact)

        return contacts

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contacts: {str(e)}")


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new conversation"""
    try:
        comm_service = CommunicationService(db)

        # Convert participant strings to UUIDs
        participant_uuids = []
        if request.participants:
            participant_uuids = [UUID(pid) for pid in request.participants]

        conversation = comm_service.create_conversation(
            creator_id=UUID(current_user_id),
            title=request.title,
            conversation_type=request.type,
            participants=participant_uuids,
        )

        return ConversationResponse.from_orm(conversation)

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create conversation: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    conversation_type: Optional[str] = Query(
        None, description="Filter by conversation type"
    ),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user's conversations"""
    try:
        comm_service = CommunicationService(db)

        conversations = comm_service.get_user_conversations(
            user_id=UUID(current_user_id), conversation_type=conversation_type
        )

        return [ConversationResponse.from_orm(conv) for conv in conversations]

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get conversations: {str(e)}"
        )


@router.get(
    "/conversations/{conversation_id}/messages", response_model=List[MessageResponse]
)
async def get_messages(
    conversation_id: UUID,
    limit: int = Query(50, description="Number of messages to retrieve"),
    offset: int = Query(0, description="Number of messages to skip"),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get messages from a conversation"""
    try:
        comm_service = CommunicationService(db)

        messages = comm_service.get_conversation_messages(
            conversation_id=conversation_id,
            requester_id=UUID(current_user_id),
            limit=limit,
            offset=offset,
        )

        return [MessageResponse.from_orm(msg) for msg in messages]

    except ViraException as e:
        raise HTTPException(
            status_code=404 if "not found" in e.message.lower() else 400,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.post(
    "/conversations/{conversation_id}/messages", response_model=MessageResponse
)
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Send a message to a conversation"""
    try:
        comm_service = CommunicationService(db)

        message = comm_service.send_message(
            conversation_id=conversation_id,
            sender_id=UUID(current_user_id),
            content=request.content,
            message_type=request.type,
            metadata=request.metadata,
        )

        return MessageResponse.from_orm(message)

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.post("/conversations/{conversation_id}/read")
async def mark_messages_as_read(
    conversation_id: UUID,
    message_ids: Optional[List[str]] = None,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Mark messages as read"""
    try:
        comm_service = CommunicationService(db)

        # Convert string IDs to UUIDs if provided
        message_uuids = None
        if message_ids:
            message_uuids = [UUID(mid) for mid in message_ids]

        count = comm_service.mark_messages_as_read(
            conversation_id=conversation_id,
            user_id=UUID(current_user_id),
            message_ids=message_uuids,
        )

        return {"message": f"Marked {count} messages as read"}

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to mark messages as read: {str(e)}"
        )


@router.get("/unread-count")
async def get_unread_count(
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get total unread message count"""
    try:
        comm_service = CommunicationService(db)

        count = comm_service.get_unread_message_count(UUID(current_user_id))

        return {"unread_count": count}

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get unread count: {str(e)}"
        )


@router.get("/search")
async def search_messages(
    q: str = Query(..., description="Search query"),
    conversation_id: Optional[UUID] = Query(
        None, description="Search within specific conversation"
    ),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Search messages"""
    try:
        comm_service = CommunicationService(db)

        messages = comm_service.search_messages(
            user_id=UUID(current_user_id), query=q, conversation_id=conversation_id
        )

        return [MessageResponse.from_orm(msg) for msg in messages]

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search messages: {str(e)}"
        )


@router.post("/conversations/trichat", response_model=ConversationResponse)
async def create_trichat_conversation(
    title: str,
    participant_ids: List[str],
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a TriChat conversation"""
    try:
        comm_service = CommunicationService(db)

        # Convert participant strings to UUIDs
        participant_uuids = [UUID(pid) for pid in participant_ids]

        conversation = comm_service.create_trichat_conversation(
            creator_id=UUID(current_user_id),
            participant_ids=participant_uuids,
            title=title,
        )

        return ConversationResponse.from_orm(conversation)

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create TriChat: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/participants/{participant_id}")
async def add_participant(
    conversation_id: UUID,
    participant_id: UUID,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add participant to conversation"""
    try:
        comm_service = CommunicationService(db)

        conversation = comm_service.add_participant_to_conversation(
            conversation_id=conversation_id,
            new_participant_id=participant_id,
            requester_id=UUID(current_user_id),
        )

        return {"message": "Participant added successfully"}

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to add participant: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}/participants/{participant_id}")
async def remove_participant(
    conversation_id: UUID,
    participant_id: UUID,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Remove participant from conversation"""
    try:
        comm_service = CommunicationService(db)

        conversation = comm_service.remove_participant_from_conversation(
            conversation_id=conversation_id,
            participant_id=participant_id,
            requester_id=UUID(current_user_id),
        )

        return {"message": "Participant removed successfully"}

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to remove participant: {str(e)}"
        )


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: UUID,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get messaging permissions for a specific user"""
    try:
        from sqlalchemy.orm import joinedload

        from app.models.sql_models import User

        current_user = db.query(User).filter(User.id == UUID(current_user_id)).first()
        target_user = (
            db.query(User)
            .options(joinedload(User.team))
            .filter(User.id == user_id)
            .first()
        )

        if not current_user or not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        can_message = can_message_user(current_user, target_user)

        return {
            "can_message": can_message,
            "reason": "Hierarchy restrictions" if not can_message else "Allowed",
            "target_user": {
                "id": str(target_user.id),
                "name": target_user.name,
                "role": target_user.role,
                "team_name": target_user.team.name if target_user.team else None,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user permissions: {str(e)}"
        )


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    title: Optional[str] = None,
    participants: Optional[List[str]] = None,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update a conversation"""
    try:
        comm_service = CommunicationService(db)

        update_data = {}
        if title is not None:
            update_data["title"] = title
        if participants is not None:
            update_data["participants"] = [UUID(pid) for pid in participants]

        conversation = comm_service.update_conversation(
            conversation_id=conversation_id,
            update_data=update_data,
            requester_id=UUID(current_user_id),
        )

        return ConversationResponse.from_orm(conversation)

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update conversation: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a conversation"""
    try:
        comm_service = CommunicationService(db)

        success = comm_service.delete_conversation(
            conversation_id=conversation_id, requester_id=UUID(current_user_id)
        )

        return {"message": "Conversation deleted successfully"}

    except ViraException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete conversation: {str(e)}"
        )
