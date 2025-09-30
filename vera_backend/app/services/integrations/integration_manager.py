"""
Integration Manager
Central manager for all third-party integrations in Vira
"""

import uuid
from typing import Any, Dict, List, Optional, Type

from sqlalchemy.orm import Session

from app.models.sql_models import Company, Integration, User

from .base_integration import BaseIntegrationService, IntegrationType
from .google_integration import GoogleIntegrationService
from .jira_integration import JiraIntegrationService
from .microsoft_integration import MicrosoftIntegrationService
from .slack_integration import SlackIntegrationService


class IntegrationManager:
    """
    Central manager for all integration services.
    Provides a unified interface for managing third-party integrations.
    """

    def __init__(self, db: Session):
        self.db = db
        self._services: Dict[IntegrationType, BaseIntegrationService] = {}
        self._initialize_services()

    def _initialize_services(self):
        """Initialize all available integration services"""
        service_classes = {
            IntegrationType.SLACK: SlackIntegrationService,
            IntegrationType.JIRA: JiraIntegrationService,
            IntegrationType.GOOGLE_CALENDAR: GoogleIntegrationService,
            IntegrationType.MICROSOFT_TEAMS: MicrosoftIntegrationService,
        }

        for integration_type, service_class in service_classes.items():
            try:
                self._services[integration_type] = service_class(self.db)
            except Exception as e:
                # Log error but continue with other services
                print(
                    f"Failed to initialize {integration_type.value} service: {str(e)}"
                )

    def get_service(
        self, integration_type: IntegrationType
    ) -> Optional[BaseIntegrationService]:
        """Get integration service by type"""
        return self._services.get(integration_type)

    def get_available_integrations(self) -> List[Dict[str, Any]]:
        """Get list of all available integration types"""
        integrations = []

        for integration_type, service in self._services.items():
            integrations.append(
                {
                    "type": integration_type.value,
                    "name": self._get_integration_display_name(integration_type),
                    "description": self._get_integration_description(integration_type),
                    "features": self._get_integration_features(integration_type),
                    "available": True,
                }
            )

        return integrations

    def get_company_integrations(self, company_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get all integrations for a company with their status"""
        integrations = (
            self.db.query(Integration)
            .filter(Integration.company_id == company_id, Integration.enabled == True)
            .all()
        )

        result = []
        for integration in integrations:
            service = self.get_service(IntegrationType(integration.integration_type))

            integration_data = {
                "id": str(integration.id),
                "type": integration.integration_type,
                "name": self._get_integration_display_name(
                    IntegrationType(integration.integration_type)
                ),
                "status": integration.config.get("status", "unknown"),
                "created_at": integration.created_at.isoformat(),
                "updated_at": integration.updated_at.isoformat(),
                "config": self._sanitize_config_for_display(integration.config),
                "healthy": service.is_integration_healthy(integration)
                if service
                else False,
            }

            result.append(integration_data)

        return result

    def create_integration(
        self,
        integration_type: IntegrationType,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Create a new integration"""
        service = self.get_service(integration_type)
        if not service:
            return {
                "success": False,
                "error": f"Integration type {integration_type.value} not available",
            }

        try:
            integration = service.create_integration(
                company_id=company_id, user_id=user_id, config=config or {}
            )

            return {
                "success": True,
                "integration_id": str(integration.id),
                "type": integration_type.value,
                "status": integration.config.get("status", "pending"),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_authorization_url(
        self,
        integration_type: IntegrationType,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        redirect_uri: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get OAuth authorization URL for an integration"""
        service = self.get_service(integration_type)
        if not service:
            return {
                "success": False,
                "error": f"Integration type {integration_type.value} not available",
            }

        try:
            auth_url = service.get_authorization_url(
                company_id=company_id,
                user_id=user_id,
                redirect_uri=redirect_uri,
                **kwargs,
            )

            return {
                "success": True,
                "authorization_url": auth_url,
                "type": integration_type.value,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def handle_oauth_callback(
        self, integration_type: IntegrationType, code: str, state: str, **kwargs
    ) -> Dict[str, Any]:
        """Handle OAuth callback for an integration"""
        service = self.get_service(integration_type)
        if not service:
            return {
                "success": False,
                "error": f"Integration type {integration_type.value} not available",
            }

        return service.handle_oauth_callback(code=code, state=state, **kwargs)

    def test_integration(self, integration_id: uuid.UUID) -> Dict[str, Any]:
        """Test an integration connection"""
        integration = self._get_integration_with_service(integration_id)
        if not integration:
            return {"success": False, "error": "Integration not found"}

        service, integration_record = integration
        return service.test_connection(integration_id)

    def refresh_integration_credentials(
        self, integration_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Refresh integration credentials"""
        integration = self._get_integration_with_service(integration_id)
        if not integration:
            return {"success": False, "error": "Integration not found"}

        service, integration_record = integration
        success = service.refresh_credentials(integration_id)

        return {
            "success": success,
            "message": "Credentials refreshed successfully"
            if success
            else "Failed to refresh credentials",
        }

    def disconnect_integration(self, integration_id: uuid.UUID) -> Dict[str, Any]:
        """Disconnect an integration"""
        integration = self._get_integration_with_service(integration_id)
        if not integration:
            return {"success": False, "error": "Integration not found"}

        service, integration_record = integration
        success = service.disconnect(integration_id)

        return {
            "success": success,
            "message": "Integration disconnected successfully"
            if success
            else "Failed to disconnect integration",
        }

    def sync_integration_data(
        self, integration_id: uuid.UUID, sync_type: str = "full"
    ) -> Dict[str, Any]:
        """Sync data for an integration"""
        integration = self._get_integration_with_service(integration_id)
        if not integration:
            return {"success": False, "error": "Integration not found"}

        service, integration_record = integration
        return service.sync_data(integration_id, sync_type)

    def handle_webhook(
        self,
        integration_type: IntegrationType,
        integration_id: uuid.UUID,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Handle webhook for an integration"""
        service = self.get_service(integration_type)
        if not service:
            return {
                "success": False,
                "error": f"Integration type {integration_type.value} not available",
            }

        return service.handle_webhook(integration_id, payload, headers)

    def get_integration_stats(self, company_id: uuid.UUID) -> Dict[str, Any]:
        """Get integration statistics for a company"""
        integrations = (
            self.db.query(Integration)
            .filter(Integration.company_id == company_id)
            .all()
        )

        stats = {
            "total_integrations": len(integrations),
            "active_integrations": 0,
            "by_type": {},
            "by_status": {},
            "health_summary": {"healthy": 0, "unhealthy": 0, "unknown": 0},
        }

        for integration in integrations:
            integration_type = integration.integration_type
            status = integration.config.get("status", "unknown")

            # Count by type
            stats["by_type"][integration_type] = (
                stats["by_type"].get(integration_type, 0) + 1
            )

            # Count by status
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            # Count active integrations
            if integration.enabled and status == "connected":
                stats["active_integrations"] += 1

            # Health check
            service = self.get_service(IntegrationType(integration_type))
            if service:
                if service.is_integration_healthy(integration):
                    stats["health_summary"]["healthy"] += 1
                else:
                    stats["health_summary"]["unhealthy"] += 1
            else:
                stats["health_summary"]["unknown"] += 1

        return stats

    def sync_all_company_integrations(
        self, company_id: uuid.UUID, sync_type: str = "incremental"
    ) -> Dict[str, Any]:
        """Sync all integrations for a company"""
        integrations = (
            self.db.query(Integration)
            .filter(Integration.company_id == company_id, Integration.enabled == True)
            .all()
        )

        results = {
            "total_integrations": len(integrations),
            "successful_syncs": 0,
            "failed_syncs": 0,
            "sync_results": [],
        }

        for integration in integrations:
            service = self.get_service(IntegrationType(integration.integration_type))
            if not service:
                continue

            # Only sync healthy integrations
            if not service.is_integration_healthy(integration):
                continue

            try:
                sync_result = service.sync_data(integration.id, sync_type)

                if sync_result.get("success", False):
                    results["successful_syncs"] += 1
                else:
                    results["failed_syncs"] += 1

                results["sync_results"].append(
                    {
                        "integration_id": str(integration.id),
                        "type": integration.integration_type,
                        "success": sync_result.get("success", False),
                        "data": sync_result.get("data", {}),
                        "error": sync_result.get("error"),
                    }
                )

            except Exception as e:
                results["failed_syncs"] += 1
                results["sync_results"].append(
                    {
                        "integration_id": str(integration.id),
                        "type": integration.integration_type,
                        "success": False,
                        "error": str(e),
                    }
                )

        return results

    def get_integration_events(
        self, integration_id: uuid.UUID, limit: int = 50
    ) -> Dict[str, Any]:
        """Get recent events for an integration"""
        integration = (
            self.db.query(Integration).filter(Integration.id == integration_id).first()
        )
        if not integration:
            return {"success": False, "error": "Integration not found"}

        events = integration.config.get("events", [])

        # Return most recent events
        recent_events = events[-limit:] if len(events) > limit else events

        return {"success": True, "events": recent_events, "total_events": len(events)}

    def update_integration_config(
        self, integration_id: uuid.UUID, config_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update integration configuration"""
        integration = self._get_integration_with_service(integration_id)
        if not integration:
            return {"success": False, "error": "Integration not found"}

        service, integration_record = integration
        success = service.update_integration_config(integration_id, config_updates)

        return {
            "success": success,
            "message": "Configuration updated successfully"
            if success
            else "Failed to update configuration",
        }

    # Private helper methods

    def _get_integration_with_service(
        self, integration_id: uuid.UUID
    ) -> Optional[tuple]:
        """Get integration record and its service"""
        integration = (
            self.db.query(Integration).filter(Integration.id == integration_id).first()
        )
        if not integration:
            return None

        service = self.get_service(IntegrationType(integration.integration_type))
        if not service:
            return None

        return service, integration

    def _get_integration_display_name(self, integration_type: IntegrationType) -> str:
        """Get display name for integration type"""
        display_names = {
            IntegrationType.SLACK: "Slack",
            IntegrationType.JIRA: "Jira",
            IntegrationType.GITHUB: "GitHub",
            IntegrationType.GOOGLE_CALENDAR: "Google Calendar & Drive",
            IntegrationType.GOOGLE_DRIVE: "Google Drive",
            IntegrationType.MICROSOFT_TEAMS: "Microsoft Teams & Outlook",
            IntegrationType.MICROSOFT_OUTLOOK: "Microsoft Outlook",
            IntegrationType.DROPBOX: "Dropbox",
            IntegrationType.TRELLO: "Trello",
        }

        return display_names.get(
            integration_type, integration_type.value.replace("_", " ").title()
        )

    def _get_integration_description(self, integration_type: IntegrationType) -> str:
        """Get description for integration type"""
        descriptions = {
            IntegrationType.SLACK: "Connect Slack workspaces to ingest messages, extract tasks, and send notifications",
            IntegrationType.JIRA: "Sync Jira issues with Vira tasks and create consolidated reports",
            IntegrationType.GITHUB: "Extract tasks from GitHub issues and pull request comments",
            IntegrationType.GOOGLE_CALENDAR: "Sync Google Calendar events and Google Drive documents for task creation and document processing",
            IntegrationType.GOOGLE_DRIVE: "Process and index Google Drive documents for Q&A and task extraction",
            IntegrationType.MICROSOFT_TEAMS: "Integrate with Microsoft Teams and Outlook for message processing and calendar sync",
            IntegrationType.MICROSOFT_OUTLOOK: "Sync Outlook calendar events and process emails for task extraction",
            IntegrationType.DROPBOX: "Access and process Dropbox files for document intelligence",
            IntegrationType.TRELLO: "Sync Trello boards and cards with Vira tasks",
        }

        return descriptions.get(
            integration_type, f"Integration with {integration_type.value}"
        )

    def _get_integration_features(self, integration_type: IntegrationType) -> List[str]:
        """Get feature list for integration type"""
        features = {
            IntegrationType.SLACK: [
                "Message ingestion from channels and DMs",
                "Task extraction from @Vira mentions",
                "Inline replies and notifications",
                "Webhook support for real-time updates",
            ],
            IntegrationType.JIRA: [
                "Issue data sync with Vira tasks",
                "Bi-directional status updates",
                "Task creation from comments",
                "Consolidated reporting",
            ],
            IntegrationType.GOOGLE_CALENDAR: [
                "Calendar event sync",
                "Task creation from meetings",
                "Google Drive document processing",
                "Document Q&A capabilities",
            ],
            IntegrationType.MICROSOFT_TEAMS: [
                "Teams message processing",
                "Outlook calendar integration",
                "Meeting summarization",
                "Email task extraction",
            ],
        }

        return features.get(integration_type, ["Basic integration functionality"])

    def _sanitize_config_for_display(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from config for display"""
        if not config:
            return {}

        # Create a copy and remove sensitive keys
        sanitized = config.copy()

        sensitive_keys = [
            "credentials",
            "access_token",
            "refresh_token",
            "api_token",
            "client_secret",
            "private_key",
            "oauth_token_secret",
        ]

        for key in sensitive_keys:
            if key in sanitized:
                sanitized[key] = "[REDACTED]"

        # Recursively sanitize nested dictionaries
        for key, value in sanitized.items():
            if isinstance(value, dict):
                sanitized[key] = self._sanitize_config_for_display(value)

        return sanitized
