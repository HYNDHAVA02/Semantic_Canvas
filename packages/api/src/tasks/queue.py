"""Task queue abstraction.

Two implementations:
- LocalTaskQueue: runs tasks in-process (local dev)
- CloudTasksQueue: enqueues to GCP Cloud Tasks (production)

Swapped by TASK_QUEUE_BACKEND env var.
"""

from __future__ import annotations

import json
import asyncio
import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class TaskQueue(Protocol):
    """Protocol for task queue implementations."""

    async def enqueue(self, task_name: str, payload: dict[str, Any]) -> str:
        """Enqueue a task. Returns a task ID."""
        ...


class LocalTaskQueue:
    """In-process task queue for local development.

    Runs the task handler in a background asyncio task.
    No durability — if the process dies, queued tasks are lost.
    Fine for local dev, not for production.
    """

    def __init__(self, handlers: dict[str, Any] | None = None):
        self._handlers = handlers or {}

    def register(self, task_name: str, handler: Any) -> None:
        """Register a handler function for a task name."""
        self._handlers[task_name] = handler

    async def enqueue(self, task_name: str, payload: dict[str, Any]) -> str:
        """Run the task in a background asyncio task."""
        import uuid

        task_id = str(uuid.uuid4())
        handler = self._handlers.get(task_name)
        if not handler:
            raise ValueError(f"No handler registered for task: {task_name}")

        async def _run() -> None:
            try:
                logger.info("Local task %s started: %s", task_name, task_id)
                await handler(payload)
                logger.info("Local task %s completed: %s", task_name, task_id)
            except Exception:
                logger.exception("Local task %s failed: %s", task_name, task_id)

        asyncio.create_task(_run())
        return task_id


class CloudTasksQueue:
    """GCP Cloud Tasks implementation.

    Enqueues an HTTP POST to the ingestion Cloud Run service.
    Cloud Tasks handles retries, dead-letter, and rate limiting.
    """

    def __init__(
        self,
        project_id: str,
        location: str,
        queue_name: str,
        ingestion_service_url: str,
    ):
        self._project_id = project_id
        self._location = location
        self._queue_name = queue_name
        self._service_url = ingestion_service_url

    async def enqueue(self, task_name: str, payload: dict[str, Any]) -> str:
        """Create a Cloud Task that POSTs to the ingestion service."""
        from google.cloud import tasks_v2

        client = tasks_v2.CloudTasksAsyncClient()
        parent = client.queue_path(
            self._project_id, self._location, self._queue_name
        )

        task = tasks_v2.Task(
            http_request=tasks_v2.HttpRequest(
                http_method=tasks_v2.HttpMethod.POST,
                url=f"{self._service_url}/tasks/{task_name}",
                headers={"Content-Type": "application/json"},
                body=json.dumps(payload).encode(),
            )
        )

        response = await client.create_task(parent=parent, task=task)
        task_id = response.name.split("/")[-1]
        logger.info("Cloud Task created: %s/%s", task_name, task_id)
        return task_id  # type: ignore[no-any-return]  # google-cloud-tasks response.name untyped


def create_task_queue(
    backend: str,
    gcp_project_id: str = "",
    cloud_tasks_location: str = "",
    cloud_tasks_queue: str = "",
    ingestion_service_url: str = "",
) -> TaskQueue:
    """Factory: create the appropriate task queue based on config."""
    if backend == "cloud_tasks":
        return CloudTasksQueue(
            project_id=gcp_project_id,
            location=cloud_tasks_location,
            queue_name=cloud_tasks_queue,
            ingestion_service_url=ingestion_service_url,
        )
    return LocalTaskQueue()
