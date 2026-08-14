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

    # CORS — comma-separated list of allowed origins. Fallback to production Vercel URL if EnvVar is missing.
    CORS_ORIGINS: str = "https://scaler-nexa-chat-qnch.vercel.app,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        # Strip whitespace and explicitly remove banned wildcards (*)
        user_origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip() and o.strip() != "*"]
        # BRUTE FORCE FALLBACK: Always allow the production Vercel app regardless of Render settings
        if "https://scaler-nexa-chat-qnch.vercel.app" not in user_origins:
            user_origins.append("https://scaler-nexa-chat-qnch.vercel.app")
        return user_origins

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
