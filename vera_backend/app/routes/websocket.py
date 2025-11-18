"""
WebSocket Routes for Real-Time Communication
Implements Socket.IO endpoints for chat, notifications, and presence
"""
import logging
from typing import Dict

import socketio
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_id_from_token
from app.database import get_db
from app.services.websocket_service import WebSocketService, connection_manager

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # Configure properly in production
    logger=True,
    engineio_logger=True,
)

# Wrap with ASGI application
socket_app = socketio.ASGIApp(
    sio,
    socketio_path="/socket.io",
)


@sio.event
async def connect(sid, environ, auth):
    """
    Handle WebSocket connection

    Client should send auth token in auth parameter:
    socket.io.connect('http://localhost:8000', {
        auth: { token: 'jwt-token-here' }
    })
    """
    try:
        if not auth or "token" not in auth:
            logger.warning(f"Connection {sid} rejected: No auth token")
            return False

        # Extract and validate JWT token
        token = auth["token"]

        try:
            # Validate token and get user_id
            user_id = await get_current_user_id_from_token(token)

            if not user_id:
                logger.warning(f"Connection {sid} rejected: Invalid token")
                return False

            # Store user_id with session
            async with sio.session(sid) as session:
                session["user_id"] = user_id

            # Register connection
            await connection_manager.connect(user_id, sid)

            # Send connection success
            await sio.emit(
                "connection_established",
                {"user_id": user_id, "status": "connected"},
                to=sid,
            )

            logger.info(f"User {user_id} connected with sid {sid}")
            return True

        except Exception as e:
            logger.error(f"Error validating token for {sid}: {e}")
            return False

    except Exception as e:
        logger.error(f"Connection error for {sid}: {e}")
        return False


@sio.event
async def disconnect(sid):
    """Handle WebSocket disconnection"""
    try:
        async with sio.session(sid) as session:
            user_id = session.get("user_id")

        if user_id:
            await connection_manager.disconnect(sid)
            logger.info(f"User {user_id} disconnected (sid: {sid})")

    except Exception as e:
        logger.error(f"Disconnect error for {sid}: {e}")


@sio.event
async def join_conversation(sid, data: Dict):
    """
    Join a conversation room

    Payload: { conversation_id: "uuid" }
    """
    try:
        async with sio.session(sid) as session:
            user_id = session.get("user_id")

        if not user_id:
            return {"error": "Not authenticated"}

        conversation_id = data.get("conversation_id")
        if not conversation_id:
            return {"error": "conversation_id required"}

        # Join Socket.IO room
        await sio.enter_room(sid, f"conversation:{conversation_id}")

        # Register in connection manager
        await connection_manager.join_conversation(user_id, conversation_id)

        # Get current state
        typing_users = connection_manager.get_typing_users(conversation_id)

        return {
            "status": "joined",
            "conversation_id": conversation_id,
            "typing_users": typing_users,
        }

    except Exception as e:
        logger.error(f"Error joining conversation: {e}")
        return {"error": str(e)}


@sio.event
async def leave_conversation(sid, data: Dict):
    """
    Leave a conversation room

    Payload: { conversation_id: "uuid" }
    """
    try:
        async with sio.session(sid) as session:
            user_id = session.get("user_id")

        if not user_id:
            return {"error": "Not authenticated"}

        conversation_id = data.get("conversation_id")
        if not conversation_id:
            return {"error": "conversation_id required"}

        # Leave Socket.IO room
        await sio.leave_room(sid, f"conversation:{conversation_id}")

        # Unregister from connection manager
        await connection_manager.leave_conversation(user_id, conversation_id)

        return {"status": "left", "conversation_id": conversation_id}

    except Exception as e:
        logger.error(f"Error leaving conversation: {e}")
        return {"error": str(e)}


@sio.event
async def typing_start(sid, data: Dict):
    """
    Indicate typing started

    Payload: { conversation_id: "uuid" }
    """
    try:
        async with sio.session(sid) as session:
            user_id = session.get("user_id")

        if not user_id:
            return {"error": "Not authenticated"}

        conversation_id = data.get("conversation_id")
        if not conversation_id:
            return {"error": "conversation_id required"}

        await connection_manager.start_typing(user_id, conversation_id)

        return {"status": "typing"}

    except Exception as e:
        logger.error(f"Error in typing_start: {e}")
        return {"error": str(e)}


@sio.event
async def typing_stop(sid, data: Dict):
    """
    Indicate typing stopped

    Payload: { conversation_id: "uuid" }
    """
    try:
        async with sio.session(sid) as session:
            user_id = session.get("user_id")

        if not user_id:
            return {"error": "Not authenticated"}

        conversation_id = data.get("conversation_id")
        if not conversation_id:
            return {"error": "conversation_id required"}

        await connection_manager.stop_typing(user_id, conversation_id)

        return {"status": "stopped"}

    except Exception as e:
        logger.error(f"Error in typing_stop: {e}")
        return {"error": str(e)}


@sio.event
async def mark_read(sid, data: Dict):
    """
    Mark message as read

    Payload: { conversation_id: "uuid", message_id: "uuid" }
    """
    try:
        async with sio.session(sid) as session:
            user_id = session.get("user_id")

        if not user_id:
            return {"error": "Not authenticated"}

        conversation_id = data.get("conversation_id")
        message_id = data.get("message_id")

        if not conversation_id or not message_id:
            return {"error": "conversation_id and message_id required"}

        # Broadcast read receipt
        await connection_manager.broadcast_message_read(
            conversation_id, message_id, user_id
        )

        return {"status": "marked_read"}

    except Exception as e:
        logger.error(f"Error in mark_read: {e}")
        return {"error": str(e)}


@sio.event
async def get_online_users(sid, data: Dict):
    """
    Get online status for users

    Payload: { user_ids: ["uuid1", "uuid2", ...] }
    """
    try:
        user_ids = data.get("user_ids", [])
        online_users = connection_manager.get_online_users(user_ids)

        return {"online_users": online_users}

    except Exception as e:
        logger.error(f"Error getting online users: {e}")
        return {"error": str(e)}


# Helper function to emit events from other parts of the application
async def emit_to_user(user_id: str, event: str, data: Dict):
    """Emit event to all connections of a user"""
    if user_id in connection_manager.active_connections:
        for sid in connection_manager.active_connections[user_id]:
            await sio.emit(event, data, to=sid)


async def emit_to_conversation(conversation_id: str, event: str, data: Dict):
    """Emit event to all participants in a conversation"""
    await sio.emit(event, data, room=f"conversation:{conversation_id}")


# Monkey-patch connection_manager.send_to_user to use Socket.IO
async def send_to_user_impl(user_id: str, message: Dict):
    """Implementation of send_to_user using Socket.IO"""
    await emit_to_user(user_id, message["type"], message)


connection_manager.send_to_user = send_to_user_impl
