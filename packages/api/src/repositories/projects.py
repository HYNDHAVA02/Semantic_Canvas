"""Repository for the projects table."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.repositories.base import BaseRepository


class ProjectsRepository(BaseRepository):
    """CRUD operations for projects."""

    async def list_all(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """List all projects with pagination. Returns (rows, total)."""
        total = await self._fetch_one(
            "SELECT count(*) AS cnt FROM projects",
        )
        rows = await self._fetch_all(
            """
            SELECT id, name, slug, description, repo_url, default_branch,
                   created_at, updated_at
            FROM projects
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )
        return rows, total["cnt"] if total else 0

    async def get_by_id(self, project_id: UUID) -> dict[str, Any] | None:
        """Get a single project by ID."""
        return await self._fetch_one(
            """
            SELECT id, name, slug, description, repo_url, default_branch,
                   created_at, updated_at
            FROM projects WHERE id = $1
            """,
            project_id,
        )

    async def create(
        self,
        name: str,
        slug: str,
        description: str | None = None,
        repo_url: str | None = None,
        default_branch: str = "main",
    ) -> dict[str, Any]:
        """Create a new project."""
        return await self._fetch_one(  # type: ignore[return-value]
            """
            INSERT INTO projects (name, slug, description, repo_url, default_branch)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, name, slug, description, repo_url, default_branch,
                      created_at, updated_at
            """,
            name,
            slug,
            description,
            repo_url,
            default_branch,
        )

    async def update(
        self,
        project_id: UUID,
        **fields: Any,
    ) -> dict[str, Any] | None:
        """Partial update of a project. Only updates provided fields."""
        allowed = {"name", "slug", "description", "repo_url", "default_branch"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return await self.get_by_id(project_id)

        set_clauses = []
        params: list[Any] = []
        for i, (col, val) in enumerate(updates.items(), start=1):
            set_clauses.append(f"{col} = ${i}")
            params.append(val)

        params.append(project_id)
        idx = len(params)

        return await self._fetch_one(
            f"""
            UPDATE projects SET {', '.join(set_clauses)}, updated_at = now()
            WHERE id = ${idx}
            RETURNING id, name, slug, description, repo_url, default_branch,
                      created_at, updated_at
            """,
            *params,
        )
