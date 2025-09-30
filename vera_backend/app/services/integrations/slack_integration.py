"""
Slack Integration Service
Comprehensive Slack integration as specified in RFC Section 13.1
"""

import asyncio
import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.oauth import AuthorizeUrlGenerator, OAuthStateUtils
from slack_sdk.signature import SignatureVerifier
from slack_sdk.webhook import WebhookClient

from app.core.config import settings
from app.models.sql_models import Company, Message, Task, User
from app.services.langchain_orchestrator import LangChainOrchestrator

from .base_integration import BaseIntegrationService, IntegrationStatus, IntegrationType


class SlackIntegrationService(BaseIntegrationService):
    """
    Slack Integration Service implementing RFC Section 13.1 requirements:
    - OAuth authentication and bot installation
    - Message ingestion from channels and DMs
    - Task extraction from @Vira mentions
    - Inline replies and notifications
    - Webhook handling for real-time events
    """

    def __init__(self, db):
        super().__init__(db)
        self.client_id = getattr(settings, "slack_client_id", None)
        self.client_secret = getattr(settings, "slack_client_secret", None)
        self.signing_secret = getattr(settings, "slack_signing_secret", None)

        # Slack OAuth scopes required for Vira functionality
        self.required_scopes = [
            "channels:read",
            "channels:history",
            "groups:read",
            "groups:history",
            "im:read",
            "im:history",
            "chat:write",
            "chat:write.public",
            "users:read",
            "users:read.email",
            "team:read",
            "commands",
            "files:read",
            "reactions:read",
        ]

        # Initialize signature verifier
        if self.signing_secret:
            self.signature_verifier = SignatureVerifier(self.signing_secret)

    def _get_integration_type(self) -> IntegrationType:
        return IntegrationType.SLACK

    def get_authorization_url(
        self, company_id: uuid.UUID, user_id: uuid.UUID, redirect_uri: str, **kwargs
    ) -> str:
        """Generate Slack OAuth authorization URL"""
        if not self.client_id:
            raise ValueError("Slack client ID not configured")

        # Generate state parameter for security
        state = OAuthStateUtils.generate(
            expires_in=600,  # 10 minutes
            user_id=str(user_id),
            company_id=str(company_id),
        )

        # Create authorization URL generator
        auth_url_generator = AuthorizeUrlGenerator(
            client_id=self.client_id,
            scopes=self.required_scopes,
            redirect_uri=redirect_uri,
        )

        return auth_url_generator.generate(state=state)

    def handle_oauth_callback(self, code: str, state: str, **kwargs) -> Dict[str, Any]:
        """Handle Slack OAuth callback and store credentials"""
        try:
            # Validate state parameter
            state_data = OAuthStateUtils.parse(state)
            user_id = uuid.UUID(state_data["user_id"])
            company_id = uuid.UUID(state_data["company_id"])

            # Exchange code for access token
            client = WebClient()
            response = client.oauth_v2_access(
                client_id=self.client_id, client_secret=self.client_secret, code=code
            )

            if not response.get("ok"):
                raise SlackApiError("OAuth exchange failed", response)

            # Extract credentials and team info
            credentials = {
                "access_token": response["access_token"],
                "bot_user_id": response.get("bot_user_id"),
                "team": response.get("team", {}),
                "enterprise": response.get("enterprise"),
                "is_enterprise_install": response.get("is_enterprise_install", False),
                "scope": response.get("scope"),
                "token_type": response.get("token_type"),
                "expires_at": None,  # Slack tokens don't expire unless revoked
            }

            # Create integration record
            config = {
                "team_id": response["team"]["id"],
                "team_name": response["team"]["name"],
                "bot_user_id": response.get("bot_user_id"),
                "webhook_url": None,  # Will be set up later if needed
                "channels": [],  # Will be populated during sync
                "last_sync": None,
                "sync_settings": {
                    "sync_public_channels": True,
                    "sync_private_channels": False,
                    "sync_dms": True,
                    "extract_tasks": True,
                    "auto_reply": True,
                },
            }

            integration = self.create_integration(company_id, user_id, config)

            # Store credentials
            self.store_credentials(integration.id, credentials)

            # Test the connection
            test_result = self.test_connection(integration.id)
            if test_result["success"]:
                self.update_integration_status(
                    integration.id, IntegrationStatus.CONNECTED
                )

                # Start initial sync
                asyncio.create_task(self._async_initial_sync(integration.id))

            self.log_integration_event(
                integration.id,
                "oauth_completed",
                {
                    "team_id": credentials["team"]["id"],
                    "team_name": credentials["team"]["name"],
                },
            )

            return self.format_success_response(
                {
                    "integration_id": str(integration.id),
                    "team_name": credentials["team"]["name"],
                    "status": "connected",
                }
            )

        except Exception as e:
            return self.format_error_response(e, "oauth_callback")

    def test_connection(self, integration_id: uuid.UUID) -> Dict[str, Any]:
        """Test Slack connection"""
        try:
            credentials = self.get_credentials(integration_id)
            if not credentials:
                return self.format_error_response(
                    Exception("No credentials found"), "test_connection"
                )

            client = WebClient(token=credentials["access_token"])

            # Test auth
            auth_response = client.auth_test()
            if not auth_response.get("ok"):
                return self.format_error_response(
                    Exception("Auth test failed"), "test_connection"
                )

            # Test basic API access
            team_info = client.team_info()
            if not team_info.get("ok"):
                return self.format_error_response(
                    Exception("Team info access failed"), "test_connection"
                )

            return self.format_success_response(
                {
                    "user_id": auth_response.get("user_id"),
                    "team": auth_response.get("team"),
                    "url": auth_response.get("url"),
                }
            )

        except SlackApiError as e:
            return self.format_error_response(e, "test_connection")
        except Exception as e:
            return self.format_error_response(e, "test_connection")

    def refresh_credentials(self, integration_id: uuid.UUID) -> bool:
        """Slack tokens don't expire, but we can re-validate them"""
        test_result = self.test_connection(integration_id)
        if test_result["success"]:
            self.update_integration_status(integration_id, IntegrationStatus.CONNECTED)
            return True
        else:
            self.update_integration_status(
                integration_id,
                IntegrationStatus.ERROR,
                test_result.get("error", {}).get("message"),
            )
            return False

    def disconnect(self, integration_id: uuid.UUID) -> bool:
        """Disconnect Slack integration"""
        try:
            credentials = self.get_credentials(integration_id)
            if credentials:
                # Revoke the token
                client = WebClient(token=credentials["access_token"])
                try:
                    client.auth_revoke()
                except SlackApiError:
                    pass  # Token might already be revoked

            # Update status
            self.update_integration_status(
                integration_id, IntegrationStatus.DISCONNECTED
            )

            # Clear credentials
            self.update_integration_config(
                integration_id,
                {"credentials": {}, "status": IntegrationStatus.DISCONNECTED.value},
            )

            self.log_integration_event(integration_id, "disconnected")
            return True

        except Exception as e:
            self.log_integration_event(
                integration_id, "disconnect_error", {"error": str(e)}
            )
            return False

    def sync_data(
        self, integration_id: uuid.UUID, sync_type: str = "full"
    ) -> Dict[str, Any]:
        """Sync data from Slack"""
        try:
            credentials = self.get_credentials(integration_id)
            if not credentials:
                return self.format_error_response(
                    Exception("No credentials"), "sync_data"
                )

            client = WebClient(token=credentials["access_token"])
            integration = self.get_integration(integration_id)

            sync_results = {
                "channels_synced": 0,
                "messages_processed": 0,
                "tasks_extracted": 0,
                "errors": [],
            }

            # Get channels
            channels_response = client.conversations_list(
                types="public_channel,private_channel,im", exclude_archived=True
            )

            if not channels_response.get("ok"):
                return self.format_error_response(
                    Exception("Failed to fetch channels"), "sync_data"
                )

            channels = channels_response["channels"]
            sync_settings = integration.config.get("sync_settings", {})

            # Process each channel
            for channel in channels:
                channel_type = channel["type"]

                # Check if we should sync this channel type
                if channel_type == "public_channel" and not sync_settings.get(
                    "sync_public_channels", True
                ):
                    continue
                if channel_type == "private_channel" and not sync_settings.get(
                    "sync_private_channels", False
                ):
                    continue
                if channel_type == "im" and not sync_settings.get("sync_dms", True):
                    continue

                try:
                    # Get channel history
                    history_response = client.conversations_history(
                        channel=channel["id"], limit=100  # Adjust based on needs
                    )

                    if history_response.get("ok"):
                        messages = history_response["messages"]
                        sync_results["channels_synced"] += 1

                        # Process messages
                        for message in messages:
                            processed = self._process_slack_message(
                                integration_id, client, channel, message
                            )
                            if processed:
                                sync_results["messages_processed"] += 1
                                if processed.get("task_extracted"):
                                    sync_results["tasks_extracted"] += 1

                except SlackApiError as e:
                    sync_results["errors"].append(f"Channel {channel['id']}: {str(e)}")

            # Update last sync time
            self.update_integration_config(
                integration_id, {"last_sync": datetime.utcnow().isoformat()}
            )

            self.log_integration_event(integration_id, "sync_completed", sync_results)

            return self.format_success_response(sync_results)

        except Exception as e:
            return self.format_error_response(e, "sync_data")

    def handle_webhook(
        self,
        integration_id: uuid.UUID,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Handle Slack webhook events"""
        try:
            # Verify webhook signature
            body = json.dumps(payload).encode()
            timestamp = headers.get("X-Slack-Request-Timestamp", "")
            signature = headers.get("X-Slack-Signature", "")

            if not self.signature_verifier.is_valid(body, timestamp, signature):
                return self.format_error_response(
                    Exception("Invalid signature"), "webhook"
                )

            # Handle URL verification challenge
            if payload.get("type") == "url_verification":
                return {"challenge": payload.get("challenge")}

            # Handle events
            event = payload.get("event", {})
            event_type = event.get("type")

            if event_type == "message":
                return self._handle_message_event(integration_id, event, payload)
            elif event_type == "member_joined_channel":
                return self._handle_member_joined_event(integration_id, event)
            elif event_type == "app_mention":
                return self._handle_app_mention_event(integration_id, event)

            self.log_integration_event(
                integration_id,
                "webhook_received",
                {"event_type": event_type, "team_id": payload.get("team_id")},
            )

            return self.format_success_response({"processed": True})

        except Exception as e:
            return self.format_error_response(e, "webhook")

    # Private helper methods

    async def _async_initial_sync(self, integration_id: uuid.UUID):
        """Perform initial sync asynchronously"""
        await asyncio.sleep(1)  # Small delay to ensure transaction is committed
        self.sync_data(integration_id, "initial")

    def _process_slack_message(
        self, integration_id: uuid.UUID, client: WebClient, channel: Dict, message: Dict
    ) -> Optional[Dict[str, Any]]:
        """Process a single Slack message"""
        try:
            # Skip bot messages and system messages
            if message.get("bot_id") or message.get("subtype"):
                return None

            text = message.get("text", "")
            user_id = message.get("user")

            if not text or not user_id:
                return None

            # Check if message mentions Vira bot
            integration = self.get_integration(integration_id)
            bot_user_id = integration.config.get("bot_user_id")

            mentions_vira = (
                f"<@{bot_user_id}>" in text if bot_user_id else "@vira" in text.lower()
            )

            result = {"processed": True, "task_extracted": False}

            # Extract tasks if Vira is mentioned and task extraction is enabled
            if mentions_vira and integration.config.get("sync_settings", {}).get(
                "extract_tasks", True
            ):
                task_result = self._extract_task_from_message(
                    integration_id, text, user_id, channel
                )
                if task_result:
                    result["task_extracted"] = True

                    # Send confirmation reply if auto-reply is enabled
                    if integration.config.get("sync_settings", {}).get(
                        "auto_reply", True
                    ):
                        self._send_slack_reply(
                            integration_id,
                            channel["id"],
                            f"✅ Task created: {task_result['title']}",
                            message.get("ts"),
                        )

            return result

        except Exception as e:
            self.log_integration_event(
                integration_id, "message_processing_error", {"error": str(e)}
            )
            return None

    def _extract_task_from_message(
        self, integration_id: uuid.UUID, text: str, user_id: str, channel: Dict
    ) -> Optional[Dict[str, Any]]:
        """Extract task from Slack message using LangChain orchestrator"""
        try:
            # Get integration and company info
            integration = self.get_integration(integration_id)
            company_id = integration.company_id

            # Find Vira user in the company (for task creation)
            vira_user = (
                self.db.query(User)
                .filter(
                    User.company_id == company_id,
                    User.role.in_(["CEO", "PM", "Supervisor"]),
                )
                .first()
            )

            if not vira_user:
                return None

            # Use LangChain orchestrator to extract task
            orchestrator = LangChainOrchestrator(self.db)

            context = {
                "source": "slack",
                "channel": channel.get("name", "unknown"),
                "slack_user_id": user_id,
                "integration_id": str(integration_id),
            }

            # Process with orchestrator
            result = orchestrator._handle_task_management(
                user_input=text, user_id=vira_user.id, context=context
            )

            if result and "task created" in result.lower():
                return {
                    "title": text[:100],  # Truncate for title
                    "description": text,
                    "source": "slack",
                }

            return None

        except Exception as e:
            self.log_integration_event(
                integration_id, "task_extraction_error", {"error": str(e)}
            )
            return None

    def _send_slack_reply(
        self, integration_id: uuid.UUID, channel: str, text: str, thread_ts: str = None
    ):
        """Send a reply to Slack channel"""
        try:
            credentials = self.get_credentials(integration_id)
            if not credentials:
                return

            client = WebClient(token=credentials["access_token"])

            client.chat_postMessage(channel=channel, text=text, thread_ts=thread_ts)

        except Exception as e:
            self.log_integration_event(integration_id, "reply_error", {"error": str(e)})

    def _handle_message_event(
        self, integration_id: uuid.UUID, event: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Slack message events"""
        try:
            credentials = self.get_credentials(integration_id)
            client = WebClient(token=credentials["access_token"])

            # Get channel info
            channel_id = event.get("channel")
            channel_info = client.conversations_info(channel=channel_id)

            if channel_info.get("ok"):
                channel = channel_info["channel"]
                self._process_slack_message(integration_id, client, channel, event)

            return self.format_success_response({"processed": True})

        except Exception as e:
            return self.format_error_response(e, "message_event")

    def _handle_member_joined_event(
        self, integration_id: uuid.UUID, event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle member joined channel events"""
        try:
            # Send welcome message as specified in RFC
            user_id = event.get("user")
            channel_id = event.get("channel")

            if user_id and channel_id:
                welcome_msg = "Welcome! Thanks for joining. I'm Vira, your AI assistant. Mention me with @vira to get help with tasks and questions."
                self._send_slack_reply(integration_id, user_id, welcome_msg)  # Send DM

            return self.format_success_response({"processed": True})

        except Exception as e:
            return self.format_error_response(e, "member_joined_event")

    def _handle_app_mention_event(
        self, integration_id: uuid.UUID, event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle app mention events"""
        try:
            text = event.get("text", "")
            channel = event.get("channel")
            user = event.get("user")
            ts = event.get("ts")

            # Process the mention for task extraction or general query
            credentials = self.get_credentials(integration_id)
            client = WebClient(token=credentials["access_token"])

            # Get channel info
            channel_info = client.conversations_info(channel=channel)
            if channel_info.get("ok"):
                channel_data = channel_info["channel"]
                self._process_slack_message(integration_id, client, channel_data, event)

            return self.format_success_response({"processed": True})

        except Exception as e:
            return self.format_error_response(e, "app_mention_event")

    # Public API methods for sending notifications

    def send_notification(
        self, integration_id: uuid.UUID, channel: str, message: str, **kwargs
    ) -> Dict[str, Any]:
        """Send notification to Slack channel"""
        try:
            credentials = self.get_credentials(integration_id)
            if not credentials:
                return self.format_error_response(
                    Exception("No credentials"), "send_notification"
                )

            client = WebClient(token=credentials["access_token"])

            response = client.chat_postMessage(channel=channel, text=message, **kwargs)

            if response.get("ok"):
                return self.format_success_response(
                    {
                        "message_ts": response.get("ts"),
                        "channel": response.get("channel"),
                    }
                )
            else:
                return self.format_error_response(
                    Exception("Failed to send message"), "send_notification"
                )

        except Exception as e:
            return self.format_error_response(e, "send_notification")

    def get_channels(self, integration_id: uuid.UUID) -> Dict[str, Any]:
        """Get list of Slack channels"""
        try:
            credentials = self.get_credentials(integration_id)
            if not credentials:
                return self.format_error_response(
                    Exception("No credentials"), "get_channels"
                )

            client = WebClient(token=credentials["access_token"])

            response = client.conversations_list(
                types="public_channel,private_channel", exclude_archived=True
            )

            if response.get("ok"):
                channels = [
                    {
                        "id": ch["id"],
                        "name": ch["name"],
                        "type": ch.get("type", "channel"),
                        "is_private": ch.get("is_private", False),
                        "member_count": ch.get("num_members", 0),
                    }
                    for ch in response["channels"]
                ]

                return self.format_success_response(channels)
            else:
                return self.format_error_response(
                    Exception("Failed to fetch channels"), "get_channels"
                )

        except Exception as e:
            return self.format_error_response(e, "get_channels")
