"""Axon runner — wraps axon analyze CLI and KuzuDB queries."""

from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path

import kuzu

from src.config import settings

logger = logging.getLogger(__name__)


def _resolve_axon() -> str:
    """Resolve the full path to the axon CLI.

    On Windows, asyncio.create_subprocess_exec does not search PATH
    the same way as shell commands, so we resolve the path explicitly.
    """
    axon_path = shutil.which("axon")
    if axon_path is None:
        raise FileNotFoundError(
            "axon CLI not found on PATH. Install it with: pip install axoniq"
        )
    return axon_path


async def run_axon_analyze(repo_path: str) -> None:
    """Run `axon analyze .` on a cloned repo."""
    axon = _resolve_axon()
    proc = await asyncio.create_subprocess_exec(
        axon, "analyze", ".",
        cwd=repo_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(
        proc.communicate(), timeout=settings.analyze_timeout
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Axon analyze failed: {stderr.decode()}")
    logger.info("Axon analyze output: %s", stdout.decode().strip())


def run_axon_cypher_sync(repo_path: str, query: str) -> list[dict[str, object]]:
    """Execute a Cypher query against Axon's KuzuDB graph.

    Opens the .axon/kuzu database in read-only mode, executes the query,
    and returns results as a list of dicts keyed by column names.
    """
    db_path = Path(repo_path) / ".axon" / "kuzu"
    if not db_path.exists():
        raise FileNotFoundError(
            f"No Axon index found at {db_path}. Run 'axon analyze' first."
        )

    db = kuzu.Database(str(db_path), read_only=True)
    conn = kuzu.Connection(db)
    try:
        result = conn.execute(query)
        columns = result.get_column_names()
        rows: list[dict[str, object]] = []
        while result.has_next():
            values = result.get_next()
            rows.append(dict(zip(columns, values)))
        return rows
    finally:
        conn.close()
        del db


async def run_axon_cypher(repo_path: str, query: str) -> list[dict[str, object]]:
    """Async wrapper around run_axon_cypher_sync.

    Runs the synchronous KuzuDB query in a thread executor to avoid
    blocking the event loop.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, run_axon_cypher_sync, repo_path, query)
