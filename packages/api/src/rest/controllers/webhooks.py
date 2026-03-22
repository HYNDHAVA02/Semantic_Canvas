"""GitHub webhook controller — receives push events and enqueues ingestion."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

from fastapi import APIRouter, Request, Response

from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def _verify_signature(payload: bytes, signature_header: str | None, secret: str) -> bool:
    """Verify GitHub HMAC-SHA256 webhook signature."""
    if not signature_header or not secret:
        return False

    if not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected}", signature_header)


@router.post("/github")
async def github_webhook(request: Request) -> Response:
    """Handle incoming GitHub webhook events.

    Verifies the HMAC-SHA256 signature, filters for push events on the
    default branch, and enqueues an Axon ingestion job.
    """
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    # Reject if no secret is configured — refuse unsigned requests
    if not settings.github_webhook_secret:
        logger.warning("GitHub webhook received but GITHUB_WEBHOOK_SECRET is not configured")
        return Response(
            content='{"error": "webhook secret not configured"}',
            status_code=401,
            media_type="application/json",
        )

    if not _verify_signature(body, signature, settings.github_webhook_secret):
        return Response(
            content='{"error": "invalid signature"}',
            status_code=401,
            media_type="application/json",
        )

    event = request.headers.get("X-GitHub-Event", "")

    # Respond to ping events (GitHub sends this on webhook creation)
    if event == "ping":
        return Response(
            content='{"action": "pong"}',
            status_code=200,
            media_type="application/json",
        )

    # Only process push events
    if event != "push":
        return Response(
            content='{"action": "ignored", "reason": "not a push event"}',
            status_code=200,
            media_type="application/json",
        )

    return await _handle_push(request, body)


async def _handle_push(request: Request, body: bytes) -> Response:
    """Process a verified push event."""
    import json

    payload: dict[str, Any] = json.loads(body)

    ref: str = payload.get("ref", "")
    repo_url: str = payload.get("repository", {}).get("clone_url", "")

    if not ref or not repo_url:
        return Response(
            content='{"error": "missing ref or repository.clone_url"}',
            status_code=400,
            media_type="application/json",
        )

    # Extract branch name from refs/heads/<branch>
    branch = ref.removeprefix("refs/heads/")

    # Look up the project by repo URL
    db_pool = request.app.state.db_pool
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, default_branch FROM projects WHERE repo_url = $1",
            repo_url,
        )

    if row is None:
        return Response(
            content='{"error": "no project found for this repository"}',
            status_code=404,
            media_type="application/json",
        )

    project_id = str(row["id"])
    default_branch = row["default_branch"] or "main"

    # Skip pushes to non-default branches
    if branch != default_branch:
        logger.info(
            "Skipping push to %s (default is %s) for project %s",
            branch, default_branch, project_id,
        )
        return Response(
            content='{"action": "skipped", "reason": "non-default branch"}',
            status_code=200,
            media_type="application/json",
        )

    # Enqueue ingestion job
    task_queue = request.app.state.task_queue
    task_id = await task_queue.enqueue(
        "axon_ingest",
        {
            "project_id": project_id,
            "repo_url": repo_url,
            "branch": branch,
        },
    )

    logger.info("Enqueued axon_ingest task %s for project %s", task_id, project_id)

    return Response(
        content=json.dumps({"action": "enqueued", "task_id": task_id}),
        status_code=202,
        media_type="application/json",
    )
