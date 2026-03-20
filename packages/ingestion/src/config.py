"""Ingestion service configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://canvas:canvas@localhost:5432/semantic_canvas"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    clone_timeout: int = 120
    analyze_timeout: int = 300

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
