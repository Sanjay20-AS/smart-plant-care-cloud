"""
Application configuration using Pydantic settings.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Supabase configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Database configuration
    # Defaults to SQLite for local development; set DATABASE_URL to use PostgreSQL
    DATABASE_URL: str = "sqlite:///./smartplant.db"

    # API configuration
    API_PREFIX: str = "/api/v1"
    API_TITLE: str = "Smart Plant Care API"
    API_VERSION: str = "1.0.0"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
