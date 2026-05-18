from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "jingli-ai-guide"
    app_env: str = "development"
    app_debug: bool = True
    api_prefix: str = "/api"
    cors_origins_raw: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        alias="CORS_ORIGINS",
    )

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ecommerce_ai"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "product_knowledge"

    llm_provider: str = "mock"
    llm_model: str = "mock-guide"
    llm_api_key: str = ""
    llm_base_url: str = ""
    embedding_model: str = "mock-embedding"
    vision_model: str = "mock-vision"

    upload_dir: str = "storage/uploads"
    max_upload_mb: int = 50
    seed_products_path: str = "../storage/sample_docs/seed_products.json"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
