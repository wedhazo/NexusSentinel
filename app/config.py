"""
Configuration module for NexusSentinel API.

This module uses Pydantic Settings to load and validate environment variables.
Environment variables are loaded from .env file if present.
"""

from typing import List, Optional, Union, Any
from pydantic import (
    AnyHttpUrl,
    PostgresDsn,
    field_validator,
    model_validator,
    Field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path
import json


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # Project metadata
    PROJECT_NAME: str = "NexusSentinel"
    API_TITLE: str = "NexusSentinel API"
    API_DESCRIPTION: str = "Stock Market Sentiment Analysis API"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API Server settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_RELOAD: bool = True
    
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "your_password_here"
    DB_NAME: str = "nexussentinel"
    DB_SCHEMA: str = "public"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False
    
    # Database URL (constructed or direct)
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @model_validator(mode='after')
    def assemble_db_url(self) -> 'Settings':
        """Construct DATABASE_URL if not provided directly."""
        if not self.DATABASE_URL:
            self.DATABASE_URL = PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.DB_USER,
                password=self.DB_PASSWORD,
                host=self.DB_HOST,
                port=self.DB_PORT,
                path=f"/{self.DB_NAME}",
            )
        return self
    
    # Security settings
    SECRET_KEY: str = "replace_with_secure_generated_key_at_least_32_chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS settings
    # Accept either a raw comma-separated string **or** a JSON / Python list.
    # We store the default as a simple string so it follows the same parsing
    # path as values coming from the environment, preventing early JSON-decode
    # errors raised by pydantic when the env value is not valid JSON.
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:8080"
    
    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS_ORIGINS from string to list if needed."""
        # Accept multiple formats:
        # 1. Comma-separated string -> "http://a.com,http://b.com"
        # 2. JSON-style list  -> '["http://a.com","http://b.com"]'
        # 3. Already a Python list
        if isinstance(v, list):
            # Already the correct type
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            # JSON list string
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError as err:
                    raise ValueError(f"Invalid JSON for CORS_ORIGINS: {err}") from err
            # Comma-separated string
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        # Any other type is unsupported
        raise ValueError("CORS_ORIGINS must be a list or string")
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: int = 100
    RATE_LIMIT_PERIOD_SECONDS: int = 60
    
    # Logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "logs/nexussentinel.log"
    
    # External services
    SENTIMENT_API_KEY: Optional[str] = None
    MARKET_DATA_API_URL: Optional[AnyHttpUrl] = None
    MARKET_DATA_API_KEY: Optional[str] = None
    # Polygon.io API key for daily OHLCV ingestion
    POLYGON_API_KEY: Optional[str] = None
    
    # Feature flags
    ENABLE_SENTIMENT_ANALYSIS: bool = True
    ENABLE_TECHNICAL_INDICATORS: bool = True
    ENABLE_SOCIAL_MEDIA_TRACKING: bool = True
    ENABLE_NEWS_TRACKING: bool = True
    
    # Project paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    
    # Pydantic settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Create global settings instance
settings = Settings()
