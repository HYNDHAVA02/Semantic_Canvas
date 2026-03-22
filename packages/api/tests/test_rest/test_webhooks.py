"""Tests for the GitHub webhook controller."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

WEBHOOK_SECRET = "test-secret-key"


def _sign(payload: bytes, secret: str = WEBHOOK_SECRET) -> str:
    """Compute the X-Hub-Signature-256 header value."""
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _push_payload(
    repo_url: str = "https://github.com/org/repo.git",
    branch: str = "main",
) -> dict[str, Any]:
    """Build a minimal GitHub push event payload."""
    return {
        "ref": f"refs/heads/{branch}",
        "repository": {
            "clone_url": repo_url,
        },
    }


@pytest.fixture
def mock_task_queue() -> AsyncMock:
    """A mock TaskQueue that records enqueue calls."""
    queue = AsyncMock()
    queue.enqueue.return_value = "task-id-123"
    return queue


@pytest_asyncio.fixture
async def client(
    db_pool,
    test_project,
    mock_task_queue: AsyncMock,
) -> AsyncClient:
    """Create an async test client with webhook secret and task queue wired up."""
    with patch("src.rest.controllers.webhooks.settings") as mock_settings:
        mock_settings.github_webhook_secret = WEBHOOK_SECRET

        from src.main import create_app

        app = create_app()

        # Wire up test fixtures on app.state
        app.state.db_pool = db_pool
        app.state.task_queue = mock_task_queue

        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest_asyncio.fixture
async def project_with_repo(db_pool, test_project) -> dict[str, Any]:
    """Set repo_url on the test project so webhook lookups work."""
    repo_url = "https://github.com/org/repo.git"
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE projects SET repo_url = $1 WHERE id = $2",
            repo_url,
            test_project["id"],
        )
    return {**test_project, "repo_url": repo_url}


# ── Valid push on default branch ─────────────────────────────────────


@pytest.mark.asyncio
async def test_valid_push_default_branch(
    client: AsyncClient,
    project_with_repo: dict[str, Any],
    mock_task_queue: AsyncMock,
) -> None:
    """Push to default branch enqueues an ingestion task."""
    payload = _push_payload(repo_url=project_with_repo["repo_url"], branch="main")
    body = json.dumps(payload).encode()

    resp = await client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": _sign(body),
            "X-GitHub-Event": "push",
            "Content-Type": "application/json",
        },
    )

    assert resp.status_code == 202
    data = resp.json()
    assert data["action"] == "enqueued"
    assert data["task_id"] == "task-id-123"

    mock_task_queue.enqueue.assert_awaited_once_with(
        "axon_ingest",
        {
            "project_id": str(project_with_repo["id"]),
            "repo_url": project_with_repo["repo_url"],
            "branch": "main",
        },
    )


# ── Invalid signature ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invalid_signature(client: AsyncClient) -> None:
    """Webhook with wrong signature returns 401."""
    body = json.dumps(_push_payload()).encode()

    resp = await client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": "sha256=bad",
            "X-GitHub-Event": "push",
            "Content-Type": "application/json",
        },
    )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_missing_signature(client: AsyncClient) -> None:
    """Webhook without signature header returns 401."""
    body = json.dumps(_push_payload()).encode()

    resp = await client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "push",
            "Content-Type": "application/json",
        },
    )

    assert resp.status_code == 401


# ── Ping event ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ping_event(client: AsyncClient) -> None:
    """GitHub ping event returns pong."""
    body = b'{"zen": "Keep it logically awesome."}'

    resp = await client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": _sign(body),
            "X-GitHub-Event": "ping",
            "Content-Type": "application/json",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["action"] == "pong"


# ── Push to non-default branch ───────────────────────────────────────


@pytest.mark.asyncio
async def test_push_non_default_branch(
    client: AsyncClient,
    project_with_repo: dict[str, Any],
    mock_task_queue: AsyncMock,
) -> None:
    """Push to a feature branch is skipped."""
    payload = _push_payload(
        repo_url=project_with_repo["repo_url"],
        branch="feat/new-feature",
    )
    body = json.dumps(payload).encode()

    resp = await client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": _sign(body),
            "X-GitHub-Event": "push",
            "Content-Type": "application/json",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["action"] == "skipped"
    mock_task_queue.enqueue.assert_not_awaited()


# ── Unknown repo ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unknown_repo(client: AsyncClient) -> None:
    """Push from an unregistered repo returns 404."""
    payload = _push_payload(repo_url="https://github.com/unknown/repo.git")
    body = json.dumps(payload).encode()

    resp = await client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": _sign(body),
            "X-GitHub-Event": "push",
            "Content-Type": "application/json",
        },
    )

    assert resp.status_code == 404


# ── Missing webhook secret config ────────────────────────────────────


@pytest.mark.asyncio
async def test_missing_webhook_secret() -> None:
    """If GITHUB_WEBHOOK_SECRET is empty, all webhooks are rejected."""
    with patch("src.rest.controllers.webhooks.settings") as mock_settings:
        mock_settings.github_webhook_secret = ""

        from src.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)  # type: ignore[arg-type]

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            body = json.dumps(_push_payload()).encode()
            resp = await ac.post(
                "/api/v1/webhooks/github",
                content=body,
                headers={
                    "X-Hub-Signature-256": _sign(body),
                    "X-GitHub-Event": "push",
                    "Content-Type": "application/json",
                },
            )

        assert resp.status_code == 401
