"""
Communication Service for managing chat and messaging
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.models.sql_models import Conversation, Message, User
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


class CommunicationService(BaseService):
    """Service for managing conversations and messages"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.user_repository = UserRepository(db)

    def create_conversation(
        self,
        creator_id: UUID,
        title: str,
        conversation_type: str = "direct",
        participants: Optional[List[UUID]] = None,
    ) -> Conversation:
        """Create a new conversation"""

        # Validate conversation type
        valid_types = ["direct", "group", "trichat"]
        if conversation_type not in valid_types:
            raise ValidationError(
                f"Invalid conversation type. Must be one of: {valid_types}",
                error_code="INVALID_CONVERSATION_TYPE",
            )

        # Validate participants exist
        if participants:
            for participant_id in participants:
                self.user_repository.get_or_raise(participant_id)

        conversation_data = {
            "id": uuid4(),
            "title": title,
            "type": conversation_type,
            "creator_id": creator_id,
            "participants": participants or [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        conversation = Conversation(**conversation_data)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    def send_message(
        self,
        conversation_id: UUID,
        sender_id: UUID,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Send a message to a conversation"""

        # Verify conversation exists and user has access
        conversation = self._get_conversation_with_access_check(
            conversation_id, sender_id
        )

        # Validate message type
        valid_types = ["text", "audio", "file", "system"]
        if message_type not in valid_types:
            raise ValidationError(
                f"Invalid message type. Must be one of: {valid_types}",
                error_code="INVALID_MESSAGE_TYPE",
            )

        message_data = {
            "id": uuid4(),
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "content": content,
            "type": message_type,
            "metadata": metadata or {},
            "is_read": False,
            "timestamp": datetime.utcnow(),
        }

        message = Message(**message_data)
        self.db.add(message)

        # Update conversation's last message timestamp
        conversation.last_message_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(message)

        return message

    def get_conversation_messages(
        self,
        conversation_id: UUID,
        requester_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Message]:
        """Get messages from a conversation"""

        # Verify access to conversation
        self._get_conversation_with_access_check(conversation_id, requester_id)

        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return list(reversed(messages))  # Return in chronological order

    def get_user_conversations(
        self, user_id: UUID, conversation_type: Optional[str] = None
    ) -> List[Conversation]:
        """Get all conversations for a user"""

        query = self.db.query(Conversation).filter(
            Conversation.participants.any(user_id)
        )

        if conversation_type:
            query = query.filter(Conversation.type == conversation_type)

        return query.order_by(Conversation.last_message_at.desc()).all()

    def mark_messages_as_read(
        self,
        conversation_id: UUID,
        user_id: UUID,
        message_ids: Optional[List[UUID]] = None,
    ) -> int:
        """Mark messages as read for a user"""

        # Verify access to conversation
        self._get_conversation_with_access_check(conversation_id, user_id)

        query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.sender_id != user_id,  # Don't mark own messages as read
            Message.is_read == False,
        )

        if message_ids:
            query = query.filter(Message.id.in_(message_ids))

        updated_count = query.update({"is_read": True})
        self.db.commit()

        return updated_count

    def get_unread_message_count(self, user_id: UUID) -> int:
        """Get total unread message count for a user"""

        # Get user's conversations
        user_conversations = self.get_user_conversations(user_id)
        conversation_ids = [c.id for c in user_conversations]

        if not conversation_ids:
            return 0

        unread_count = (
            self.db.query(Message)
            .filter(
                Message.conversation_id.in_(conversation_ids),
                Message.sender_id != user_id,
                Message.is_read == False,
            )
            .count()
        )

        return unread_count

    def search_messages(
        self, user_id: UUID, query: str, conversation_id: Optional[UUID] = None
    ) -> List[Message]:
        """Search messages by content"""

        # Get user's conversations if not searching in specific conversation
        if conversation_id:
            self._get_conversation_with_access_check(conversation_id, user_id)
            conversation_filter = Message.conversation_id == conversation_id
        else:
            user_conversations = self.get_user_conversations(user_id)
            conversation_ids = [c.id for c in user_conversations]
            conversation_filter = Message.conversation_id.in_(conversation_ids)

        messages = (
            self.db.query(Message)
            .filter(conversation_filter, Message.content.ilike(f"%{query}%"))
            .order_by(Message.timestamp.desc())
            .limit(50)
            .all()
        )

        return messages

    def create_trichat_conversation(
        self, creator_id: UUID, participant_ids: List[UUID], title: str
    ) -> Conversation:
        """Create a TriChat conversation with multiple participants"""

        if len(participant_ids) < 2:
            raise ValidationError(
                "TriChat requires at least 2 participants",
                error_code="INSUFFICIENT_PARTICIPANTS",
            )

        # Include creator in participants if not already included
        all_participants = list(set([creator_id] + participant_ids))

        return self.create_conversation(
            creator_id=creator_id,
            title=title,
            conversation_type="trichat",
            participants=all_participants,
        )

    def add_participant_to_conversation(
        self, conversation_id: UUID, new_participant_id: UUID, requester_id: UUID
    ) -> Conversation:
        """Add a participant to an existing conversation"""

        conversation = self._get_conversation_with_access_check(
            conversation_id, requester_id
        )

        # Check if requester can add participants (creator or supervisor)
        requester = self.user_repository.get_or_raise(requester_id)
        if conversation.creator_id != requester_id and requester.role != "supervisor":
            raise AuthorizationError(
                "Only conversation creator or supervisor can add participants",
                error_code="INSUFFICIENT_PERMISSIONS",
            )

        # Validate new participant exists
        self.user_repository.get_or_raise(new_participant_id)

        # Add participant if not already in conversation
        if new_participant_id not in conversation.participants:
            conversation.participants.append(new_participant_id)
            conversation.updated_at = datetime.utcnow()

            # Send system message about new participant
            participant = self.user_repository.get_or_raise(new_participant_id)
            system_message_content = f"{participant.name} was added to the conversation"

            self.send_message(
                conversation_id=conversation_id,
                sender_id=requester_id,
                content=system_message_content,
                message_type="system",
            )

            self.db.commit()
            self.db.refresh(conversation)

        return conversation

    def remove_participant_from_conversation(
        self, conversation_id: UUID, participant_id: UUID, requester_id: UUID
    ) -> Conversation:
        """Remove a participant from a conversation"""

        conversation = self._get_conversation_with_access_check(
            conversation_id, requester_id
        )

        # Check permissions (creator, supervisor, or removing self)
        requester = self.user_repository.get_or_raise(requester_id)
        can_remove = (
            conversation.creator_id == requester_id
            or requester.role == "supervisor"
            or participant_id == requester_id
        )

        if not can_remove:
            raise AuthorizationError(
                "Insufficient permissions to remove participant",
                error_code="INSUFFICIENT_PERMISSIONS",
            )

        # Remove participant
        if participant_id in conversation.participants:
            conversation.participants.remove(participant_id)
            conversation.updated_at = datetime.utcnow()

            # Send system message about participant removal
            participant = self.user_repository.get_or_raise(participant_id)
            system_message_content = f"{participant.name} left the conversation"

            self.send_message(
                conversation_id=conversation_id,
                sender_id=requester_id,
                content=system_message_content,
                message_type="system",
            )

            self.db.commit()
            self.db.refresh(conversation)

        return conversation

    def _get_conversation_with_access_check(
        self, conversation_id: UUID, user_id: UUID
    ) -> Conversation:
        """Get conversation and verify user has access"""

        conversation = (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if not conversation:
            raise NotFoundError(
                "Conversation not found", error_code="CONVERSATION_NOT_FOUND"
            )

        # Check if user is a participant
        if user_id not in conversation.participants:
            raise AuthorizationError(
                "You don't have access to this conversation",
                error_code="CONVERSATION_ACCESS_DENIED",
            )

        return conversation

    def update_conversation(
        self, conversation_id: UUID, update_data: Dict[str, Any], requester_id: UUID
    ) -> Conversation:
        """Update a conversation"""
        conversation = self._get_conversation_with_access_check(
            conversation_id, requester_id
        )

        # Update fields
        for key, value in update_data.items():
            if hasattr(conversation, key):
                setattr(conversation, key, value)

        conversation.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def delete_conversation(self, conversation_id: UUID, requester_id: UUID) -> bool:
        """Delete a conversation"""
        conversation = self._get_conversation_with_access_check(
            conversation_id, requester_id
        )

        self.db.delete(conversation)
        self.db.commit()
        return True
