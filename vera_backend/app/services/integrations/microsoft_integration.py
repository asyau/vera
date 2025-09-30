"""
Microsoft Integration Service
Comprehensive Microsoft Teams/Outlook integration as specified in RFC Section 13.1 & 13.3
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient
from requests_oauthlib import OAuth2Session

from app.core.config import settings
from app.models.sql_models import Company, Task, User
from app.services.langchain_orchestrator import LangChainOrchestrator

from .base_integration import BaseIntegrationService, IntegrationStatus, IntegrationType


class MicrosoftIntegrationService(BaseIntegrationService):
    """
    Microsoft Integration Service implementing RFC Section 13.1 & 13.3:
    - OAuth 2.0 authentication for Microsoft Graph API
    - Microsoft Teams integration for message ingestion and bot functionality
    - Outlook integration for calendar events and email processing
    - Task extraction from Teams messages and meeting notes
    - Calendar integration for deadlines and meeting summarization
    """

    def __init__(self, db):
        super().__init__(db)
        self.client_id = getattr(settings, "microsoft_client_id", None)
        self.client_secret = getattr(settings, "microsoft_client_secret", None)
        self.tenant_id = getattr(settings, "microsoft_tenant_id", None)

        # Microsoft Graph API scopes
        self.scopes = [
            "https://graph.microsoft.com/.default",  # Application permissions
        ]

        # Delegated scopes for OAuth flow
        self.delegated_scopes = [
            "User.Read",
            "Calendars.ReadWrite",
            "Mail.Read",
            "Chat.Read",
            "Chat.ReadWrite",
            "Team.ReadBasic.All",
            "Channel.ReadBasic.All",
            "ChannelMessage.Read.All",
            "Files.Read.All",
        ]

        # Microsoft Graph endpoints
        self.authority = (
            f"https://login.microsoftonline.com/{self.tenant_id}"
            if self.tenant_id
            else "https://login.microsoftonline.com/common"
        )
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"

        # Initialize Graph client for application permissions (when available)
        self._graph_client = None

    async def _get_graph_client(
        self, integration_id: uuid.UUID
    ) -> Optional[GraphServiceClient]:
        """Get Microsoft Graph client with proper authentication"""
        try:
            if not all([self.client_id, self.client_secret, self.tenant_id]):
                return None

            # Create credential for application permissions
            credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            # Create Graph client
            client = GraphServiceClient(credentials=credential, scopes=self.scopes)
            return client

        except Exception as e:
            self.log_integration_event(
                integration_id, "graph_client_error", {"error": str(e)}
            )
            return None

    def _get_integration_type(self) -> IntegrationType:
        return (
            IntegrationType.MICROSOFT_TEAMS
        )  # Primary type, but handles both Teams and Outlook

    def get_authorization_url(
        self, company_id: uuid.UUID, user_id: uuid.UUID, redirect_uri: str, **kwargs
    ) -> str:
        """Generate Microsoft OAuth authorization URL"""
        if not self.client_id:
            raise ValueError("Microsoft client ID not configured")

        # Create OAuth session
        oauth = OAuth2Session(
            client_id=self.client_id,
            scope=self.delegated_scopes,
            redirect_uri=redirect_uri,
        )

        # Generate state parameter
        state_data = {
            "user_id": str(user_id),
            "company_id": str(company_id),
            "timestamp": datetime.utcnow().isoformat(),
        }
        state = json.dumps(state_data)

        # Create temporary integration to store flow state
        config = {
            "oauth_state": "pending",
            "redirect_uri": redirect_uri,
            "state_data": state_data,
        }

        integration = self.create_integration(company_id, user_id, config)
        state_data["integration_id"] = str(integration.id)

        # Update state with integration ID
        updated_state = json.dumps(state_data)
        self.update_integration_config(integration.id, {"state_data": state_data})

        authorization_url, state = oauth.authorization_url(
            f"{self.authority}/oauth2/v2.0/authorize", state=updated_state
        )

        return authorization_url

    def handle_oauth_callback(self, code: str, state: str, **kwargs) -> Dict[str, Any]:
        """Handle Microsoft OAuth callback"""
        try:
            # Parse state
            state_data = json.loads(state)
            integration_id = uuid.UUID(state_data.get("integration_id"))

            integration = self.get_integration(integration_id)
            if not integration:
                return self.format_error_response(
                    ValueError("Integration not found"), "oauth_callback"
                )

            redirect_uri = integration.config.get("redirect_uri")

            # Exchange code for token
            token_url = f"{self.authority}/oauth2/v2.0/token"
            token_data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "scope": " ".join(self.delegated_scopes),
            }

            token_response = requests.post(token_url, data=token_data)
            token_response.raise_for_status()

            token_info = token_response.json()

            # Get user info
            headers = {
                "Authorization": f"Bearer {token_info['access_token']}",
                "Content-Type": "application/json",
            }

            user_response = requests.get(f"{self.graph_endpoint}/me", headers=headers)
            user_response.raise_for_status()
            user_info = user_response.json()

            # Store credentials
            credentials_data = {
                "access_token": token_info["access_token"],
                "refresh_token": token_info.get("refresh_token"),
                "token_type": token_info.get("token_type", "Bearer"),
                "expires_in": token_info.get("expires_in"),
                "expires_at": (
                    datetime.utcnow()
                    + timedelta(seconds=token_info.get("expires_in", 3600))
                ).isoformat(),
                "scope": token_info.get("scope"),
            }

            self.store_credentials(integration_id, credentials_data)

            # Update integration config
            config_updates = {
                "oauth_state": "completed",
                "user_info": {
                    "id": user_info.get("id"),
                    "email": user_info.get("mail")
                    or user_info.get("userPrincipalName"),
                    "display_name": user_info.get("displayName"),
                    "job_title": user_info.get("jobTitle"),
                    "office_location": user_info.get("officeLocation"),
                },
                "services": {"teams": True, "outlook": True, "onedrive": True},
                "sync_settings": {
                    "teams_sync_enabled": True,
                    "outlook_sync_enabled": True,
                    "extract_tasks_from_messages": True,
                    "extract_tasks_from_meetings": True,
                    "sync_personal_calendar": True,
                    "sync_team_channels": [],
                    "calendar_sync_days_ahead": 30,
                    "calendar_sync_days_behind": 7,
                },
                "last_teams_sync": None,
                "last_outlook_sync": None,
            }

            self.update_integration_config(integration_id, config_updates)
            self.update_integration_status(integration_id, IntegrationStatus.CONNECTED)

            # Test services
            test_result = self.test_connection(integration_id)

            self.log_integration_event(
                integration_id,
                "oauth_completed",
                {
                    "user_email": user_info.get("mail")
                    or user_info.get("userPrincipalName"),
                    "services_available": ["teams", "outlook", "onedrive"],
                },
            )

            return self.format_success_response(
                {
                    "integration_id": str(integration_id),
                    "user_email": user_info.get("mail")
                    or user_info.get("userPrincipalName"),
                    "display_name": user_info.get("displayName"),
                    "services": ["Microsoft Teams", "Outlook", "OneDrive"],
                    "status": "connected",
                }
            )

        except Exception as e:
            return self.format_error_response(e, "oauth_callback")

    def test_connection(self, integration_id: uuid.UUID) -> Dict[str, Any]:
        """Test Microsoft Graph API connection"""
        try:
            headers = self._get_auth_headers(integration_id)
            if not headers:
                return self.format_error_response(
                    Exception("No credentials found"), "test_connection"
                )

            # Test user profile access
            user_response = requests.get(f"{self.graph_endpoint}/me", headers=headers)
            user_response.raise_for_status()
            user_info = user_response.json()

            # Test Teams access
            teams_response = requests.get(
                f"{self.graph_endpoint}/me/joinedTeams", headers=headers
            )
            teams_count = (
                len(teams_response.json().get("value", []))
                if teams_response.status_code == 200
                else 0
            )

            # Test Calendar access
            calendar_response = requests.get(
                f"{self.graph_endpoint}/me/calendars", headers=headers
            )
            calendar_count = (
                len(calendar_response.json().get("value", []))
                if calendar_response.status_code == 200
                else 0
            )

            return self.format_success_response(
                {
                    "user_id": user_info.get("id"),
                    "display_name": user_info.get("displayName"),
                    "email": user_info.get("mail")
                    or user_info.get("userPrincipalName"),
                    "teams_count": teams_count,
                    "calendars_count": calendar_count,
                }
            )

        except Exception as e:
            return self.format_error_response(e, "test_connection")

    def refresh_credentials(self, integration_id: uuid.UUID) -> bool:
        """Refresh Microsoft OAuth credentials"""
        try:
            credentials = self.get_credentials(integration_id)
            if not credentials or not credentials.get("refresh_token"):
                return False

            # Check if token is expired
            expires_at = credentials.get("expires_at")
            if expires_at:
                expiry_time = datetime.fromisoformat(expires_at)
                if datetime.utcnow() < expiry_time - timedelta(minutes=5):
                    return True  # Token is still valid

            # Refresh token
            token_url = f"{self.authority}/oauth2/v2.0/token"
            token_data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": credentials["refresh_token"],
                "grant_type": "refresh_token",
                "scope": " ".join(self.delegated_scopes),
            }

            token_response = requests.post(token_url, data=token_data)
            token_response.raise_for_status()

            token_info = token_response.json()

            # Update stored credentials
            credentials_data = {
                "access_token": token_info["access_token"],
                "refresh_token": token_info.get(
                    "refresh_token", credentials.get("refresh_token")
                ),
                "token_type": token_info.get("token_type", "Bearer"),
                "expires_in": token_info.get("expires_in"),
                "expires_at": (
                    datetime.utcnow()
                    + timedelta(seconds=token_info.get("expires_in", 3600))
                ).isoformat(),
                "scope": token_info.get("scope"),
            }

            self.store_credentials(integration_id, credentials_data)
            self.update_integration_status(integration_id, IntegrationStatus.CONNECTED)

            return True

        except Exception as e:
            self.update_integration_status(
                integration_id, IntegrationStatus.ERROR, str(e)
            )
            return False

    def disconnect(self, integration_id: uuid.UUID) -> bool:
        """Disconnect Microsoft integration"""
        try:
            # Note: Microsoft Graph doesn't have a simple token revocation endpoint
            # In production, you might want to call the revoke endpoint if available

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
        """Sync data from Microsoft Teams and Outlook"""
        try:
            headers = self._get_auth_headers(integration_id)
            if not headers:
                return self.format_error_response(
                    Exception("No credentials"), "sync_data"
                )

            integration = self.get_integration(integration_id)
            sync_settings = integration.config.get("sync_settings", {})

            sync_results = {
                "teams_messages_processed": 0,
                "teams_tasks_created": 0,
                "outlook_events_processed": 0,
                "outlook_tasks_created": 0,
                "emails_processed": 0,
                "errors": [],
            }

            # Sync Teams if enabled
            if sync_settings.get("teams_sync_enabled", True):
                teams_result = self._sync_teams_data(integration_id, headers, sync_type)
                sync_results["teams_messages_processed"] = teams_result.get(
                    "messages_processed", 0
                )
                sync_results["teams_tasks_created"] = teams_result.get(
                    "tasks_created", 0
                )
                sync_results["errors"].extend(teams_result.get("errors", []))

            # Sync Outlook if enabled
            if sync_settings.get("outlook_sync_enabled", True):
                outlook_result = self._sync_outlook_data(
                    integration_id, headers, sync_type
                )
                sync_results["outlook_events_processed"] = outlook_result.get(
                    "events_processed", 0
                )
                sync_results["outlook_tasks_created"] = outlook_result.get(
                    "tasks_created", 0
                )
                sync_results["emails_processed"] = outlook_result.get(
                    "emails_processed", 0
                )
                sync_results["errors"].extend(outlook_result.get("errors", []))

            # Update sync timestamps
            self.update_integration_config(
                integration_id,
                {
                    "last_teams_sync": datetime.utcnow().isoformat(),
                    "last_outlook_sync": datetime.utcnow().isoformat(),
                },
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
        """Handle Microsoft Graph webhook notifications"""
        try:
            # Microsoft Graph sends webhook notifications for various resources
            validation_token = headers.get("validationToken")

            # Handle subscription validation
            if validation_token:
                return {"validationResponse": validation_token}

            # Process notification
            value = payload.get("value", [])

            result = {"processed": True, "notifications_handled": len(value)}

            for notification in value:
                resource = notification.get("resource")
                change_type = notification.get("changeType")
                resource_data = notification.get("resourceData", {})

                if "teams" in resource or "chats" in resource:
                    # Teams message notification
                    self._handle_teams_notification(integration_id, notification)
                elif "calendars" in resource or "events" in resource:
                    # Calendar event notification
                    self._handle_calendar_notification(integration_id, notification)
                elif "messages" in resource:
                    # Email notification
                    self._handle_email_notification(integration_id, notification)

            self.log_integration_event(
                integration_id,
                "webhook_processed",
                {
                    "notifications_count": len(value),
                    "resource_types": [n.get("resource", "unknown") for n in value],
                },
            )

            return self.format_success_response(result)

        except Exception as e:
            return self.format_error_response(e, "webhook")

    # Private helper methods

    def _get_auth_headers(self, integration_id: uuid.UUID) -> Optional[Dict[str, str]]:
        """Get authentication headers for Microsoft Graph API"""
        try:
            credentials = self.get_credentials(integration_id)
            if not credentials:
                return None

            # Check if token needs refresh
            expires_at = credentials.get("expires_at")
            if expires_at:
                expiry_time = datetime.fromisoformat(expires_at)
                if datetime.utcnow() >= expiry_time - timedelta(minutes=5):
                    # Token expired or expiring soon, try to refresh
                    if not self.refresh_credentials(integration_id):
                        return None
                    # Get updated credentials
                    credentials = self.get_credentials(integration_id)

            return {
                "Authorization": f"{credentials.get('token_type', 'Bearer')} {credentials['access_token']}",
                "Content-Type": "application/json",
            }

        except Exception:
            return None

    def _sync_teams_data(
        self, integration_id: uuid.UUID, headers: Dict[str, str], sync_type: str
    ) -> Dict[str, Any]:
        """Sync Microsoft Teams data"""
        try:
            integration = self.get_integration(integration_id)
            sync_settings = integration.config.get("sync_settings", {})

            result = {"messages_processed": 0, "tasks_created": 0, "errors": []}

            # Get joined teams
            teams_response = requests.get(
                f"{self.graph_endpoint}/me/joinedTeams", headers=headers
            )
            teams_response.raise_for_status()
            teams = teams_response.json().get("value", [])

            for team in teams:
                team_id = team.get("id")

                try:
                    # Get team channels
                    channels_response = requests.get(
                        f"{self.graph_endpoint}/teams/{team_id}/channels",
                        headers=headers,
                    )

                    if channels_response.status_code != 200:
                        continue

                    channels = channels_response.json().get("value", [])

                    for channel in channels:
                        channel_id = channel.get("id")

                        try:
                            # Get channel messages
                            messages_url = f"{self.graph_endpoint}/teams/{team_id}/channels/{channel_id}/messages"

                            # Add date filter for incremental sync
                            if sync_type == "incremental":
                                last_sync = integration.config.get("last_teams_sync")
                                if last_sync:
                                    last_sync_date = datetime.fromisoformat(
                                        last_sync.replace("Z", "+00:00")
                                    )
                                    messages_url += f"?$filter=createdDateTime gt {last_sync_date.isoformat()}"

                            messages_response = requests.get(
                                messages_url, headers=headers
                            )

                            if messages_response.status_code != 200:
                                continue

                            messages = messages_response.json().get("value", [])

                            for message in messages:
                                try:
                                    processed = self._process_teams_message(
                                        integration_id, message, team, channel
                                    )
                                    if processed:
                                        result["messages_processed"] += 1
                                        if processed.get("task_created"):
                                            result["tasks_created"] += 1
                                except Exception as e:
                                    result["errors"].append(
                                        f"Message processing: {str(e)}"
                                    )

                        except Exception as e:
                            result["errors"].append(
                                f"Channel {channel.get('displayName', 'unknown')}: {str(e)}"
                            )

                except Exception as e:
                    result["errors"].append(
                        f"Team {team.get('displayName', 'unknown')}: {str(e)}"
                    )

            return result

        except Exception as e:
            return {"messages_processed": 0, "tasks_created": 0, "errors": [str(e)]}

    def _sync_outlook_data(
        self, integration_id: uuid.UUID, headers: Dict[str, str], sync_type: str
    ) -> Dict[str, Any]:
        """Sync Microsoft Outlook data"""
        try:
            integration = self.get_integration(integration_id)
            sync_settings = integration.config.get("sync_settings", {})

            result = {
                "events_processed": 0,
                "tasks_created": 0,
                "emails_processed": 0,
                "errors": [],
            }

            # Sync calendar events
            if sync_settings.get("sync_personal_calendar", True):
                calendar_result = self._sync_calendar_events(
                    integration_id, headers, sync_type
                )
                result["events_processed"] = calendar_result.get("events_processed", 0)
                result["tasks_created"] += calendar_result.get("tasks_created", 0)
                result["errors"].extend(calendar_result.get("errors", []))

            # Sync emails (limited - just recent important ones)
            email_result = self._sync_recent_emails(integration_id, headers, sync_type)
            result["emails_processed"] = email_result.get("emails_processed", 0)
            result["errors"].extend(email_result.get("errors", []))

            return result

        except Exception as e:
            return {
                "events_processed": 0,
                "tasks_created": 0,
                "emails_processed": 0,
                "errors": [str(e)],
            }

    def _process_teams_message(
        self,
        integration_id: uuid.UUID,
        message: Dict[str, Any],
        team: Dict[str, Any],
        channel: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Process a Teams message for task extraction"""
        try:
            integration = self.get_integration(integration_id)

            # Check if task extraction is enabled
            if not integration.config.get("sync_settings", {}).get(
                "extract_tasks_from_messages", True
            ):
                return {"processed": True, "task_created": False}

            # Extract message content
            body = message.get("body", {})
            content = body.get("content", "") if isinstance(body, dict) else str(body)
            from_user = message.get("from", {}).get("user", {})

            if not content:
                return {"processed": True, "task_created": False}

            # Look for task-related content
            task_keywords = [
                "todo",
                "task",
                "action item",
                "follow up",
                "deadline",
                "due",
                "complete",
                "assign",
            ]
            content_lower = content.lower()

            has_task_keywords = any(
                keyword in content_lower for keyword in task_keywords
            )

            if not has_task_keywords:
                return {"processed": True, "task_created": False}

            # Use LangChain orchestrator to extract task
            company_id = integration.company_id
            creator = (
                self.db.query(User)
                .filter(
                    User.company_id == company_id,
                    User.role.in_(["CEO", "PM", "Supervisor"]),
                )
                .first()
            )

            if not creator:
                return {"processed": True, "task_created": False}

            orchestrator = LangChainOrchestrator(self.db)

            context = {
                "source": "microsoft_teams",
                "team": team.get("displayName", "Unknown Team"),
                "channel": channel.get("displayName", "Unknown Channel"),
                "message_author": from_user.get("displayName", "Unknown User"),
                "integration_id": str(integration_id),
            }

            # Process with orchestrator
            result = orchestrator._handle_task_management(
                user_input=content, user_id=creator.id, context=context
            )

            if result and "task created" in result.lower():
                return {"processed": True, "task_created": True}

            return {"processed": True, "task_created": False}

        except Exception as e:
            self.log_integration_event(
                integration_id, "teams_message_processing_error", {"error": str(e)}
            )
            return None

    def _sync_calendar_events(
        self, integration_id: uuid.UUID, headers: Dict[str, str], sync_type: str
    ) -> Dict[str, Any]:
        """Sync calendar events from Outlook"""
        try:
            integration = self.get_integration(integration_id)
            sync_settings = integration.config.get("sync_settings", {})

            result = {"events_processed": 0, "tasks_created": 0, "errors": []}

            # Calculate time range
            now = datetime.utcnow()
            start_time = (
                now - timedelta(days=sync_settings.get("calendar_sync_days_behind", 7))
            ).isoformat()
            end_time = (
                now + timedelta(days=sync_settings.get("calendar_sync_days_ahead", 30))
            ).isoformat()

            # Get calendar events
            events_url = f"{self.graph_endpoint}/me/events?$filter=start/dateTime ge '{start_time}' and end/dateTime le '{end_time}'"

            events_response = requests.get(events_url, headers=headers)
            events_response.raise_for_status()

            events = events_response.json().get("value", [])

            for event in events:
                try:
                    processed = self._process_calendar_event(integration_id, event)
                    if processed:
                        result["events_processed"] += 1
                        if processed.get("task_created"):
                            result["tasks_created"] += 1
                except Exception as e:
                    result["errors"].append(f"Event processing: {str(e)}")

            return result

        except Exception as e:
            return {"events_processed": 0, "tasks_created": 0, "errors": [str(e)]}

    def _sync_recent_emails(
        self, integration_id: uuid.UUID, headers: Dict[str, str], sync_type: str
    ) -> Dict[str, Any]:
        """Sync recent important emails"""
        try:
            result = {"emails_processed": 0, "errors": []}

            # Get recent high-importance emails
            emails_url = f"{self.graph_endpoint}/me/messages?$filter=importance eq 'high'&$top=20&$orderby=receivedDateTime desc"

            emails_response = requests.get(emails_url, headers=headers)
            if emails_response.status_code != 200:
                return result

            emails = emails_response.json().get("value", [])

            for email in emails:
                try:
                    # For now, just log that we processed it
                    # In a full implementation, you'd extract tasks from email content
                    self.log_integration_event(
                        integration_id,
                        "email_processed",
                        {
                            "subject": email.get("subject", "No Subject"),
                            "from": email.get("from", {})
                            .get("emailAddress", {})
                            .get("address", "Unknown"),
                            "importance": email.get("importance", "normal"),
                        },
                    )

                    result["emails_processed"] += 1

                except Exception as e:
                    result["errors"].append(f"Email processing: {str(e)}")

            return result

        except Exception as e:
            return {"emails_processed": 0, "errors": [str(e)]}

    def _process_calendar_event(
        self, integration_id: uuid.UUID, event: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process a calendar event and potentially create tasks"""
        try:
            integration = self.get_integration(integration_id)

            # Check if task creation from events is enabled
            if not integration.config.get("sync_settings", {}).get(
                "extract_tasks_from_meetings", True
            ):
                return {"processed": True, "task_created": False}

            subject = event.get("subject", "Untitled Event")
            body = event.get("body", {})
            content = body.get("content", "") if isinstance(body, dict) else str(body)

            # Check if this looks like a task-related event
            task_keywords = [
                "meeting",
                "review",
                "deadline",
                "due",
                "complete",
                "finish",
                "deliver",
                "submit",
                "action",
            ]

            event_text = f"{subject} {content}".lower()
            is_task_related = any(keyword in event_text for keyword in task_keywords)

            if not is_task_related:
                return {"processed": True, "task_created": False}

            # Create task
            company_id = integration.company_id
            creator = (
                self.db.query(User)
                .filter(
                    User.company_id == company_id,
                    User.role.in_(["CEO", "PM", "Supervisor"]),
                )
                .first()
            )

            if not creator:
                return {"processed": True, "task_created": False}

            # Check if task already exists
            event_id = event.get("id", "")
            existing_task = (
                self.db.query(Task)
                .filter(Task.original_prompt.contains(event_id))
                .first()
            )

            if existing_task:
                return {"processed": True, "task_created": False}

            # Create new task
            start_time_str = event.get("start", {}).get("dateTime", "")

            new_task = Task(
                id=uuid.uuid4(),
                name=f"Meeting: {subject}",
                description=f"[Microsoft Calendar Event]\n{content}\n\nEvent Time: {start_time_str}",
                status="pending",
                assigned_to=None,  # Will be assigned later
                created_by=creator.id,
                original_prompt=f"Microsoft Calendar event: {event_id}",
                priority="medium",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db.add(new_task)
            self.db.commit()

            return {
                "processed": True,
                "task_created": True,
                "task_id": str(new_task.id),
            }

        except Exception as e:
            self.log_integration_event(
                integration_id, "calendar_event_processing_error", {"error": str(e)}
            )
            return None

    def _handle_teams_notification(
        self, integration_id: uuid.UUID, notification: Dict[str, Any]
    ):
        """Handle Teams webhook notification"""
        try:
            # This would trigger incremental sync for the specific resource
            self.log_integration_event(
                integration_id,
                "teams_webhook_received",
                {
                    "resource": notification.get("resource"),
                    "change_type": notification.get("changeType"),
                },
            )

            # Trigger incremental sync
            # In a production system, you might queue this for background processing

        except Exception as e:
            self.log_integration_event(
                integration_id, "teams_webhook_error", {"error": str(e)}
            )

    def _handle_calendar_notification(
        self, integration_id: uuid.UUID, notification: Dict[str, Any]
    ):
        """Handle Calendar webhook notification"""
        try:
            self.log_integration_event(
                integration_id,
                "calendar_webhook_received",
                {
                    "resource": notification.get("resource"),
                    "change_type": notification.get("changeType"),
                },
            )

        except Exception as e:
            self.log_integration_event(
                integration_id, "calendar_webhook_error", {"error": str(e)}
            )

    def _handle_email_notification(
        self, integration_id: uuid.UUID, notification: Dict[str, Any]
    ):
        """Handle Email webhook notification"""
        try:
            self.log_integration_event(
                integration_id,
                "email_webhook_received",
                {
                    "resource": notification.get("resource"),
                    "change_type": notification.get("changeType"),
                },
            )

        except Exception as e:
            self.log_integration_event(
                integration_id, "email_webhook_error", {"error": str(e)}
            )

    # Public API methods

    def get_teams(self, integration_id: uuid.UUID) -> Dict[str, Any]:
        """Get list of joined Microsoft Teams"""
        try:
            # Try using new Graph SDK first, fall back to REST API
            try:
                return asyncio.run(self._get_teams_with_sdk(integration_id))
            except Exception:
                # Fallback to REST API
                headers = self._get_auth_headers(integration_id)
                if not headers:
                    return self.format_error_response(
                        Exception("No credentials"), "get_teams"
                    )

                teams_response = requests.get(
                    f"{self.graph_endpoint}/me/joinedTeams", headers=headers
                )
                teams_response.raise_for_status()

                teams = [
                    {
                        "id": team["id"],
                        "display_name": team.get("displayName", "Untitled Team"),
                        "description": team.get("description", ""),
                        "web_url": team.get("webUrl", ""),
                    }
                    for team in teams_response.json().get("value", [])
                ]

                return self.format_success_response(teams)

        except Exception as e:
            return self.format_error_response(e, "get_teams")

    async def _get_teams_with_sdk(self, integration_id: uuid.UUID) -> Dict[str, Any]:
        """Get teams using the new Graph SDK"""
        client = await self._get_graph_client(integration_id)
        if not client:
            raise Exception("Could not create Graph client")

        # Get joined teams using the SDK
        teams_result = await client.me.joined_teams.get()

        teams = []
        if teams_result and teams_result.value:
            for team in teams_result.value:
                teams.append(
                    {
                        "id": team.id,
                        "display_name": team.display_name or "Untitled Team",
                        "description": team.description or "",
                        "web_url": team.web_url or "",
                    }
                )

        return self.format_success_response(teams)

    def get_calendars(self, integration_id: uuid.UUID) -> Dict[str, Any]:
        """Get list of Outlook calendars"""
        try:
            headers = self._get_auth_headers(integration_id)
            if not headers:
                return self.format_error_response(
                    Exception("No credentials"), "get_calendars"
                )

            calendars_response = requests.get(
                f"{self.graph_endpoint}/me/calendars", headers=headers
            )
            calendars_response.raise_for_status()

            calendars = [
                {
                    "id": cal["id"],
                    "name": cal.get("name", "Untitled Calendar"),
                    "color": cal.get("color", "auto"),
                    "is_default": cal.get("isDefaultCalendar", False),
                    "can_edit": cal.get("canEdit", False),
                }
                for cal in calendars_response.json().get("value", [])
            ]

            return self.format_success_response(calendars)

        except Exception as e:
            return self.format_error_response(e, "get_calendars")

    def create_calendar_event(
        self, integration_id: uuid.UUID, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create event in Outlook calendar"""
        try:
            headers = self._get_auth_headers(integration_id)
            if not headers:
                return self.format_error_response(
                    Exception("No credentials"), "create_event"
                )

            event = {
                "subject": event_data.get("subject", "New Event from Vira"),
                "body": {
                    "contentType": "HTML",
                    "content": event_data.get("description", ""),
                },
                "start": {
                    "dateTime": event_data.get("start_time"),
                    "timeZone": event_data.get("timezone", "UTC"),
                },
                "end": {
                    "dateTime": event_data.get("end_time"),
                    "timeZone": event_data.get("timezone", "UTC"),
                },
            }

            # Add attendees if provided
            if event_data.get("attendees"):
                event["attendees"] = [
                    {"emailAddress": {"address": email, "name": email.split("@")[0]}}
                    for email in event_data["attendees"]
                ]

            calendar_id = event_data.get("calendar_id", "calendar")
            events_response = requests.post(
                f"{self.graph_endpoint}/me/{calendar_id}/events",
                headers=headers,
                json=event,
            )
            events_response.raise_for_status()

            created_event = events_response.json()

            return self.format_success_response(
                {
                    "event_id": created_event.get("id"),
                    "web_link": created_event.get("webLink"),
                }
            )

        except Exception as e:
            return self.format_error_response(e, "create_event")

    def send_teams_message(
        self, integration_id: uuid.UUID, channel_id: str, message: str, **kwargs
    ) -> Dict[str, Any]:
        """Send message to Microsoft Teams channel"""
        try:
            headers = self._get_auth_headers(integration_id)
            if not headers:
                return self.format_error_response(
                    Exception("No credentials"), "send_message"
                )

            message_data = {"body": {"contentType": "html", "content": message}}

            # Note: Sending messages to Teams requires specific permissions and setup
            # This is a simplified implementation

            return self.format_success_response(
                {
                    "message": "Teams message functionality requires additional setup",
                    "status": "not_implemented",
                }
            )

        except Exception as e:
            return self.format_error_response(e, "send_message")
