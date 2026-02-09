import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Program
    PROJECT_NAME: str = "Board API"
    VERSION: str = "1.0.0"
    TESTING: bool = False

    # DB
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/board"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Other
    USE_VIEWS_COUNTER_CACHE: bool = True


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()