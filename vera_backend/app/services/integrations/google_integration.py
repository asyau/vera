"""
Google Integration Service
Comprehensive Google Calendar/Drive integration as specified in RFC Section 13.3 & 13.4
"""

import io
import json
import os
import pickle
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from app.core.config import settings
from app.models.sql_models import Company, Task, User

from .base_integration import BaseIntegrationService, IntegrationStatus, IntegrationType


class GoogleIntegrationService(BaseIntegrationService):
    """
    Google Integration Service implementing RFC Sections 13.3 & 13.4:
    - OAuth 2.0 authentication for Google services
    - Google Calendar integration for task deadlines and meeting extraction
    - Google Drive integration for document ingestion and linking
    - Automatic task creation from calendar events
    - Document processing and Q&A capabilities
    """

    def __init__(self, db):
        super().__init__(db)
        self.client_secrets_file = getattr(settings, "google_client_secrets_file", None)
        self.scopes = [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ]

    def _get_integration_type(self) -> IntegrationType:
        return (
            IntegrationType.GOOGLE_CALENDAR
        )  # Primary type, but handles both Calendar and Drive

    def get_authorization_url(
        self, company_id: uuid.UUID, user_id: uuid.UUID, redirect_uri: str, **kwargs
    ) -> str:
        """Generate Google OAuth authorization URL"""
        if not self.client_secrets_file or not os.path.exists(self.client_secrets_file):
            raise ValueError("Google client secrets file not found")

        # Create OAuth flow
        flow = Flow.from_client_secrets_file(
            self.client_secrets_file, scopes=self.scopes, redirect_uri=redirect_uri
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

        authorization_url, _ = flow.authorization_url(
            access_type="offline", include_granted_scopes="true", state=updated_state
        )

        return authorization_url

    def handle_oauth_callback(self, code: str, state: str, **kwargs) -> Dict[str, Any]:
        """Handle Google OAuth callback"""
        try:
            # Parse state
            state_data = json.loads(state)
            integration_id = uuid.UUID(state_data.get("integration_id"))

            integration = self.get_integration(integration_id)
            if not integration:
                return self.format_error_response(
                    ValueError("Integration not found"), "oauth_callback"
                )

            # Create OAuth flow
            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=self.scopes,
                redirect_uri=integration.config.get("redirect_uri"),
            )

            # Exchange code for token
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Test the credentials
            service = build("oauth2", "v2", credentials=credentials)
            user_info = service.userinfo().get().execute()

            # Store credentials
            credentials_data = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
                "expiry": credentials.expiry.isoformat()
                if credentials.expiry
                else None,
            }

            self.store_credentials(integration_id, credentials_data)

            # Update integration config
            config_updates = {
                "oauth_state": "completed",
                "user_info": {
                    "email": user_info.get("email"),
                    "name": user_info.get("name"),
                    "picture": user_info.get("picture"),
                },
                "services": {"calendar": True, "drive": True},
                "sync_settings": {
                    "calendar_sync_enabled": True,
                    "drive_sync_enabled": True,
                    "create_tasks_from_events": True,
                    "sync_drive_folders": [],
                    "calendar_sync_days_ahead": 30,
                    "calendar_sync_days_behind": 7,
                },
                "last_calendar_sync": None,
                "last_drive_sync": None,
            }

            self.update_integration_config(integration_id, config_updates)
            self.update_integration_status(integration_id, IntegrationStatus.CONNECTED)

            # Test services
            test_result = self.test_connection(integration_id)

            self.log_integration_event(
                integration_id,
                "oauth_completed",
                {
                    "user_email": user_info.get("email"),
                    "services_available": ["calendar", "drive"],
                },
            )

            return self.format_success_response(
                {
                    "integration_id": str(integration_id),
                    "user_email": user_info.get("email"),
                    "user_name": user_info.get("name"),
                    "services": ["Google Calendar", "Google Drive"],
                    "status": "connected",
                }
            )

        except Exception as e:
            return self.format_error_response(e, "oauth_callback")

    def test_connection(self, integration_id: uuid.UUID) -> Dict[str, Any]:
        """Test Google services connection"""
        try:
            credentials = self._get_google_credentials(integration_id)
            if not credentials:
                return self.format_error_response(
                    Exception("No credentials found"), "test_connection"
                )

            # Test Calendar API
            calendar_service = build("calendar", "v3", credentials=credentials)
            calendar_list = calendar_service.calendarList().list().execute()

            # Test Drive API
            drive_service = build("drive", "v3", credentials=credentials)
            about = drive_service.about().get(fields="user").execute()

            return self.format_success_response(
                {
                    "calendar_access": True,
                    "calendars_count": len(calendar_list.get("items", [])),
                    "drive_access": True,
                    "drive_user": about.get("user", {}).get("displayName", "Unknown"),
                }
            )

        except HttpError as e:
            return self.format_error_response(e, "test_connection")
        except Exception as e:
            return self.format_error_response(e, "test_connection")

    def refresh_credentials(self, integration_id: uuid.UUID) -> bool:
        """Refresh Google OAuth credentials"""
        try:
            credentials = self._get_google_credentials(integration_id)
            if not credentials:
                return False

            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

                # Update stored credentials
                credentials_data = {
                    "token": credentials.token,
                    "refresh_token": credentials.refresh_token,
                    "token_uri": credentials.token_uri,
                    "client_id": credentials.client_id,
                    "client_secret": credentials.client_secret,
                    "scopes": credentials.scopes,
                    "expiry": credentials.expiry.isoformat()
                    if credentials.expiry
                    else None,
                }

                self.store_credentials(integration_id, credentials_data)
                self.update_integration_status(
                    integration_id, IntegrationStatus.CONNECTED
                )

                return True

            return True  # Credentials are still valid

        except Exception as e:
            self.update_integration_status(
                integration_id, IntegrationStatus.ERROR, str(e)
            )
            return False

    def disconnect(self, integration_id: uuid.UUID) -> bool:
        """Disconnect Google integration"""
        try:
            # Revoke credentials if possible
            credentials = self._get_google_credentials(integration_id)
            if credentials and credentials.token:
                try:
                    import requests

                    requests.post(
                        "https://oauth2.googleapis.com/revoke",
                        params={"token": credentials.token},
                        headers={"content-type": "application/x-www-form-urlencoded"},
                    )
                except:
                    pass  # Revocation failed, but we'll continue with disconnect

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
        """Sync data from Google Calendar and Drive"""
        try:
            credentials = self._get_google_credentials(integration_id)
            if not credentials:
                return self.format_error_response(
                    Exception("No credentials"), "sync_data"
                )

            integration = self.get_integration(integration_id)
            sync_settings = integration.config.get("sync_settings", {})

            sync_results = {
                "calendar_events_processed": 0,
                "calendar_tasks_created": 0,
                "drive_files_processed": 0,
                "drive_documents_indexed": 0,
                "errors": [],
            }

            # Sync Calendar if enabled
            if sync_settings.get("calendar_sync_enabled", True):
                calendar_result = self._sync_calendar_data(
                    integration_id, credentials, sync_type
                )
                sync_results["calendar_events_processed"] = calendar_result.get(
                    "events_processed", 0
                )
                sync_results["calendar_tasks_created"] = calendar_result.get(
                    "tasks_created", 0
                )
                sync_results["errors"].extend(calendar_result.get("errors", []))

            # Sync Drive if enabled
            if sync_settings.get("drive_sync_enabled", True):
                drive_result = self._sync_drive_data(
                    integration_id, credentials, sync_type
                )
                sync_results["drive_files_processed"] = drive_result.get(
                    "files_processed", 0
                )
                sync_results["drive_documents_indexed"] = drive_result.get(
                    "documents_indexed", 0
                )
                sync_results["errors"].extend(drive_result.get("errors", []))

            # Update sync timestamps
            self.update_integration_config(
                integration_id,
                {
                    "last_calendar_sync": datetime.utcnow().isoformat(),
                    "last_drive_sync": datetime.utcnow().isoformat(),
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
        """Handle Google webhook notifications (Calendar push notifications)"""
        try:
            # Google Calendar sends push notifications for calendar changes
            resource_id = headers.get("X-Goog-Resource-ID")
            resource_state = headers.get("X-Goog-Resource-State")

            if resource_state == "sync":
                # Initial sync notification, acknowledge
                return self.format_success_response({"acknowledged": True})

            elif resource_state in ["exists", "not_exists"]:
                # Calendar event changed, trigger incremental sync
                sync_result = self.sync_data(integration_id, "incremental")

                return self.format_success_response(
                    {
                        "processed": True,
                        "action": "incremental_sync_triggered",
                        "sync_result": sync_result,
                    }
                )

            self.log_integration_event(
                integration_id,
                "webhook_received",
                {"resource_state": resource_state, "resource_id": resource_id},
            )

            return self.format_success_response({"processed": True})

        except Exception as e:
            return self.format_error_response(e, "webhook")

    # Private helper methods

    def _get_google_credentials(
        self, integration_id: uuid.UUID
    ) -> Optional[Credentials]:
        """Get Google OAuth credentials"""
        try:
            credentials_data = self.get_credentials(integration_id)
            if not credentials_data:
                return None

            credentials = Credentials(
                token=credentials_data.get("token"),
                refresh_token=credentials_data.get("refresh_token"),
                token_uri=credentials_data.get("token_uri"),
                client_id=credentials_data.get("client_id"),
                client_secret=credentials_data.get("client_secret"),
                scopes=credentials_data.get("scopes"),
            )

            # Set expiry if available
            if credentials_data.get("expiry"):
                credentials.expiry = datetime.fromisoformat(credentials_data["expiry"])

            return credentials

        except Exception:
            return None

    def _sync_calendar_data(
        self, integration_id: uuid.UUID, credentials: Credentials, sync_type: str
    ) -> Dict[str, Any]:
        """Sync Google Calendar data"""
        try:
            calendar_service = build("calendar", "v3", credentials=credentials)
            integration = self.get_integration(integration_id)
            sync_settings = integration.config.get("sync_settings", {})

            result = {"events_processed": 0, "tasks_created": 0, "errors": []}

            # Get calendars
            calendar_list = calendar_service.calendarList().list().execute()

            # Calculate time range
            now = datetime.utcnow()
            time_min = (
                now - timedelta(days=sync_settings.get("calendar_sync_days_behind", 7))
            ).isoformat() + "Z"
            time_max = (
                now + timedelta(days=sync_settings.get("calendar_sync_days_ahead", 30))
            ).isoformat() + "Z"

            for calendar_item in calendar_list.get("items", []):
                calendar_id = calendar_item["id"]

                try:
                    # Get events from this calendar
                    events_result = (
                        calendar_service.events()
                        .list(
                            calendarId=calendar_id,
                            timeMin=time_min,
                            timeMax=time_max,
                            maxResults=100,
                            singleEvents=True,
                            orderBy="startTime",
                        )
                        .execute()
                    )

                    events = events_result.get("items", [])

                    for event in events:
                        try:
                            processed = self._process_calendar_event(
                                integration_id, event, calendar_item
                            )
                            if processed:
                                result["events_processed"] += 1
                                if processed.get("task_created"):
                                    result["tasks_created"] += 1
                        except Exception as e:
                            result["errors"].append(
                                f"Event {event.get('id', 'unknown')}: {str(e)}"
                            )

                except HttpError as e:
                    result["errors"].append(f"Calendar {calendar_id}: {str(e)}")

            return result

        except Exception as e:
            return {"events_processed": 0, "tasks_created": 0, "errors": [str(e)]}

    def _sync_drive_data(
        self, integration_id: uuid.UUID, credentials: Credentials, sync_type: str
    ) -> Dict[str, Any]:
        """Sync Google Drive data"""
        try:
            drive_service = build("drive", "v3", credentials=credentials)
            integration = self.get_integration(integration_id)
            sync_settings = integration.config.get("sync_settings", {})

            result = {"files_processed": 0, "documents_indexed": 0, "errors": []}

            # Get folders to sync (if specified)
            folders_to_sync = sync_settings.get("sync_drive_folders", [])

            query = "mimeType != 'application/vnd.google-apps.folder'"

            if folders_to_sync:
                # Limit to specific folders
                folder_queries = [
                    f"'{folder_id}' in parents" for folder_id in folders_to_sync
                ]
                query += f" and ({' or '.join(folder_queries)})"

            # Add date filter for incremental sync
            if sync_type == "incremental":
                last_sync = integration.config.get("last_drive_sync")
                if last_sync:
                    last_sync_date = datetime.fromisoformat(
                        last_sync.replace("Z", "+00:00")
                    )
                    query += f" and modifiedTime > '{last_sync_date.isoformat()}'"

            # Get files
            files_result = (
                drive_service.files()
                .list(
                    q=query,
                    pageSize=100,
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink, parents)",
                )
                .execute()
            )

            files = files_result.get("files", [])

            for file in files:
                try:
                    processed = self._process_drive_file(
                        integration_id, drive_service, file
                    )
                    if processed:
                        result["files_processed"] += 1
                        if processed.get("document_indexed"):
                            result["documents_indexed"] += 1
                except Exception as e:
                    result["errors"].append(
                        f"File {file.get('name', 'unknown')}: {str(e)}"
                    )

            return result

        except Exception as e:
            return {"files_processed": 0, "documents_indexed": 0, "errors": [str(e)]}

    def _process_calendar_event(
        self, integration_id: uuid.UUID, event: Dict[str, Any], calendar: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process a calendar event and potentially create tasks"""
        try:
            integration = self.get_integration(integration_id)

            # Check if task creation from events is enabled
            if not integration.config.get("sync_settings", {}).get(
                "create_tasks_from_events", True
            ):
                return {"processed": True, "task_created": False}

            # Extract event details
            summary = event.get("summary", "Untitled Event")
            description = event.get("description", "")
            start = event.get("start", {})
            end = event.get("end", {})

            # Skip all-day events or events without specific times
            if "dateTime" not in start:
                return {"processed": True, "task_created": False}

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
            ]

            event_text = f"{summary} {description}".lower()
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
            existing_task = (
                self.db.query(Task)
                .filter(Task.original_prompt.contains(event.get("id", "")))
                .first()
            )

            if existing_task:
                return {"processed": True, "task_created": False}

            # Create new task
            start_time = datetime.fromisoformat(
                start["dateTime"].replace("Z", "+00:00")
            )

            new_task = Task(
                id=uuid.uuid4(),
                name=f"Calendar: {summary}",
                description=f"[Google Calendar Event]\n{description}\n\nEvent Time: {start_time.strftime('%Y-%m-%d %H:%M')}",
                status="pending",
                assigned_to=None,  # Will be assigned later
                created_by=creator.id,
                original_prompt=f"Google Calendar event: {event.get('id')}",
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

    def _process_drive_file(
        self, integration_id: uuid.UUID, drive_service, file: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process a Google Drive file for indexing"""
        try:
            file_id = file.get("id")
            file_name = file.get("name", "Untitled")
            mime_type = file.get("mimeType", "")

            # Only process text-based documents
            supported_types = [
                "application/vnd.google-apps.document",
                "application/vnd.google-apps.presentation",
                "application/vnd.google-apps.spreadsheet",
                "text/plain",
                "application/pdf",
            ]

            if mime_type not in supported_types:
                return {"processed": True, "document_indexed": False}

            # Extract text content (simplified - in production, you'd use proper text extraction)
            try:
                if mime_type == "application/vnd.google-apps.document":
                    # Export as plain text
                    request = drive_service.files().export_media(
                        fileId=file_id, mimeType="text/plain"
                    )
                    file_content = request.execute().decode("utf-8")
                else:
                    # For other types, we'd implement specific extraction logic
                    file_content = f"Document: {file_name}\nType: {mime_type}\nLink: {file.get('webViewLink', '')}"

                # Here you would typically:
                # 1. Chunk the content
                # 2. Generate embeddings
                # 3. Store in vector database
                # 4. Link to projects/teams

                # For now, we'll just log that we processed it
                self.log_integration_event(
                    integration_id,
                    "drive_file_processed",
                    {
                        "file_id": file_id,
                        "file_name": file_name,
                        "mime_type": mime_type,
                        "content_length": len(file_content),
                    },
                )

                return {"processed": True, "document_indexed": True}

            except Exception as e:
                self.log_integration_event(
                    integration_id,
                    "drive_file_extraction_error",
                    {"file_id": file_id, "error": str(e)},
                )
                return {"processed": True, "document_indexed": False}

        except Exception as e:
            self.log_integration_event(
                integration_id, "drive_file_processing_error", {"error": str(e)}
            )
            return None

    # Public API methods

    def get_calendars(self, integration_id: uuid.UUID) -> Dict[str, Any]:
        """Get list of Google Calendars"""
        try:
            credentials = self._get_google_credentials(integration_id)
            if not credentials:
                return self.format_error_response(
                    Exception("No credentials"), "get_calendars"
                )

            calendar_service = build("calendar", "v3", credentials=credentials)
            calendar_list = calendar_service.calendarList().list().execute()

            calendars = [
                {
                    "id": cal["id"],
                    "summary": cal.get("summary", "Untitled Calendar"),
                    "description": cal.get("description", ""),
                    "primary": cal.get("primary", False),
                    "access_role": cal.get("accessRole", "reader"),
                }
                for cal in calendar_list.get("items", [])
            ]

            return self.format_success_response(calendars)

        except Exception as e:
            return self.format_error_response(e, "get_calendars")

    def get_calendar_events(
        self,
        integration_id: uuid.UUID,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get Google Calendar events for a specific date range"""
        try:
            credentials = self._get_google_credentials(integration_id)
            if not credentials:
                return self.format_error_response(
                    Exception("No credentials"), "get_calendar_events"
                )

            calendar_service = build("calendar", "v3", credentials=credentials)

            # Set default date range if not provided
            now = datetime.utcnow()
            if not start_date:
                start_date = (now - timedelta(days=30)).isoformat() + "Z"
            elif not start_date.endswith("Z"):
                start_date = start_date + "Z"

            if not end_date:
                end_date = (now + timedelta(days=30)).isoformat() + "Z"
            elif not end_date.endswith("Z"):
                end_date = end_date + "Z"

            # Get list of calendars first
            calendar_list = calendar_service.calendarList().list().execute()
            all_events = []

            for calendar_item in calendar_list.get("items", []):
                calendar_id = calendar_item["id"]

                try:
                    # Get events from this calendar
                    events_result = (
                        calendar_service.events()
                        .list(
                            calendarId=calendar_id,
                            timeMin=start_date,
                            timeMax=end_date,
                            maxResults=250,
                            singleEvents=True,
                            orderBy="startTime",
                        )
                        .execute()
                    )

                    events = events_result.get("items", [])

                    # Format events for frontend
                    for event in events:
                        formatted_event = {
                            "id": event.get("id"),
                            "summary": event.get("summary", "No Title"),
                            "description": event.get("description", ""),
                            "start": event.get("start", {}),
                            "end": event.get("end", {}),
                            "location": event.get("location", ""),
                            "attendees": event.get("attendees", []),
                            "htmlLink": event.get("htmlLink", ""),
                            "calendar_id": calendar_id,
                            "calendar_name": calendar_item.get(
                                "summary", "Unknown Calendar"
                            ),
                        }
                        all_events.append(formatted_event)

                except HttpError as e:
                    # Skip calendars that can't be accessed
                    continue

            # Sort events by start time
            all_events.sort(
                key=lambda x: x.get("start", {}).get(
                    "dateTime", x.get("start", {}).get("date", "")
                )
            )

            return self.format_success_response(all_events)

        except Exception as e:
            return self.format_error_response(e, "get_calendar_events")

    def create_calendar_event(
        self, integration_id: uuid.UUID, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create event in Google Calendar"""
        try:
            credentials = self._get_google_credentials(integration_id)
            if not credentials:
                return self.format_error_response(
                    Exception("No credentials"), "create_event"
                )

            calendar_service = build("calendar", "v3", credentials=credentials)

            event = {
                "summary": event_data.get("summary", "New Event from Vira"),
                "description": event_data.get("description", ""),
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
                    {"email": email} for email in event_data["attendees"]
                ]

            calendar_id = event_data.get("calendar_id", "primary")
            created_event = (
                calendar_service.events()
                .insert(calendarId=calendar_id, body=event)
                .execute()
            )

            return self.format_success_response(
                {
                    "event_id": created_event.get("id"),
                    "html_link": created_event.get("htmlLink"),
                }
            )

        except Exception as e:
            return self.format_error_response(e, "create_event")

    def get_drive_folders(self, integration_id: uuid.UUID) -> Dict[str, Any]:
        """Get list of Google Drive folders"""
        try:
            credentials = self._get_google_credentials(integration_id)
            if not credentials:
                return self.format_error_response(
                    Exception("No credentials"), "get_folders"
                )

            drive_service = build("drive", "v3", credentials=credentials)

            folders_result = (
                drive_service.files()
                .list(
                    q="mimeType='application/vnd.google-apps.folder'",
                    pageSize=100,
                    fields="nextPageToken, files(id, name, parents)",
                )
                .execute()
            )

            folders = [
                {
                    "id": folder["id"],
                    "name": folder["name"],
                    "parent_folders": folder.get("parents", []),
                }
                for folder in folders_result.get("files", [])
            ]

            return self.format_success_response(folders)

        except Exception as e:
            return self.format_error_response(e, "get_folders")
