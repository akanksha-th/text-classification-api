from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent 
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App metadata
    APP_NAME: str = "Social Sentiment API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # API keys
    API_SERVICE_NAME: str = "youtube"
    API_VERSION: str = "v3"
    YOUTUBE_API_KEY: str | None = None

    # Model Settings
    SENTIMENT_MODEL: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    MAX_LENGTH: int = 512
    BATCH_SIZE: int = 32

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 3600

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 10

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()       # ensures the settings are loaded only once
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


if __name__ == "__main__":
    print(f"Looking for .env at: {ENV_PATH}")
    print(f"File exists: {ENV_PATH.exists()}")

    settings = get_settings()
    print(f"API Key loaded: {settings.YOUTUBE_API_KEY[:10]}...")
    print(f"App Name: {settings.APP_NAME}")
    print(f"Debug: {settings.DEBUG}")