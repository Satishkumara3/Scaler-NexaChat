"""
Application configuration.
Reads from environment variables with safe defaults for local development.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Scaler Chat API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DB_PATH: str = "./chat.db"

    # CORS — comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        # Strip whitespace and explicitly remove banned wildcards (*)
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip() and o.strip() != "*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance (singleton)."""
    return Settings()


settings = get_settings()
