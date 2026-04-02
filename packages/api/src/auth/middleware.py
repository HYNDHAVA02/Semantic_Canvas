"""Optional auth middleware — validates tokens if present, allows anonymous otherwise.

Extracts Authorization header and resolves an AuthContext:
- Bearer <jwt> → Firebase JWT (dashboard users)
- Bearer sc_pat_... → Personal API Token (AI agents)
- Missing/invalid → request proceeds with no auth context

This is **permissive** by default. To require auth on specific endpoints,
check `request.state.auth` in the route handler.

Implemented as a pure ASGI middleware (not BaseHTTPMiddleware) to preserve
streaming responses such as SSE connections on /mcp/sse.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)

_Scope = dict[str, Any]
_Receive = Callable[[], Awaitable[dict[str, Any]]]
_Send = Callable[[dict[str, Any]], Awaitable[None]]
_ASGIApp = Callable[[_Scope, _Receive, _Send], Awaitable[None]]


class OptionalAuthMiddleware:
    """Extract auth context from Authorization header if present.

    Pure ASGI middleware — does not wrap the response body, so SSE and
    other streaming responses work correctly.
    """

    def __init__(self, app: _ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: _Scope, receive: _Receive, send: _Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Build a lightweight request-like view for header access
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()

        # Default: no auth
        scope["state"] = scope.get("state", {})
        scope["state"]["auth"] = None

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                auth_ctx = await self._resolve_token(scope, token)
                scope["state"]["auth"] = auth_ctx
            except Exception:
                logger.debug(
                    "Auth token validation failed, proceeding anonymously",
                    exc_info=True,
                )

        await self.app(scope, receive, send)

    async def _resolve_token(self, scope: _Scope, token: str) -> object | None:
        """Resolve a Bearer token to an auth context dict."""
        if token.startswith("sc_pat_"):
            return await self._resolve_pat(scope, token)
        return await self._resolve_jwt(token)

    async def _resolve_pat(self, scope: _Scope, token: str) -> object | None:
        """Validate a Personal API Token against the database."""
        # Access the db_pool stored on the ASGI app's state
        app = scope.get("app")
        pool = getattr(getattr(app, "state", None), "db_pool", None)
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
