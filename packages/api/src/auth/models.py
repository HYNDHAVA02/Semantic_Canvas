"""Auth models shared across the application."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class Role(str, Enum):
    """User roles within a project."""

    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class AuthContext(BaseModel):
    """Resolved auth context available to all handlers.

    Created by auth middleware from either:
    - JWT token (dashboard users via Firebase Auth)
    - PAT (Personal API Token for AI agents)

    Passed to repository methods and MCP tool handlers
    for project scoping and permission checks.
    """

    user_id: str
    project_id: UUID
    role: Role

    def can_write(self) -> bool:
        """Check if the user can create/modify data."""
        return self.role in (Role.ADMIN, Role.EDITOR)

    def can_admin(self) -> bool:
        """Check if the user can manage project settings."""
        return self.role == Role.ADMIN
