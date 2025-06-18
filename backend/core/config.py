"""Application configuration module."""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Extractra"
    VERSION: str = "0.1.0"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # LLM Configuration
    PD_GEMINI_MODEL: str = os.getenv("PD_GEMINI_MODEL", "")
    CE_GEMINI_MODEL: str = os.getenv("CE_GEMINI_MODEL", "")
    GOOGLE_GENAI_USE_VERTEXAI: bool = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", True)
    GOOGLE_CLOUD_PROJECT: Optional[str] = os.getenv("GOOGLE_CLOUD_PROJECT", "stellar-acre-233805")
    GOOGLE_CLOUD_LOCATION: Optional[str] = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    # Crawl4AI Configuration
    CRAWL4AI_TIMEOUT: int = 30
    CRAWL4AI_MAX_RETRIES: int = 3
    
    # Task Configuration
    MAX_CONCURRENT_TASKS: int = 10
    TASK_TIMEOUT: int = 3600  # 1 hour
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings() 