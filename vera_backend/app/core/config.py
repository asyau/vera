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

    # External APIs
    elevenlabs_api_key: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
    google_cloud_api_key: Optional[str] = os.getenv("GOOGLE_CLOUD_API_KEY")
    slack_api_token: Optional[str] = os.getenv("SLACK_API_TOKEN")
    teams_api_token: Optional[str] = os.getenv("TEAMS_API_TOKEN")

    # File Storage
    max_file_size_mb: int = 50
    allowed_file_types: list = [".pdf", ".doc", ".docx", ".txt", ".md"]

    # Redis (for caching and real-time features)
    redis_url: Optional[str] = os.getenv("REDIS_URL")

    # Microservices
    api_gateway_host: str = os.getenv("API_GATEWAY_HOST", "localhost")
    api_gateway_port: int = int(os.getenv("API_GATEWAY_PORT", "8000"))

    # Vector Database
    vector_dimensions: int = 1536  # OpenAI embeddings dimension

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()
