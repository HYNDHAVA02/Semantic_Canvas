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

    # GitHub webhook
    github_webhook_secret: str = ""

    # CORS — set CORS_ORIGINS='["https://your-app.vercel.app"]' in production
    cors_origins: list[str] = ["http://localhost:3000"]

    # MCP SSE allowed hosts (DNS rebinding protection, mcp>=1.26)
    # Wildcard port syntax supported: "localhost:*" matches any localhost port.
    # In production, add your Cloud Run hostname (e.g. "semantic-canvas-xxx.run.app").
    mcp_allowed_hosts: list[str] = ["localhost:*", "127.0.0.1:*"]

    # Server
    port: int = 8000
    environment: str = "development"  # development | staging | production

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
