from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", ".env.example"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "Finaxis"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Persistência local em arquivos JSON
    DATA_DIR: str = "data"
    BACKUP_DIR: str = "backups"

    CORS_ORIGINS: List[str] = ["*"]

    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    FRONTEND_DIR: str = "frontend"

    # Horizonte em dias para gerar lançamentos recorrentes
    RECURRING_LOOKAHEAD_DAYS: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()