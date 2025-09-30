import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.pydantic_models import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
)
from app.models.sql_models import Conversation, Project, Team, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(db: Session = Depends(get_db)):
    """Get all conversations."""
    try:
        conversations = (
            db.query(Conversation)
            .options(joinedload(Conversation.project), joinedload(Conversation.team))
            .all()
        )
        return ConversationListResponse(
            conversations=[
                ConversationResponse.from_orm(conversation)
                for conversation in conversations
            ],
            total=len(conversations),
        )
    except Exception as e:
        logger.error(f"Error fetching conversations: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching conversations: {str(e)}"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Get a specific conversation by ID."""
    try:
        conversation = (
            db.query(Conversation)
            .options(joinedload(Conversation.project), joinedload(Conversation.team))
            .filter(Conversation.id == uuid.UUID(conversation_id))
            .first()
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return ConversationResponse.from_orm(conversation)
    except Exception as e:
        logger.error(f"Error fetching conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching conversation: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/conversations", response_model=ConversationListResponse
)
async def get_project_conversations(project_id: str, db: Session = Depends(get_db)):
    """Get all conversations for a specific project."""
    try:
        conversations = (
            db.query(Conversation)
            .options(joinedload(Conversation.project), joinedload(Conversation.team))
            .filter(Conversation.project_id == uuid.UUID(project_id))
            .all()
        )
        return ConversationListResponse(
            conversations=[
                ConversationResponse.from_orm(conversation)
                for conversation in conversations
            ],
            total=len(conversations),
        )
    except Exception as e:
        logger.error(f"Error fetching conversations for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching conversations: {str(e)}"
        )


@router.get("/teams/{team_id}/conversations", response_model=ConversationListResponse)
async def get_team_conversations(team_id: str, db: Session = Depends(get_db)):
    """Get all conversations for a specific team."""
    try:
        conversations = (
            db.query(Conversation)
            .options(joinedload(Conversation.project), joinedload(Conversation.team))
            .filter(Conversation.team_id == uuid.UUID(team_id))
            .all()
        )
        return ConversationListResponse(
            conversations=[
                ConversationResponse.from_orm(conversation)
                for conversation in conversations
            ],
            total=len(conversations),
        )
    except Exception as e:
        logger.error(f"Error fetching conversations for team {team_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching conversations: {str(e)}"
        )


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_info: ConversationCreate, db: Session = Depends(get_db)
):
    """Create a new conversation."""
    try:
        # Verify project exists if provided
        if conversation_info.project_id:
            project = (
                db.query(Project)
                .filter(Project.id == conversation_info.project_id)
                .first()
            )
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

        # Verify team exists if provided
        if conversation_info.team_id:
            team = db.query(Team).filter(Team.id == conversation_info.team_id).first()
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")

        # Verify all participant users exist
        for participant_id in conversation_info.participant_ids:
            user = db.query(User).filter(User.id == participant_id).first()
            if not user:
                raise HTTPException(
                    status_code=404, detail=f"User with ID {participant_id} not found"
                )

        conversation = Conversation(
            id=uuid.uuid4(),
            type=conversation_info.type,
            participant_ids=conversation_info.participant_ids,
            project_id=conversation_info.project_id,
            team_id=conversation_info.team_id,
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        # Load related data for response
        conversation = (
            db.query(Conversation)
            .options(joinedload(Conversation.project), joinedload(Conversation.team))
            .filter(Conversation.id == conversation.id)
            .first()
        )

        logger.info(
            f"Created conversation: {conversation.type} with ID: {conversation.id}"
        )
        return ConversationResponse.from_orm(conversation)

    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error creating conversation: {str(e)}"
        )


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    db: Session = Depends(get_db),
):
    """Update a conversation."""
    try:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == uuid.UUID(conversation_id))
            .first()
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Update fields if provided
        if conversation_update.type is not None:
            conversation.type = conversation_update.type
        if conversation_update.participant_ids is not None:
            # Verify all participant users exist
            for participant_id in conversation_update.participant_ids:
                user = db.query(User).filter(User.id == participant_id).first()
                if not user:
                    raise HTTPException(
                        status_code=404,
                        detail=f"User with ID {participant_id} not found",
                    )
            conversation.participant_ids = conversation_update.participant_ids
        if conversation_update.project_id is not None:
            # Verify new project exists
            project = (
                db.query(Project)
                .filter(Project.id == conversation_update.project_id)
                .first()
            )
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            conversation.project_id = conversation_update.project_id
        if conversation_update.team_id is not None:
            # Verify new team exists
            team = db.query(Team).filter(Team.id == conversation_update.team_id).first()
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")
            conversation.team_id = conversation_update.team_id

        db.commit()
        db.refresh(conversation)

        # Load related data for response
        conversation = (
            db.query(Conversation)
            .options(joinedload(Conversation.project), joinedload(Conversation.team))
            .filter(Conversation.id == conversation.id)
            .first()
        )

        return ConversationResponse.from_orm(conversation)

    except Exception as e:
        logger.error(f"Error updating conversation {conversation_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error updating conversation: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Delete a conversation."""
    try:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == uuid.UUID(conversation_id))
            .first()
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        db.delete(conversation)
        db.commit()

        return {"message": "Conversation deleted successfully"}

    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error deleting conversation: {str(e)}"
        )
