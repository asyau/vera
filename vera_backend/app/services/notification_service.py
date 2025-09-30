"""
Notification Service for multi-channel notification delivery
"""
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ExternalServiceError, ValidationError
from app.models.sql_models import User
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


class NotificationChannel(Enum):
    """Supported notification channels"""

    IN_APP = "in_app"
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    PUSH = "push"


class NotificationPriority(Enum):
    """Notification priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationService(BaseService):
    """Service for managing multi-channel notifications"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.user_repository = UserRepository(db)

    async def send_notification(
        self,
        recipient_id: UUID,
        title: str,
        content: str,
        notification_type: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        channels: Optional[List[NotificationChannel]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send notification through specified channels"""

        # Get recipient user
        recipient = self.user_repository.get_or_raise(recipient_id)

        # Determine channels based on user preferences and notification type
        if not channels:
            channels = self._determine_channels(recipient, notification_type, priority)

        # Send through each channel
        delivery_results = {}

        for channel in channels:
            try:
                result = await self._send_through_channel(
                    channel, recipient, title, content, notification_type, metadata
                )
                delivery_results[channel.value] = {"success": True, "result": result}
            except Exception as e:
                delivery_results[channel.value] = {"success": False, "error": str(e)}

        # Store notification record
        notification_record = {
            "id": str(uuid4()),
            "recipient_id": str(recipient_id),
            "title": title,
            "content": content,
            "type": notification_type,
            "priority": priority.value,
            "channels": [c.value for c in channels],
            "delivery_results": delivery_results,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        # TODO: Store in notification history table

        return notification_record

    async def send_task_notification(
        self,
        recipient_id: UUID,
        task_title: str,
        task_id: UUID,
        notification_type: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send task-related notification"""

        notification_templates = {
            "task_assigned": {
                "title": f"New Task Assigned: {task_title}",
                "content": f"You have been assigned a new task: {task_title}. Please review and update the status accordingly.",
            },
            "task_due_soon": {
                "title": f"Task Due Soon: {task_title}",
                "content": f'Task "{task_title}" is due soon. Please ensure it\'s completed on time.',
            },
            "task_overdue": {
                "title": f"Overdue Task: {task_title}",
                "content": f'Task "{task_title}" is now overdue. Please update the status or extend the deadline.',
            },
            "task_completed": {
                "title": f"Task Completed: {task_title}",
                "content": f'Task "{task_title}" has been marked as completed.',
            },
        }

        template = notification_templates.get(notification_type)
        if not template:
            raise ValidationError(
                f"Unknown task notification type: {notification_type}"
            )

        metadata = {
            "task_id": str(task_id),
            "task_title": task_title,
            **(additional_context or {}),
        }

        return await self.send_notification(
            recipient_id=recipient_id,
            title=template["title"],
            content=template["content"],
            notification_type=notification_type,
            priority=NotificationPriority.MEDIUM,
            metadata=metadata,
        )

    async def send_message_notification(
        self,
        recipient_id: UUID,
        sender_name: str,
        conversation_title: str,
        message_preview: str,
        conversation_id: UUID,
    ) -> Dict[str, Any]:
        """Send message notification"""

        title = f"New message from {sender_name}"
        content = f"In {conversation_title}: {message_preview[:100]}..."

        metadata = {
            "conversation_id": str(conversation_id),
            "sender_name": sender_name,
            "conversation_title": conversation_title,
        }

        return await self.send_notification(
            recipient_id=recipient_id,
            title=title,
            content=content,
            notification_type="new_message",
            priority=NotificationPriority.LOW,
            metadata=metadata,
        )

    async def send_daily_briefing_notification(
        self, recipient_id: UUID, summary_content: str
    ) -> Dict[str, Any]:
        """Send daily briefing notification"""

        return await self.send_notification(
            recipient_id=recipient_id,
            title="Your Daily Briefing is Ready",
            content=summary_content[:200] + "..."
            if len(summary_content) > 200
            else summary_content,
            notification_type="daily_briefing",
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
        )

    async def send_team_notification(
        self,
        team_id: UUID,
        title: str,
        content: str,
        notification_type: str,
        exclude_user_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Send notification to all team members"""

        # Get team members
        team_members = self.user_repository.get_by_team(str(team_id))

        # Filter out excluded user
        if exclude_user_id:
            team_members = [m for m in team_members if m.id != exclude_user_id]

        # Send to each team member
        results = []
        for member in team_members:
            result = await self.send_notification(
                recipient_id=member.id,
                title=title,
                content=content,
                notification_type=notification_type,
            )
            results.append(result)

        return results

    def get_notification_preferences(self, user_id: UUID) -> Dict[str, Any]:
        """Get user's notification preferences"""

        user = self.user_repository.get_or_raise(user_id)

        # Default preferences if none set
        default_preferences = {
            "channels": {
                "in_app": True,
                "email": True,
                "slack": False,
                "teams": False,
                "push": True,
            },
            "notification_types": {
                "task_assigned": ["in_app", "email"],
                "task_due_soon": ["in_app", "push"],
                "task_overdue": ["in_app", "email", "push"],
                "new_message": ["in_app", "push"],
                "daily_briefing": ["in_app", "email"],
                "team_updates": ["in_app"],
            },
            "quiet_hours": {
                "enabled": False,
                "start_time": "22:00",
                "end_time": "08:00",
            },
        }

        return user.notification_preferences or default_preferences

    def update_notification_preferences(
        self, user_id: UUID, preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user's notification preferences"""

        # Validate preferences structure
        self._validate_preferences(preferences)

        # Update user preferences
        self.user_repository.update(
            user_id,
            {"notification_preferences": preferences, "updated_at": datetime.utcnow()},
        )

        return preferences

    def _determine_channels(
        self, recipient: User, notification_type: str, priority: NotificationPriority
    ) -> List[NotificationChannel]:
        """Determine which channels to use based on user preferences and notification type"""

        preferences = self.get_notification_preferences(recipient.id)

        # Get channels for this notification type
        type_channels = preferences.get("notification_types", {}).get(
            notification_type, ["in_app"]
        )

        # Convert to enum values
        channels = []
        for channel_name in type_channels:
            try:
                channel = NotificationChannel(channel_name)
                # Check if channel is enabled in user preferences
                if preferences.get("channels", {}).get(channel_name, False):
                    channels.append(channel)
            except ValueError:
                continue

        # Always include in-app for high priority notifications
        if (
            priority == NotificationPriority.URGENT
            and NotificationChannel.IN_APP not in channels
        ):
            channels.append(NotificationChannel.IN_APP)

        return channels or [NotificationChannel.IN_APP]

    async def _send_through_channel(
        self,
        channel: NotificationChannel,
        recipient: User,
        title: str,
        content: str,
        notification_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send notification through specific channel"""

        if channel == NotificationChannel.IN_APP:
            return await self._send_in_app_notification(
                recipient, title, content, metadata
            )
        elif channel == NotificationChannel.EMAIL:
            return await self._send_email_notification(
                recipient, title, content, metadata
            )
        elif channel == NotificationChannel.SLACK:
            return await self._send_slack_notification(
                recipient, title, content, metadata
            )
        elif channel == NotificationChannel.TEAMS:
            return await self._send_teams_notification(
                recipient, title, content, metadata
            )
        elif channel == NotificationChannel.PUSH:
            return await self._send_push_notification(
                recipient, title, content, metadata
            )
        else:
            raise ValidationError(f"Unsupported notification channel: {channel}")

    async def _send_in_app_notification(
        self,
        recipient: User,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send in-app notification"""

        # TODO: Implement WebSocket real-time notification
        # For now, store in database for retrieval

        return {
            "channel": "in_app",
            "status": "queued",
            "recipient_id": str(recipient.id),
        }

    async def _send_email_notification(
        self,
        recipient: User,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send email notification"""

        # TODO: Implement email service integration
        # This would integrate with services like SendGrid, AWS SES, etc.

        return {
            "channel": "email",
            "status": "sent",
            "recipient_email": recipient.email,
        }

    async def _send_slack_notification(
        self,
        recipient: User,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send Slack notification"""

        # TODO: Implement Slack API integration
        if not settings.slack_api_token:
            raise ExternalServiceError("Slack API token not configured")

        return {"channel": "slack", "status": "sent"}

    async def _send_teams_notification(
        self,
        recipient: User,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send Microsoft Teams notification"""

        # TODO: Implement Teams API integration
        if not settings.teams_api_token:
            raise ExternalServiceError("Teams API token not configured")

        return {"channel": "teams", "status": "sent"}

    async def _send_push_notification(
        self,
        recipient: User,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send push notification"""

        # TODO: Implement push notification service
        # This would integrate with Firebase Cloud Messaging or similar

        return {"channel": "push", "status": "sent"}

    def _validate_preferences(self, preferences: Dict[str, Any]) -> None:
        """Validate notification preferences structure"""

        required_keys = ["channels", "notification_types"]
        for key in required_keys:
            if key not in preferences:
                raise ValidationError(f"Missing required preference key: {key}")

        # Validate channel names
        valid_channels = [c.value for c in NotificationChannel]
        for channel in preferences["channels"]:
            if channel not in valid_channels:
                raise ValidationError(f"Invalid channel: {channel}")

        # Validate notification type configurations
        for notification_type, channels in preferences["notification_types"].items():
            for channel in channels:
                if channel not in valid_channels:
                    raise ValidationError(
                        f"Invalid channel in {notification_type}: {channel}"
                    )
