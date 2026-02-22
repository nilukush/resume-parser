"""
Application configuration settings.

This module uses Pydantic Settings to load configuration from environment variables
and .env file. All sensitive configuration should come from environment variables.
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        DATABASE_URL: Async PostgreSQL connection string
        DATABASE_URL_SYNC: Synchronous PostgreSQL connection string (for Alembic)
        REDIS_URL: Redis connection string for Celery and caching
        OPENAI_API_KEY: OpenAI API key for NLP processing
        SECRET_KEY: Secret key for JWT token signing
        ENVIRONMENT: Application environment (development, staging, production)
        ALLOWED_ORIGINS: CORS allowed origins (comma-separated)
        MAX_UPLOAD_SIZE: Maximum file upload size in bytes (default 10MB)
    """

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://resumate_user:resumate_password@localhost:5433/resumate",
        description="Async PostgreSQL database URL"
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql://resumate_user:resumate_password@localhost:5433/resumate",
        description="Synchronous PostgreSQL database URL for migrations"
    )
    USE_DATABASE: bool = Field(
        default=False,
        description="Enable PostgreSQL database storage (vs in-memory)"
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # OpenAI
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key for NLP features"
    )

    # Security
    SECRET_KEY: str = Field(
        default="change-this-in-production-use-openssl-rand-hex-32",
        description="Secret key for JWT token signing"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )

    # Application
    ENVIRONMENT: str = Field(
        default="development",
        description="Application environment (development, staging, production)"
    )
    APP_NAME: str = Field(default="ResuMate", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")

    # CORS
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Comma-separated list of allowed CORS origins"
    )

    # File Upload
    MAX_UPLOAD_SIZE: int = Field(
        default=10485760,  # 10MB
        description="Maximum file upload size in bytes"
    )
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        description="Allowed MIME types for file uploads"
    )

    # Storage
    STORAGE_BACKEND: str = Field(
        default="local",
        description="Storage backend: local, s3, gcs"
    )
    AWS_ACCESS_KEY_ID: str = Field(default="", description="AWS access key for S3")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", description="AWS secret key for S3")
    AWS_S3_BUCKET: str = Field(default="", description="AWS S3 bucket name")
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")

    # Celery
    USE_CELERY: bool = Field(
        default=False,
        description="Enable Celery async task processing"
    )
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL"
    )

    # Sentry (Error Tracking)
    SENTRY_DSN: str = Field(default="", description="Sentry DSN for error tracking")
    SENTRY_ENVIRONMENT: str = Field(
        default="development",
        description="Sentry environment name"
    )

    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=20, description="Default pagination page size")
    MAX_PAGE_SIZE: int = Field(default=100, description="Maximum pagination page size")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        """Validate CORS origins are properly formatted."""
        if isinstance(v, str):
            return v
        return ",".join(v) if isinstance(v, list) else str(v)

    @property
    def allowed_origins_list(self) -> List[str]:
        """Return CORS origins as a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() in ("development", "dev")

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() in ("production", "prod")

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.ENVIRONMENT.lower() in ("testing", "test")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This function caches the settings instance to avoid repeated loading
    from environment variables. The cache is created per-settings instance.

    Returns:
        Settings: The application settings instance
    """
    return Settings()


def clear_settings_cache() -> None:
    """
    Clear the cached settings instance.

    This function clears the LRU cache for get_settings(), forcing a reload
    of environment variables on the next call to get_settings().

    Use this in tests to reset settings between test runs when using
    monkeypatch.setenv() to change environment variables.

    Example:
        monkeypatch.setenv("USE_DATABASE", "false")
        clear_settings_cache()
        settings = get_settings()  # Will reload with new env vars
    """
    get_settings.cache_clear()


# Global settings instance
settings = get_settings()
