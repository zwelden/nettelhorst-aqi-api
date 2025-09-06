from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, field_validator
import os


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    DATABASE_URL: PostgresDsn
    DATABASE_URL_ASYNC: Optional[str] = None
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    SCHEDULER_TIMEZONE: str = "UTC"
    SCHEDULER_JOB_DEFAULTS_COALESCE: bool = False
    SCHEDULER_JOB_DEFAULTS_MAX_INSTANCES: int = 1
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @field_validator("DATABASE_URL")
    def validate_database_url(cls, v):
        return str(v)
    
    @field_validator("DATABASE_URL_ASYNC")
    def validate_async_database_url(cls, v, values):
        if v is None and "DATABASE_URL" in values.data:
            sync_url = str(values.data["DATABASE_URL"])
            return sync_url.replace("postgresql://", "postgresql+asyncpg://")
        return v


settings = Settings()