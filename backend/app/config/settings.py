from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Banco Agil API"
    app_env: str = "development"
    debug: bool = True

    groq_api_key: str
    groq_model: str = "openai/gpt-oss-120b"
    groq_max_tokens: int = 700

    frontend_url: str = "http://localhost:8501"

    exchange_api_url: str = "https://api.frankfurter.dev/v1"
    exchange_api_timeout: float = 10.0

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized_value = value.strip().lower()

            if normalized_value in {"release", "production", "prod"}:
                return False

            if normalized_value in {"development", "dev"}:
                return True

        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
