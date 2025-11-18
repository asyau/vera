"""
Core configuration settings for Vira backend
"""
import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost/vera"
    )

    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Supabase
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_key: Optional[str] = os.getenv("SUPABASE_KEY")

    # JWT
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # LangChain/LangGraph Debugging (LangSmith)
    langchain_tracing_v2: Optional[str] = os.getenv("LANGCHAIN_TRACING_V2")
    langchain_endpoint: Optional[str] = os.getenv("LANGCHAIN_ENDPOINT")
    langchain_api_key: Optional[str] = os.getenv("LANGCHAIN_API_KEY")
    langchain_project: Optional[str] = os.getenv("LANGCHAIN_PROJECT", "vira")
    langchain_verbose: Optional[str] = os.getenv("LANGCHAIN_VERBOSE")
    langchain_debug: Optional[str] = os.getenv("LANGCHAIN_DEBUG")

    # Email Configuration
    smtp_host: Optional[str] = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: Optional[str] = os.getenv("SMTP_USERNAME")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    smtp_from_email: Optional[str] = os.getenv("SMTP_FROM_EMAIL", "noreply@vira.ai")
    smtp_from_name: Optional[str] = os.getenv("SMTP_FROM_NAME", "Vira AI")

    # External APIs
    elevenlabs_api_key: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
    google_cloud_api_key: Optional[str] = os.getenv("GOOGLE_CLOUD_API_KEY")
    slack_api_token: Optional[str] = os.getenv("SLACK_API_TOKEN")
    teams_api_token: Optional[str] = os.getenv("TEAMS_API_TOKEN")

    # Slack Integration
    slack_client_id: Optional[str] = os.getenv("SLACK_CLIENT_ID")
    slack_client_secret: Optional[str] = os.getenv("SLACK_CLIENT_SECRET")
    slack_signing_secret: Optional[str] = os.getenv("SLACK_SIGNING_SECRET")
    slack_webhook_url: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")
    slack_bot_token: Optional[str] = os.getenv("SLACK_BOT_TOKEN")

    # Microsoft Integration
    microsoft_client_id: Optional[str] = os.getenv("MICROSOFT_CLIENT_ID")
    microsoft_client_secret: Optional[str] = os.getenv("MICROSOFT_CLIENT_SECRET")
    microsoft_tenant_id: Optional[str] = os.getenv("MICROSOFT_TENANT_ID")
    teams_webhook_url: Optional[str] = os.getenv("TEAMS_WEBHOOK_URL")

    # Google Integration
    google_client_secrets_file: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRETS_FILE")
    google_client_id: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")

    # Jira Integration
    jira_server_url: Optional[str] = os.getenv("JIRA_SERVER_URL")
    jira_consumer_key: Optional[str] = os.getenv("JIRA_CONSUMER_KEY")
    jira_consumer_secret: Optional[str] = os.getenv("JIRA_CONSUMER_SECRET")

    # GitHub Integration
    github_client_id: Optional[str] = os.getenv("GITHUB_CLIENT_ID")
    github_client_secret: Optional[str] = os.getenv("GITHUB_CLIENT_SECRET")

    # Push Notifications (Firebase Cloud Messaging)
    fcm_server_key: Optional[str] = os.getenv("FCM_SERVER_KEY")
    fcm_project_id: Optional[str] = os.getenv("FCM_PROJECT_ID")

    # File Storage
    max_file_size_mb: int = 50
    allowed_file_types: list = [".pdf", ".doc", ".docx", ".txt", ".md"]

    # Redis (for caching and real-time features)
    redis_url: Optional[str] = os.getenv("REDIS_URL")

    # Microservices
    api_gateway_host: str = os.getenv("API_GATEWAY_HOST", "localhost")
    api_gateway_port: int = int(os.getenv("API_GATEWAY_PORT", "8000"))

    # CORS Configuration
    cors_origins: Optional[str] = os.getenv("CORS_ORIGINS", None)  # Comma-separated list
    cors_allow_all: bool = os.getenv("CORS_ALLOW_ALL", "false").lower() == "true"

    # Vector Database
    vector_dimensions: int = 1536  # OpenAI embeddings dimension

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()
