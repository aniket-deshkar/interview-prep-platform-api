from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    app_name: str = "Interview Prep Platform API"
    environment: Literal["local", "test", "staging", "production"] = "local"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    secret_key: SecretStr = SecretStr("development-only-secret-key-change-me")
    token_encryption_key: SecretStr = SecretStr("")
    access_token_ttl_minutes: int = 30
    refresh_token_ttl_days: int = 30

    database_url: str = (
        "postgresql+asyncpg://interview_prep:interview_prep@localhost:5432/interview_prep"
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    s3_endpoint_url: str | None = "http://localhost:9000"
    s3_access_key_id: SecretStr = SecretStr("minioadmin")
    s3_secret_access_key: SecretStr = SecretStr("minioadmin")
    s3_bucket: str = "resumes"
    s3_region: str = "ap-south-1"

    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-5.4-mini"
    embedding_model: str = "text-embedding-3-small"

    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    microsoft_client_id: str = ""
    microsoft_client_secret: SecretStr = SecretStr("")
    oauth_redirect_base_url: str = "http://localhost:8000/api/v1/integrations"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @field_validator("api_v1_prefix")
    @classmethod
    def prefix_must_start_with_slash(cls, value: str) -> str:
        return value if value.startswith("/") else f"/{value}"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
