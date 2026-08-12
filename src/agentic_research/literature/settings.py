"""Environment-backed provider settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class LiteratureSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openalex_api_key: str | None = None
    semantic_scholar_api_key: str | None = None
    user_agent: str = "Agentic-Research/0.2 (+https://github.com/ZHX4/Agentic-Research)"
    request_timeout_seconds: float = 30.0
    openalex_min_interval_seconds: float = 0.1
    semantic_scholar_min_interval_seconds: float = 1.0
    arxiv_min_interval_seconds: float = 3.0
