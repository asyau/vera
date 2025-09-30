"""
Integration Services for Vira
Comprehensive third-party integrations as specified in RFC Section 13
"""

from .base_integration import BaseIntegrationService
from .google_integration import GoogleIntegrationService
from .integration_manager import IntegrationManager
from .jira_integration import JiraIntegrationService
from .microsoft_integration import MicrosoftIntegrationService
from .slack_integration import SlackIntegrationService

__all__ = [
    "BaseIntegrationService",
    "SlackIntegrationService",
    "JiraIntegrationService",
    "GoogleIntegrationService",
    "MicrosoftIntegrationService",
    "IntegrationManager",
]
