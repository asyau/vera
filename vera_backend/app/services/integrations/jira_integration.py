"""
Jira Integration Service
Comprehensive Jira integration as specified in RFC Section 13.2
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from jira import JIRA
from jira.exceptions import JIRAError

from app.core.config import settings
from app.models.sql_models import Company, Task, User
from app.services.langchain_orchestrator import LangChainOrchestrator

from .base_integration import BaseIntegrationService, IntegrationStatus, IntegrationType


class JiraIntegrationService(BaseIntegrationService):
    """
    Jira Integration Service implementing RFC Section 13.2 requirements:
    - OAuth and API token authentication
    - Issue data pull and sync with Vira tasks
    - Auto-create Vira tasks from Jira comments/status changes
    - Bi-directional sync of task status
    - Consolidated reporting combining Vira and Jira data
    - Webhook handling for real-time updates
    """

    def __init__(self, db):
        super().__init__(db)
        self.server_url = getattr(settings, "jira_server_url", None)
        self.consumer_key = getattr(settings, "jira_consumer_key", None)
        self.consumer_secret = getattr(settings, "jira_consumer_secret", None)

    def _get_integration_type(self) -> IntegrationType:
        return IntegrationType.JIRA

    def get_authorization_url(
        self, company_id: uuid.UUID, user_id: uuid.UUID, redirect_uri: str, **kwargs
    ) -> str:
        """Generate Jira OAuth authorization URL or return API token setup instructions"""
        auth_method = kwargs.get("auth_method", "api_token")

        if auth_method == "api_token":
            # For API token method, return setup instructions
            return f"Please create an API token at: {self.server_url}/secure/ViewProfile.jspa?selectedTab=com.atlassian.pats.pats-plugin:jira-user-personal-access-tokens"

        elif auth_method == "oauth":
            # OAuth 1.0a flow (for self-hosted Jira)
            if not self.consumer_key or not self.consumer_secret:
                raise ValueError("Jira OAuth not configured")

            # Create temporary integration to store OAuth flow state
            config = {
                "auth_method": "oauth",
                "oauth_state": "pending",
                "redirect_uri": redirect_uri,
                "user_id": str(user_id),
                "company_id": str(company_id),
            }

            integration = self.create_integration(company_id, user_id, config)

            # Initialize OAuth flow
            oauth_dict = {
                "consumer_key": self.consumer_key,
                "consumer_secret": self.consumer_secret,
                "access_token": "",
                "access_token_secret": "",
                "request_token": "",
                "request_token_secret": "",
            }

            try:
                jira = JIRA(server=self.server_url, oauth=oauth_dict)
                request_token = jira._get_oauth_request_token()

                # Store request token
                config["oauth_request_token"] = request_token
                self.update_integration_config(integration.id, config)

                return jira._get_oauth_authorization_url(request_token)

            except JIRAError as e:
                raise ValueError(f"OAuth setup failed: {str(e)}")

        else:
            raise ValueError("Unsupported auth method")

    def handle_oauth_callback(self, code: str, state: str, **kwargs) -> Dict[str, Any]:
        """Handle Jira OAuth callback or API token setup"""
        auth_method = kwargs.get("auth_method", "api_token")

        if auth_method == "api_token":
            return self._setup_api_token_auth(kwargs)
        elif auth_method == "oauth":
            return self._handle_oauth_callback(code, state, kwargs)
        else:
            return self.format_error_response(
                ValueError("Unsupported auth method"), "oauth_callback"
            )

    def _setup_api_token_auth(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Setup API token authentication"""
        try:
            email = kwargs.get("email")
            api_token = kwargs.get("api_token")
            server_url = kwargs.get("server_url", self.server_url)
            company_id = uuid.UUID(kwargs.get("company_id"))
            user_id = uuid.UUID(kwargs.get("user_id"))

            if not all([email, api_token, server_url]):
                return self.format_error_response(
                    ValueError("Missing required fields: email, api_token, server_url"),
                    "api_token_setup",
                )

            # Test connection
            jira = JIRA(server=server_url, basic_auth=(email, api_token))

            # Verify connection
            user_info = jira.myself()
            projects = jira.projects()

            # Create integration
            config = {
                "auth_method": "api_token",
                "server_url": server_url,
                "user_info": {
                    "key": user_info.key,
                    "name": user_info.displayName,
                    "email": user_info.emailAddress,
                },
                "sync_settings": {
                    "sync_issues": True,
                    "create_tasks_from_comments": True,
                    "bidirectional_sync": True,
                    "sync_projects": [
                        p.key for p in projects[:10]
                    ],  # Limit initial projects
                    "sync_interval_minutes": 30,
                },
                "last_sync": None,
                "webhook_url": None,
            }

            integration = self.create_integration(company_id, user_id, config)

            # Store credentials
            credentials = {
                "email": email,
                "api_token": api_token,
                "server_url": server_url,
            }
            self.store_credentials(integration.id, credentials)

            # Update status
            self.update_integration_status(integration.id, IntegrationStatus.CONNECTED)

            self.log_integration_event(
                integration.id,
                "api_token_setup_completed",
                {
                    "server_url": server_url,
                    "user_key": user_info.key,
                    "projects_count": len(projects),
                },
            )

            return self.format_success_response(
                {
                    "integration_id": str(integration.id),
                    "server_url": server_url,
                    "user_name": user_info.displayName,
                    "projects_count": len(projects),
                    "status": "connected",
                }
            )

        except JIRAError as e:
            return self.format_error_response(e, "api_token_setup")
        except Exception as e:
            return self.format_error_response(e, "api_token_setup")

    def _handle_oauth_callback(
        self, verifier: str, oauth_token: str, kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle OAuth callback"""
        try:
            # Find integration by OAuth token
            integrations = (
                self.db.query(Integration)
                .filter(
                    Integration.integration_type == self.integration_type.value,
                    Integration.config.contains(
                        {"oauth_request_token": {"oauth_token": oauth_token}}
                    ),
                )
                .all()
            )

            if not integrations:
                return self.format_error_response(
                    ValueError("Invalid OAuth state"), "oauth_callback"
                )

            integration = integrations[0]
            request_token = integration.config.get("oauth_request_token", {})

            # Complete OAuth flow
            oauth_dict = {
                "consumer_key": self.consumer_key,
                "consumer_secret": self.consumer_secret,
                "access_token": "",
                "access_token_secret": "",
                "request_token": request_token.get("oauth_token"),
                "request_token_secret": request_token.get("oauth_token_secret"),
            }

            jira = JIRA(server=self.server_url, oauth=oauth_dict)
            access_token = jira._get_oauth_access_token(verifier)

            # Store access token
            credentials = {
                "oauth_token": access_token["oauth_token"],
                "oauth_token_secret": access_token["oauth_token_secret"],
                "server_url": self.server_url,
            }
            self.store_credentials(integration.id, credentials)

            # Update integration config
            config_updates = {"auth_method": "oauth", "oauth_state": "completed"}
            self.update_integration_config(integration.id, config_updates)
            self.update_integration_status(integration.id, IntegrationStatus.CONNECTED)

            return self.format_success_response(
                {"integration_id": str(integration.id), "status": "connected"}
            )

        except Exception as e:
            return self.format_error_response(e, "oauth_callback")

    def test_connection(self, integration_id: uuid.UUID) -> Dict[str, Any]:
        """Test Jira connection"""
        try:
            jira_client = self._get_jira_client(integration_id)
            if not jira_client:
                return self.format_error_response(
                    Exception("No credentials found"), "test_connection"
                )

            # Test basic operations
            user_info = jira_client.myself()
            projects = jira_client.projects()

            return self.format_success_response(
                {
                    "user": user_info.displayName,
                    "email": getattr(user_info, "emailAddress", "N/A"),
                    "projects_count": len(projects),
                }
            )

        except JIRAError as e:
            return self.format_error_response(e, "test_connection")
        except Exception as e:
            return self.format_error_response(e, "test_connection")

    def refresh_credentials(self, integration_id: uuid.UUID) -> bool:
        """Refresh Jira credentials (mainly for OAuth)"""
        integration = self.get_integration(integration_id)
        if not integration:
            return False

        auth_method = integration.config.get("auth_method")

        if auth_method == "api_token":
            # API tokens don't expire, just test connection
            test_result = self.test_connection(integration_id)
            if test_result["success"]:
                self.update_integration_status(
                    integration_id, IntegrationStatus.CONNECTED
                )
                return True
            else:
                self.update_integration_status(integration_id, IntegrationStatus.ERROR)
                return False

        elif auth_method == "oauth":
            # OAuth tokens may need refresh (implementation depends on Jira setup)
            test_result = self.test_connection(integration_id)
            return test_result["success"]

        return False

    def disconnect(self, integration_id: uuid.UUID) -> bool:
        """Disconnect Jira integration"""
        try:
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
        """Sync data from Jira"""
        try:
            jira_client = self._get_jira_client(integration_id)
            if not jira_client:
                return self.format_error_response(
                    Exception("No Jira client"), "sync_data"
                )

            integration = self.get_integration(integration_id)
            sync_settings = integration.config.get("sync_settings", {})

            sync_results = {
                "issues_synced": 0,
                "tasks_created": 0,
                "tasks_updated": 0,
                "projects_synced": 0,
                "errors": [],
            }

            # Get projects to sync
            projects_to_sync = sync_settings.get("sync_projects", [])

            for project_key in projects_to_sync:
                try:
                    # Get project issues
                    jql_query = f"project = {project_key}"

                    # Add date filter for incremental sync
                    if sync_type == "incremental":
                        last_sync = integration.config.get("last_sync")
                        if last_sync:
                            last_sync_date = datetime.fromisoformat(
                                last_sync.replace("Z", "+00:00")
                            )
                            jql_query += f" AND updated >= '{last_sync_date.strftime('%Y-%m-%d %H:%M')}'"

                    issues = jira_client.search_issues(jql_query, maxResults=100)

                    for issue in issues:
                        try:
                            # Sync issue to Vira task
                            task_result = self._sync_jira_issue_to_task(
                                integration_id, issue
                            )
                            if task_result:
                                if task_result["action"] == "created":
                                    sync_results["tasks_created"] += 1
                                elif task_result["action"] == "updated":
                                    sync_results["tasks_updated"] += 1

                            sync_results["issues_synced"] += 1

                        except Exception as e:
                            sync_results["errors"].append(
                                f"Issue {issue.key}: {str(e)}"
                            )

                    sync_results["projects_synced"] += 1

                except JIRAError as e:
                    sync_results["errors"].append(f"Project {project_key}: {str(e)}")

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
        """Handle Jira webhook events"""
        try:
            event_type = payload.get("webhookEvent")
            issue = payload.get("issue")

            if not issue:
                return self.format_success_response(
                    {"processed": False, "reason": "No issue in payload"}
                )

            result = {"processed": True, "actions": []}

            # Handle different webhook events
            if event_type in ["jira:issue_created", "jira:issue_updated"]:
                sync_result = self._sync_jira_issue_to_task(
                    integration_id, issue, is_webhook=True
                )
                if sync_result:
                    result["actions"].append(
                        f"Task {sync_result['action']}: {sync_result.get('task_id')}"
                    )

            elif event_type == "comment_created":
                comment = payload.get("comment", {})
                comment_result = self._handle_jira_comment(
                    integration_id, issue, comment
                )
                if comment_result:
                    result["actions"].append(
                        f"Task extracted from comment: {comment_result.get('task_id')}"
                    )

            self.log_integration_event(
                integration_id,
                "webhook_processed",
                {
                    "event_type": event_type,
                    "issue_key": issue.get("key"),
                    "actions": result["actions"],
                },
            )

            return self.format_success_response(result)

        except Exception as e:
            return self.format_error_response(e, "webhook")

    # Private helper methods

    def _get_jira_client(self, integration_id: uuid.UUID) -> Optional[JIRA]:
        """Get authenticated Jira client"""
        try:
            credentials = self.get_credentials(integration_id)
            integration = self.get_integration(integration_id)

            if not credentials or not integration:
                return None

            auth_method = integration.config.get("auth_method")

            if auth_method == "api_token":
                return JIRA(
                    server=credentials["server_url"],
                    basic_auth=(credentials["email"], credentials["api_token"]),
                )

            elif auth_method == "oauth":
                oauth_dict = {
                    "consumer_key": self.consumer_key,
                    "consumer_secret": self.consumer_secret,
                    "access_token": credentials["oauth_token"],
                    "access_token_secret": credentials["oauth_token_secret"],
                }
                return JIRA(server=credentials["server_url"], oauth=oauth_dict)

            return None

        except Exception:
            return None

    def _sync_jira_issue_to_task(
        self, integration_id: uuid.UUID, issue: Any, is_webhook: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Sync Jira issue to Vira task"""
        try:
            integration = self.get_integration(integration_id)
            company_id = integration.company_id

            # Check if task already exists
            existing_task = (
                self.db.query(Task)
                .filter(
                    Task.original_prompt.contains(
                        issue.key if hasattr(issue, "key") else issue.get("key")
                    )
                )
                .first()
            )

            # Extract issue data
            issue_key = issue.key if hasattr(issue, "key") else issue.get("key")
            summary = (
                issue.fields.summary
                if hasattr(issue, "fields")
                else issue.get("fields", {}).get("summary")
            )
            description = (
                getattr(issue.fields, "description", "")
                if hasattr(issue, "fields")
                else issue.get("fields", {}).get("description", "")
            )
            status = (
                issue.fields.status.name
                if hasattr(issue, "fields")
                else issue.get("fields", {}).get("status", {}).get("name")
            )
            assignee = (
                getattr(issue.fields, "assignee", None)
                if hasattr(issue, "fields")
                else issue.get("fields", {}).get("assignee")
            )

            # Map Jira status to Vira status
            vira_status = self._map_jira_status_to_vira(status)

            # Find assignee in Vira
            vira_assignee = None
            if assignee:
                assignee_email = (
                    assignee.emailAddress
                    if hasattr(assignee, "emailAddress")
                    else assignee.get("emailAddress")
                )
                if assignee_email:
                    vira_assignee = (
                        self.db.query(User)
                        .filter(
                            User.email == assignee_email, User.company_id == company_id
                        )
                        .first()
                    )

            if existing_task:
                # Update existing task
                existing_task.name = summary
                existing_task.description = f"[Jira: {issue_key}] {description}"
                existing_task.status = vira_status
                if vira_assignee:
                    existing_task.assigned_to = vira_assignee.id
                existing_task.updated_at = datetime.utcnow()

                self.db.commit()

                return {
                    "action": "updated",
                    "task_id": str(existing_task.id),
                    "jira_key": issue_key,
                }
            else:
                # Create new task
                # Find a user to create the task (preferably PM or CEO)
                creator = (
                    self.db.query(User)
                    .filter(
                        User.company_id == company_id,
                        User.role.in_(["CEO", "PM", "Supervisor"]),
                    )
                    .first()
                )

                if not creator:
                    return None

                new_task = Task(
                    id=uuid.uuid4(),
                    name=summary,
                    description=f"[Jira: {issue_key}] {description}",
                    status=vira_status,
                    assigned_to=vira_assignee.id if vira_assignee else None,
                    created_by=creator.id,
                    original_prompt=f"Jira issue sync: {issue_key}",
                    priority="medium",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                self.db.add(new_task)
                self.db.commit()

                return {
                    "action": "created",
                    "task_id": str(new_task.id),
                    "jira_key": issue_key,
                }

        except Exception as e:
            self.log_integration_event(
                integration_id,
                "sync_issue_error",
                {
                    "error": str(e),
                    "issue_key": issue.key
                    if hasattr(issue, "key")
                    else issue.get("key", "unknown"),
                },
            )
            return None

    def _handle_jira_comment(
        self, integration_id: uuid.UUID, issue: Any, comment: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Handle Jira comment for task extraction"""
        try:
            integration = self.get_integration(integration_id)

            # Check if task extraction from comments is enabled
            if not integration.config.get("sync_settings", {}).get(
                "create_tasks_from_comments", True
            ):
                return None

            comment_body = comment.get("body", "")
            author = comment.get("author", {})

            # Use LangChain orchestrator to extract potential tasks
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
                return None

            orchestrator = LangChainOrchestrator(self.db)

            context = {
                "source": "jira_comment",
                "issue_key": issue.key if hasattr(issue, "key") else issue.get("key"),
                "comment_author": author.get("displayName", "Unknown"),
                "integration_id": str(integration_id),
            }

            # Process with orchestrator
            result = orchestrator._handle_task_management(
                user_input=comment_body, user_id=creator.id, context=context
            )

            if result and "task created" in result.lower():
                return {"task_extracted": True, "source": "jira_comment"}

            return None

        except Exception as e:
            self.log_integration_event(
                integration_id, "comment_processing_error", {"error": str(e)}
            )
            return None

    def _map_jira_status_to_vira(self, jira_status: str) -> str:
        """Map Jira status to Vira task status"""
        status_mapping = {
            "To Do": "pending",
            "Open": "pending",
            "In Progress": "in-progress",
            "In Review": "in-progress",
            "Done": "complete",
            "Closed": "complete",
            "Resolved": "complete",
            "Cancelled": "cancelled",
        }

        return status_mapping.get(jira_status, "pending")

    # Public API methods

    def get_projects(self, integration_id: uuid.UUID) -> Dict[str, Any]:
        """Get Jira projects"""
        try:
            jira_client = self._get_jira_client(integration_id)
            if not jira_client:
                return self.format_error_response(
                    Exception("No Jira client"), "get_projects"
                )

            projects = jira_client.projects()

            project_list = [
                {
                    "key": p.key,
                    "name": p.name,
                    "description": getattr(p, "description", ""),
                    "lead": getattr(p, "lead", {}).get("displayName", "N/A")
                    if hasattr(p, "lead")
                    else "N/A",
                }
                for p in projects
            ]

            return self.format_success_response(project_list)

        except Exception as e:
            return self.format_error_response(e, "get_projects")

    def create_jira_issue(
        self, integration_id: uuid.UUID, project_key: str, issue_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create issue in Jira"""
        try:
            jira_client = self._get_jira_client(integration_id)
            if not jira_client:
                return self.format_error_response(
                    Exception("No Jira client"), "create_issue"
                )

            issue_dict = {
                "project": {"key": project_key},
                "summary": issue_data.get("summary", "New issue from Vira"),
                "description": issue_data.get("description", ""),
                "issuetype": {"name": issue_data.get("issue_type", "Task")},
            }

            # Add assignee if provided
            if issue_data.get("assignee"):
                issue_dict["assignee"] = {"name": issue_data["assignee"]}

            new_issue = jira_client.create_issue(fields=issue_dict)

            return self.format_success_response(
                {
                    "issue_key": new_issue.key,
                    "issue_url": f"{jira_client._options['server']}/browse/{new_issue.key}",
                }
            )

        except Exception as e:
            return self.format_error_response(e, "create_issue")

    def get_consolidated_report(
        self, integration_id: uuid.UUID, project_keys: List[str] = None
    ) -> Dict[str, Any]:
        """Get consolidated report combining Vira and Jira data"""
        try:
            jira_client = self._get_jira_client(integration_id)
            integration = self.get_integration(integration_id)

            if not jira_client or not integration:
                return self.format_error_response(
                    Exception("Integration not available"), "consolidated_report"
                )

            company_id = integration.company_id

            # Get Vira tasks
            vira_tasks = self.db.query(Task).filter(Task.company_id == company_id).all()

            # Get Jira issues
            jira_issues = []
            projects = project_keys or integration.config.get("sync_settings", {}).get(
                "sync_projects", []
            )

            for project_key in projects:
                try:
                    issues = jira_client.search_issues(
                        f"project = {project_key}", maxResults=100
                    )
                    for issue in issues:
                        jira_issues.append(
                            {
                                "key": issue.key,
                                "summary": issue.fields.summary,
                                "status": issue.fields.status.name,
                                "assignee": issue.fields.assignee.displayName
                                if issue.fields.assignee
                                else None,
                                "created": str(issue.fields.created),
                                "updated": str(issue.fields.updated),
                            }
                        )
                except JIRAError:
                    continue

            # Compile report
            report = {
                "vira_tasks": {
                    "total": len(vira_tasks),
                    "by_status": {},
                    "tasks": [
                        {
                            "id": str(task.id),
                            "name": task.name,
                            "status": task.status,
                            "created_at": task.created_at.isoformat(),
                            "is_jira_synced": "Jira:" in (task.original_prompt or ""),
                        }
                        for task in vira_tasks
                    ],
                },
                "jira_issues": {
                    "total": len(jira_issues),
                    "by_status": {},
                    "issues": jira_issues,
                },
                "sync_status": {
                    "last_sync": integration.config.get("last_sync"),
                    "integration_status": integration.config.get("status"),
                },
            }

            # Calculate status distributions
            for task in vira_tasks:
                status = task.status
                report["vira_tasks"]["by_status"][status] = (
                    report["vira_tasks"]["by_status"].get(status, 0) + 1
                )

            for issue in jira_issues:
                status = issue["status"]
                report["jira_issues"]["by_status"][status] = (
                    report["jira_issues"]["by_status"].get(status, 0) + 1
                )

            return self.format_success_response(report)

        except Exception as e:
            return self.format_error_response(e, "consolidated_report")
