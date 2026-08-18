"""Runtime configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings shared by the local API and future pipelines."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="MERCURY_", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"
    model_version: str = "unconfigured"
    redis_url: str = "redis://localhost:6379/0"
    mlflow_tracking_uri: str = "http://localhost:5000"
    postgres_dsn: str = "postgresql://mercury:mercury@localhost:5432/mercury"


@lru_cache
def get_settings() -> Settings:
    """Return one immutable settings object per process."""

    return Settings()
