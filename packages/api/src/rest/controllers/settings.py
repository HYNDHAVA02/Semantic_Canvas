"""Settings controller — PAT generation and MCP config."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter()


class CreateTokenBody(BaseModel):
    """Request body for generating a personal API token."""

    label: str = Field(min_length=1, max_length=200)


@router.post("/tokens", status_code=201)
async def create_token(
    request: Request,
    project_id: UUID,
    body: CreateTokenBody,
) -> dict[str, Any]:
    """Generate a personal API token.

    The plaintext token is returned once and never stored.
    Only the SHA-256 hash is persisted.
    """
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO personal_api_tokens (project_id, label, token_hash)
            VALUES ($1, $2, $3)
            RETURNING id, label, created_at
            """,
            project_id,
            body.label,
            token_hash,
        )

    return {
        "id": str(row["id"]),
        "label": row["label"],
        "token": token,
        "created_at": str(row["created_at"]),
    }


@router.get("/mcp-config")
async def mcp_config(
    request: Request,
    project_id: UUID,
) -> dict[str, Any]:
    """Return a copy-paste MCP server configuration JSON."""
    base_url = str(request.base_url).rstrip("/")

    return {
        "mcpServers": {
            "semantic-canvas": {
                "url": f"{base_url}/mcp/sse",
                "headers": {
                    "Authorization": "Bearer <YOUR_API_TOKEN>",
                    "X-Project-Id": str(project_id),
                },
            }
        }
    }
