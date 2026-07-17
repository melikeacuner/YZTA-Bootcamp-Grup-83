from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Uygulama genelinde kullanılan ortam ayarları (.env üzerinden okunur)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Proby AI"
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+asyncpg://proby:proby@localhost:5432/proby",
        description="SQLAlchemy async bağlantı dizesi",
    )

    redis_url: str = Field(default="redis://localhost:6379/0")

    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_collection: str = Field(default="problem_records")

    jwt_secret_key: str = Field(default="change-me-in-env")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=60)

    gemini_api_key: str | None = Field(default=None)
    gemini_llm_model: str = Field(default="gemini-1.5-flash")
    gemini_embedding_model: str = Field(default="text-embedding-004")
    embedding_dimension: int = Field(default=768)
    llm_timeout_seconds: float = Field(default=3.0)

    rag_similarity_threshold: float = Field(default=0.5)
    rag_max_results: int = Field(default=10)
    search_cache_ttl_seconds: int = Field(default=300)

    embedding_max_retries: int = Field(default=3)
    embedding_retry_interval_seconds: int = Field(default=30)

    cors_allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
