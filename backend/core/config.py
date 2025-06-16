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
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL")
    GOOGLE_GENAI_USE_VERTEXAI: bool = False
    
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