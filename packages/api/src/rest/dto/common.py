"""Shared DTOs for REST API responses and query parameters."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel):
    """Standard paginated list response."""

    data: list[dict[str, Any]]
    total: int
    limit: int
    offset: int
