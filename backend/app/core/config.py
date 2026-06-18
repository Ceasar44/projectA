from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Owly Backend"
    environment: str = Field(default="development", alias="APP_ENV")
    api_v1_prefix: str = "/api"
    database_url: str = Field(default="postgresql://postgres:postgres@localhost:5432/owly", alias="DATABASE_URL")
    jwt_secret: str = Field(default="dev-secret-change-me", alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    log_level: str = "INFO"
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    webhook_secret: str = Field(default="change-me", alias="WEBHOOK_SECRET")
    auto_create_schema: bool = Field(default=False, alias="AUTO_CREATE_SCHEMA")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
