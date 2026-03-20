"""Application configuration. Reads from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings loaded from environment variables.

    Locally: read from .env or docker-compose environment.
    Production: injected by Cloud Run from Secret Manager.
    """

    # Database
    database_url: str = "postgresql://canvas:canvas@localhost:5432/semantic_canvas"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Auth
    firebase_project_id: str = ""
    jwt_algorithm: str = "RS256"

    # Embeddings
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # Task queue
    task_queue_backend: str = "local"  # "local" or "cloud_tasks"
    gcp_project_id: str = ""
    cloud_tasks_queue: str = ""
    cloud_tasks_location: str = ""
    ingestion_service_url: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Server
    port: int = 8000
    environment: str = "development"  # development | staging | production

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
