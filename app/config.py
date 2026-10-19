from functools import lru_cache

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    max_bot_token: str = Field(min_length=1)
    max_api_base_url: AnyHttpUrl = "https://platform-api2.max.ru"
    max_webhook_secret: str = Field(min_length=5, max_length=256)
    webhook_path: str = "/webhook/max"
    app_host: str = "0.0.0.0"
    app_port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"
    public_base_url: str = ""

    @field_validator("max_webhook_secret")
    @classmethod
    def secret_characters(cls, value: str) -> str:
        if not all(char.isascii() and (char.isalnum() or char in "_-") for char in value):
            raise ValueError("MAX_WEBHOOK_SECRET may contain only A-Z, a-z, 0-9, _ and -")
        return value

    @field_validator("webhook_path")
    @classmethod
    def webhook_path_is_relative(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("WEBHOOK_PATH must begin with /")
        return value.rstrip("/") or "/"


@lru_cache
def get_settings() -> Settings:
    return Settings()

