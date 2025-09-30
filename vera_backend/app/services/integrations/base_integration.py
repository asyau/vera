"""
Base Integration Service
Abstract base class for all third-party integrations in Vira
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from app.models.sql_models import Company, Integration, User


class IntegrationType(Enum):
    """Supported integration types"""

    SLACK = "slack"
    JIRA = "jira"
    GITHUB = "github"
    GOOGLE_CALENDAR = "google_calendar"
    GOOGLE_DRIVE = "google_drive"
    MICROSOFT_TEAMS = "microsoft_teams"
    MICROSOFT_OUTLOOK = "microsoft_outlook"
    DROPBOX = "dropbox"
    TRELLO = "trello"


class IntegrationStatus(Enum):
    """Integration status states"""

    PENDING = "pending"
    CONNECTED = "connected"
    ERROR = "error"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"


class BaseIntegrationService(ABC):
    """Abstract base class for all integration services"""

    def __init__(self, db: Session):
        self.db = db
        self.integration_type = self._get_integration_type()

    @abstractmethod
    def _get_integration_type(self) -> IntegrationType:
        """Return the integration type for this service"""
        pass

    @abstractmethod
    def get_authorization_url(
        self, company_id: uuid.UUID, user_id: uuid.UUID, redirect_uri: str, **kwargs
    ) -> str:
        """Generate OAuth authorization URL for this integration"""
        pass

    @abstractmethod
    def handle_oauth_callback(self, code: str, state: str, **kwargs) -> Dict[str, Any]:
        """Handle OAuth callback and store credentials"""
        pass

    @abstractmethod
    def test_connection(self, integration_id: uuid.UUID) -> Dict[str, Any]:
        """Test if the integration connection is working"""
        pass

    @abstractmethod
    def refresh_credentials(self, integration_id: uuid.UUID) -> bool:
        """Refresh expired OAuth credentials"""
        pass

    @abstractmethod
    def disconnect(self, integration_id: uuid.UUID) -> bool:
        """Disconnect and cleanup the integration"""
        pass

    @abstractmethod
    def sync_data(
        self, integration_id: uuid.UUID, sync_type: str = "full"
    ) -> Dict[str, Any]:
        """Sync data from the external service"""
        pass

    @abstractmethod
    def handle_webhook(
        self,
        integration_id: uuid.UUID,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Handle incoming webhook from the external service"""
        pass

    # Common helper methods

    def create_integration(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        config: Dict[str, Any],
        status: IntegrationStatus = IntegrationStatus.PENDING,
    ) -> Integration:
        """Create a new integration record"""
        integration = Integration(
            id=uuid.uuid4(),
            company_id=company_id,
            integration_type=self.integration_type.value,
            config=config,
            enabled=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Add initial status to config
        integration.config["status"] = status.value
        integration.config["created_by"] = str(user_id)

        self.db.add(integration)
        self.db.commit()
        self.db.refresh(integration)

        return integration

    def get_integration(self, integration_id: uuid.UUID) -> Optional[Integration]:
        """Get integration by ID"""
        return (
            self.db.query(Integration).filter(Integration.id == integration_id).first()
        )

    def get_company_integrations(self, company_id: uuid.UUID) -> List[Integration]:
        """Get all integrations for a company"""
        return (
            self.db.query(Integration)
            .filter(
                Integration.company_id == company_id,
                Integration.integration_type == self.integration_type.value,
            )
            .all()
        )

    def update_integration_config(
        self, integration_id: uuid.UUID, config_updates: Dict[str, Any]
    ) -> bool:
        """Update integration configuration"""
        integration = self.get_integration(integration_id)
        if not integration:
            return False

        # Merge config updates
        if integration.config:
            integration.config.update(config_updates)
        else:
            integration.config = config_updates

        integration.updated_at = datetime.utcnow()

        self.db.commit()
        return True

    def update_integration_status(
        self,
        integration_id: uuid.UUID,
        status: IntegrationStatus,
        error_message: str = None,
    ) -> bool:
        """Update integration status"""
        config_updates = {
            "status": status.value,
            "last_status_update": datetime.utcnow().isoformat(),
        }

        if error_message:
            config_updates["last_error"] = error_message

        return self.update_integration_config(integration_id, config_updates)

    def is_integration_healthy(self, integration: Integration) -> bool:
        """Check if integration is in a healthy state"""
        if not integration or not integration.enabled:
            return False

        status = integration.config.get("status")
        return status == IntegrationStatus.CONNECTED.value

    def get_credentials(self, integration_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get stored credentials for an integration"""
        integration = self.get_integration(integration_id)
        if not integration:
            return None

        return integration.config.get("credentials", {})

    def store_credentials(
        self, integration_id: uuid.UUID, credentials: Dict[str, Any]
    ) -> bool:
        """Store OAuth credentials securely"""
        config_updates = {
            "credentials": credentials,
            "credentials_updated_at": datetime.utcnow().isoformat(),
        }

        return self.update_integration_config(integration_id, config_updates)

    def log_integration_event(
        self, integration_id: uuid.UUID, event_type: str, details: Dict[str, Any] = None
    ):
        """Log integration events for debugging and monitoring"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "integration_type": self.integration_type.value,
            "details": details or {},
        }

        # Store in integration config events log (keep last 50 events)
        integration = self.get_integration(integration_id)
        if integration:
            events = integration.config.get("events", [])
            events.append(event)

            # Keep only last 50 events
            if len(events) > 50:
                events = events[-50:]

            self.update_integration_config(integration_id, {"events": events})

    def validate_webhook_signature(
        self, payload: bytes, signature: str, secret: str
    ) -> bool:
        """Validate webhook signature (override in specific integrations)"""
        # Base implementation - override in specific integrations
        return True

    def format_error_response(
        self, error: Exception, context: str = None
    ) -> Dict[str, Any]:
        """Format error response consistently"""
        return {
            "success": False,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "context": context,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    def format_success_response(
        self, data: Any = None, message: str = None
    ) -> Dict[str, Any]:
        """Format success response consistently"""
        response = {"success": True, "timestamp": datetime.utcnow().isoformat()}

        if data is not None:
            response["data"] = data

        if message:
            response["message"] = message

        return response
