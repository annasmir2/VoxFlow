from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    project_name: str = "VoxFlow AI"
    api_v1_prefix: str = "/api"
    database_url: str = "sqlite:///./app.db"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    ai_provider: str = "ollama"
    ai_timezone: str = "Europe/London"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
