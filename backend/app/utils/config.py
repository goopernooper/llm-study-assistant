from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LLM Study Assistant"
    environment: str = "dev"

    data_dir: str = "/data"
    upload_dir: str | None = None
    index_dir: str | None = None
    sqlite_path: str | None = None

    openai_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    embed_model: str = "text-embedding-3-small"

    use_local_embeddings: bool = False
    local_embed_model: str = "all-MiniLM-L6-v2"
    use_local_llm: bool = False

    cors_origins: str = "http://localhost:5173"

    default_top_k: int = 5
    default_temperature: float = 0.2
    max_context_chunks: int = 12
    request_timeout: int = 60

    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore", case_sensitive=False)

    def resolved_upload_dir(self) -> str:
        if self.upload_dir:
            return self.upload_dir
        return str(Path(self.data_dir) / "uploads")

    def resolved_index_dir(self) -> str:
        if self.index_dir:
            return self.index_dir
        return str(Path(self.data_dir) / "index")

    def resolved_sqlite_path(self) -> str:
        if self.sqlite_path:
            return self.sqlite_path
        return str(Path(self.data_dir) / "metadata.db")

    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
