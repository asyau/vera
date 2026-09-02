"""
WebSocket Service for Real-Time Communication
Handles real-time messaging, notifications, and presence
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ViraException
from app.models.sql_models import Message, User
from app.services.base import BaseService

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """
    Manages WebSocket connections for users
    Handles connection lifecycle, room management, and message broadcasting
    """

    def __init__(self):
        # Map: user_id -> set of connection IDs
        self.active_connections: Dict[str, Set[str]] = {}

        # Map: connection_id -> user_id
        self.connection_users: Dict[str, str] = {}

        # Map: conversation_id -> set of user_ids
        self.conversation_rooms: Dict[str, Set[str]] = {}

        # Map: user_id -> last_seen timestamp
        self.user_presence: Dict[str, datetime] = {}

        # Map: conversation_id -> set of typing user_ids
        self.typing_indicators: Dict[str, Set[str]] = {}

    async def connect(self, user_id: str, connection_id: str):
        """Register a new WebSocket connection for a user"""
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(connection_id)
        self.connection_users[connection_id] = user_id
        self.user_presence[user_id] = datetime.utcnow()

        logger.info(f"User {user_id} connected with connection {connection_id}")

        # Notify others about user coming online
        await self.broadcast_presence_update(user_id, "online")

    async def disconnect(self, connection_id: str):
        """Unregister a WebSocket connection"""
        if connection_id not in self.connection_users:
            return

        user_id = self.connection_users[connection_id]

        # Remove connection
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(connection_id)

            # If user has no more connections, mark as offline
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                self.user_presence[user_id] = datetime.utcnow()
                await self.broadcast_presence_update(user_id, "offline")

        del self.connection_users[connection_id]

        logger.info(f"Connection {connection_id} disconnected for user {user_id}")

    def is_user_online(self, user_id: str) -> bool:
        """Check if a user is currently online"""
        return user_id in self.active_connections

    def get_online_users(self, user_ids: List[str]) -> List[str]:
        """Get list of online users from a given list"""
        return [uid for uid in user_ids if self.is_user_online(uid)]

    async def join_conversation(self, user_id: str, conversation_id: str):
        """Add user to a conversation room"""
        if conversation_id not in self.conversation_rooms:
            self.conversation_rooms[conversation_id] = set()

        self.conversation_rooms[conversation_id].add(user_id)
        logger.info(f"User {user_id} joined conversation {conversation_id}")

    async def leave_conversation(self, user_id: str, conversation_id: str):
        """Remove user from a conversation room"""
        if conversation_id in self.conversation_rooms:
            self.conversation_rooms[conversation_id].discard(user_id)

            # Clean up empty rooms
            if not self.conversation_rooms[conversation_id]:
                del self.conversation_rooms[conversation_id]

        logger.info(f"User {user_id} left conversation {conversation_id}")

    async def start_typing(self, user_id: str, conversation_id: str):
        """Indicate that a user is typing in a conversation"""
        if conversation_id not in self.typing_indicators:
            self.typing_indicators[conversation_id] = set()

        self.typing_indicators[conversation_id].add(user_id)

        # Broadcast typing indicator to conversation participants
        await self.broadcast_to_conversation(
            conversation_id,
            {
                "type": "typing_start",
                "user_id": user_id,
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            exclude_user_id=user_id,
        )

    async def stop_typing(self, user_id: str, conversation_id: str):
        """Indicate that a user stopped typing in a conversation"""
        if conversation_id in self.typing_indicators:
            self.typing_indicators[conversation_id].discard(user_id)

        # Broadcast typing stopped to conversation participants
        await self.broadcast_to_conversation(
            conversation_id,
            {
                "type": "typing_stop",
                "user_id": user_id,
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            exclude_user_id=user_id,
        )

    def get_typing_users(self, conversation_id: str) -> List[str]:
        """Get list of users currently typing in a conversation"""
        return list(self.typing_indicators.get(conversation_id, set()))

    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send a message to all connections of a specific user"""
        # This will be implemented by the actual WebSocket handler
        # (Socket.IO, FastAPI WebSocket, etc.)
        pass

    async def broadcast_to_conversation(
        self,
        conversation_id: str,
        message: Dict[str, Any],
        exclude_user_id: Optional[str] = None,
    ):
        """Broadcast a message to all participants in a conversation"""
        if conversation_id not in self.conversation_rooms:
            return

        participants = self.conversation_rooms[conversation_id]

        for user_id in participants:
            if user_id != exclude_user_id:
                await self.send_to_user(user_id, message)

    async def broadcast_presence_update(self, user_id: str, status: str):
        """Broadcast user presence update to relevant conversations"""
        # Find all conversations this user is in and notify participants
        for conversation_id, participants in self.conversation_rooms.items():
            if user_id in participants:
                await self.broadcast_to_conversation(
                    conversation_id,
                    {
                        "type": "presence_update",
                        "user_id": user_id,
                        "status": status,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    exclude_user_id=user_id,
                )

    async def broadcast_message(
        self, conversation_id: str, message: Message, sender_id: str
    ):
        """Broadcast a new message to conversation participants"""
        await self.broadcast_to_conversation(
            conversation_id,
            {
                "type": "new_message",
                "message": {
                    "id": str(message.id),
                    "conversation_id": str(message.conversation_id),
                    "sender_id": str(message.sender_id),
                    "content": message.content,
                    "message_type": message.type,
                    "timestamp": message.timestamp.isoformat(),
                    "is_read": message.is_read,
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
            exclude_user_id=sender_id,
        )

    async def broadcast_message_read(
        self, conversation_id: str, message_id: str, user_id: str
    ):
        """Broadcast message read receipt"""
        await self.broadcast_to_conversation(
            conversation_id,
            {
                "type": "message_read",
                "message_id": message_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def broadcast_notification(self, user_id: str, notification: Dict[str, Any]):
        """Send a notification to a user"""
        await self.send_to_user(
            user_id,
            {
                "type": "notification",
                "notification": notification,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


class WebSocketService(BaseService):
    """
    WebSocket service for handling real-time events
    Works with WebSocketConnectionManager to manage connections
    """

    def __init__(self, db: Session, connection_manager: WebSocketConnectionManager):
        super().__init__(db)
        self.connection_manager = connection_manager

    async def handle_connection(self, user_id: str, connection_id: str):
        """Handle new WebSocket connection"""
        try:
            await self.connection_manager.connect(user_id, connection_id)

            # Send initial connection success message
            await self.connection_manager.send_to_user(
                user_id,
                {
                    "type": "connection_established",
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Error handling connection for user {user_id}: {e}")
            raise ViraException(f"Failed to establish connection: {str(e)}")

    async def handle_disconnection(self, connection_id: str):
        """Handle WebSocket disconnection"""
        try:
            await self.connection_manager.disconnect(connection_id)
        except Exception as e:
            logger.error(f"Error handling disconnection for {connection_id}: {e}")

    async def handle_join_conversation(self, user_id: str, conversation_id: str):
        """Handle user joining a conversation"""
        try:
            await self.connection_manager.join_conversation(user_id, conversation_id)

            # Get typing users and online participants
            typing_users = self.connection_manager.get_typing_users(conversation_id)

            # Send current state to joining user
            await self.connection_manager.send_to_user(
                user_id,
                {
                    "type": "conversation_joined",
                    "conversation_id": conversation_id,
                    "typing_users": typing_users,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Error joining conversation {conversation_id}: {e}")
            raise ViraException(f"Failed to join conversation: {str(e)}")

    async def handle_leave_conversation(self, user_id: str, conversation_id: str):
        """Handle user leaving a conversation"""
        try:
            # Stop typing if user was typing
            await self.connection_manager.stop_typing(user_id, conversation_id)
            await self.connection_manager.leave_conversation(user_id, conversation_id)
        except Exception as e:
            logger.error(f"Error leaving conversation {conversation_id}: {e}")

    async def handle_typing_event(
        self, user_id: str, conversation_id: str, is_typing: bool
    ):
        """Handle typing indicator events"""
        try:
            if is_typing:
                await self.connection_manager.start_typing(user_id, conversation_id)
            else:
                await self.connection_manager.stop_typing(user_id, conversation_id)
        except Exception as e:
            logger.error(f"Error handling typing event: {e}")

    async def broadcast_new_message(
        self, conversation_id: str, message: Message, sender_id: str
    ):
        """Broadcast a new message to conversation participants"""
        try:
            # Stop typing indicator for sender
            await self.connection_manager.stop_typing(sender_id, conversation_id)

            # Broadcast message
            await self.connection_manager.broadcast_message(
                conversation_id, message, sender_id
            )
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")

    async def broadcast_message_read(
        self, conversation_id: str, message_id: str, user_id: str
    ):
        """Broadcast message read receipt"""
        try:
            await self.connection_manager.broadcast_message_read(
                conversation_id, message_id, user_id
            )
        except Exception as e:
            logger.error(f"Error broadcasting read receipt: {e}")

    async def send_notification(self, user_id: str, notification: Dict[str, Any]):
        """Send real-time notification to user"""
        try:
            await self.connection_manager.broadcast_notification(user_id, notification)
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    def get_online_status(self, user_ids: List[str]) -> Dict[str, bool]:
        """Get online status for multiple users"""
        return {
            user_id: self.connection_manager.is_user_online(user_id)
            for user_id in user_ids
        }


# Global connection manager instance
connection_manager = WebSocketConnectionManager()
