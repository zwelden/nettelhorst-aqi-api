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
    
    # AirGradient API Settings
    AIRGRADIENT_API_TOKEN: str
    AIRGRADIENT_API_BASE_URL: str = "https://api.airgradient.com/public/api/v1"
    
    # Historical Data Seeding Settings
    HISTORICAL_SEED_DAYS_BACK: int = 130
    HISTORICAL_SEED_BATCH_SIZE_DAYS: int = 7
    HISTORICAL_SEED_DELAY_BETWEEN_REQUESTS: float = 0.5
    HISTORICAL_SEED_DELAY_BETWEEN_LOCATIONS: float = 1.0
    HISTORICAL_SEED_VALIDATE_API_FIRST: bool = True
    
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
    
    @field_validator("HISTORICAL_SEED_DAYS_BACK")
    def validate_historical_days_back(cls, v):
        if v <= 0:
            raise ValueError("HISTORICAL_SEED_DAYS_BACK must be greater than 0")
        if v > 365:
            raise ValueError("HISTORICAL_SEED_DAYS_BACK should not exceed 365 days for performance reasons")
        return v
    
    @field_validator("HISTORICAL_SEED_BATCH_SIZE_DAYS")
    def validate_historical_batch_size(cls, v):
        if v <= 0:
            raise ValueError("HISTORICAL_SEED_BATCH_SIZE_DAYS must be greater than 0")
        return v
    
    @field_validator("HISTORICAL_SEED_DELAY_BETWEEN_REQUESTS")
    def validate_historical_request_delay(cls, v):
        if v < 0:
            raise ValueError("HISTORICAL_SEED_DELAY_BETWEEN_REQUESTS cannot be negative")
        return v
    
    @field_validator("HISTORICAL_SEED_DELAY_BETWEEN_LOCATIONS")
    def validate_historical_location_delay(cls, v):
        if v < 0:
            raise ValueError("HISTORICAL_SEED_DELAY_BETWEEN_LOCATIONS cannot be negative")
        return v


settings = Settings()