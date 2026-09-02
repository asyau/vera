"""
Notification Service for multi-channel notification delivery
"""
import json
import smtplib
import requests
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
        """Send email notification via SMTP"""

        if not settings.smtp_username or not settings.smtp_password:
            # Gracefully skip if email not configured
            return {
                "channel": "email",
                "status": "skipped",
                "reason": "Email not configured",
                "recipient_email": recipient.email,
            }

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
            msg['To'] = recipient.email
            msg['Subject'] = title

            # Create HTML and plain text versions
            text_content = content
            html_content = f"""
            <html>
              <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                  <h2 style="color: #333;">{title}</h2>
                  <p>{content.replace('\n', '<br>')}</p>
                  <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                  <p style="color: #666; font-size: 12px;">
                    This is an automated notification from Vira AI.
                  </p>
                </div>
              </body>
            </html>
            """

            # Attach both versions
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()  # Enable TLS
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)

            return {
                "channel": "email",
                "status": "sent",
                "recipient_email": recipient.email,
            }

        except Exception as e:
            raise ExternalServiceError(f"Failed to send email: {str(e)}")

    async def _send_slack_notification(
        self,
        recipient: User,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send Slack notification via webhook or API"""

        # Check if Slack webhook or bot token is configured
        if not settings.slack_webhook_url and not settings.slack_bot_token:
            return {
                "channel": "slack",
                "status": "skipped",
                "reason": "Slack not configured",
            }

        try:
            # Prepare Slack message block
            slack_message = {
                "text": title,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": title,
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": content
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"📧 Recipient: {recipient.name} ({recipient.email})"
                            }
                        ]
                    }
                ]
            }

            # Use webhook if available (simpler)
            if settings.slack_webhook_url:
                response = requests.post(
                    settings.slack_webhook_url,
                    json=slack_message,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                response.raise_for_status()
                return {"channel": "slack", "status": "sent", "method": "webhook"}

            # Otherwise use Bot API
            elif settings.slack_bot_token:
                # This would require knowing the user's Slack ID or channel
                # For now, we'll skip actual implementation
                return {
                    "channel": "slack",
                    "status": "skipped",
                    "reason": "User Slack ID mapping not implemented"
                }

        except requests.RequestException as e:
            raise ExternalServiceError(f"Failed to send Slack notification: {str(e)}")

    async def _send_teams_notification(
        self,
        recipient: User,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send Microsoft Teams notification via webhook"""

        if not settings.teams_webhook_url:
            return {
                "channel": "teams",
                "status": "skipped",
                "reason": "Teams webhook not configured",
            }

        try:
            # Microsoft Teams Adaptive Card format
            teams_message = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": title,
                "themeColor": "0078D4",
                "title": title,
                "sections": [
                    {
                        "activityTitle": "Vira AI Notification",
                        "activitySubtitle": f"For: {recipient.name}",
                        "activityImage": "https://www.vira.ai/logo.png",
                        "text": content,
                        "facts": [
                            {
                                "name": "Recipient:",
                                "value": recipient.email
                            },
                            {
                                "name": "Sent:",
                                "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                            }
                        ]
                    }
                ]
            }

            response = requests.post(
                settings.teams_webhook_url,
                json=teams_message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()

            return {"channel": "teams", "status": "sent", "method": "webhook"}

        except requests.RequestException as e:
            raise ExternalServiceError(f"Failed to send Teams notification: {str(e)}")

    async def _send_push_notification(
        self,
        recipient: User,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send push notification via Firebase Cloud Messaging"""

        if not settings.fcm_server_key:
            return {
                "channel": "push",
                "status": "skipped",
                "reason": "FCM not configured",
            }

        try:
            # FCM API endpoint
            fcm_url = "https://fcm.googleapis.com/fcm/send"

            # Get user's device tokens from preferences (if stored)
            device_tokens = []
            if recipient.preferences and "device_tokens" in recipient.preferences:
                device_tokens = recipient.preferences.get("device_tokens", [])

            if not device_tokens:
                return {
                    "channel": "push",
                    "status": "skipped",
                    "reason": "No device tokens registered for user",
                }

            # Prepare FCM message
            fcm_message = {
                "notification": {
                    "title": title,
                    "body": content,
                    "icon": "vira_icon",
                    "click_action": "FLUTTER_NOTIFICATION_CLICK"
                },
                "data": metadata or {},
                "registration_ids": device_tokens
            }

            # Send to FCM
            response = requests.post(
                fcm_url,
                json=fcm_message,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"key={settings.fcm_server_key}"
                },
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            return {
                "channel": "push",
                "status": "sent",
                "success_count": result.get("success", 0),
                "failure_count": result.get("failure", 0),
            }

        except requests.RequestException as e:
            raise ExternalServiceError(f"Failed to send push notification: {str(e)}")

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
