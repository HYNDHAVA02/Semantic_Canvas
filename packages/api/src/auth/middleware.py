"""Optional auth middleware — validates tokens if present, allows anonymous otherwise.

Extracts Authorization header and resolves an AuthContext:
- Bearer <jwt> → Firebase JWT (dashboard users)
- Bearer sc_pat_... → Personal API Token (AI agents)
- Missing/invalid → request proceeds with no auth context

This is **permissive** by default. To require auth on specific endpoints,
check `request.state.auth` in the route handler.
"""

from __future__ import annotations

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger(__name__)


class OptionalAuthMiddleware(BaseHTTPMiddleware):
    """Extract auth context from Authorization header if present."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request, optionally resolving auth."""
        request.state.auth = None

        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return await call_next(request)

        token = auth_header[7:]  # strip "Bearer "

        try:
            if token.startswith("sc_pat_"):
                # Personal API Token — validate against DB
                request.state.auth = await self._resolve_pat(request, token)
            else:
                # Assume Firebase JWT
                request.state.auth = await self._resolve_jwt(token)
        except Exception:
            logger.debug("Auth token validation failed, proceeding anonymously", exc_info=True)

        return await call_next(request)

    async def _resolve_pat(self, request: Request, token: str) -> object | None:
        """Validate a Personal API Token against the database.

        Returns a dict with user_id, project_id, and role if valid.
        """
        pool = getattr(request.app.state, "db_pool", None)
        if not pool:
            return None

        row = await pool.fetchrow(
            """
            SELECT t.id, t.project_id, t.label
            FROM personal_access_tokens t
            WHERE t.token_hash = encode(sha256($1::bytea), 'hex')
              AND (t.expires_at IS NULL OR t.expires_at > now())
              AND t.revoked_at IS NULL
            """,
            token.encode(),
        )
        if not row:
            return None

        return {
            "user_id": f"pat:{row['id']}",
            "project_id": str(row["project_id"]),
            "role": "editor",
            "source": "pat",
        }

    async def _resolve_jwt(self, token: str) -> object | None:
        """Validate a Firebase JWT.

        Placeholder — full verification requires fetching Firebase public keys.
        For now, decode without verification to extract claims.
        """
        # TODO: Add real Firebase JWT verification using firebase_admin or PyJWT
        # with Google's public keys. For now, just log that we saw a JWT.
        logger.debug("JWT token received (verification not yet implemented)")
        return None
