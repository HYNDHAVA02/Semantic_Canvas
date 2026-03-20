"""Axon CLI runner — wraps axon analyze and axon cypher commands."""

from __future__ import annotations

import asyncio
import json
import logging

from src.config import settings

logger = logging.getLogger(__name__)


async def run_axon_analyze(repo_path: str) -> None:
    """Run `axon analyze .` on a cloned repo."""
    proc = await asyncio.create_subprocess_exec(
        "axon", "analyze", ".",
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


async def run_axon_cypher(repo_path: str, query: str) -> list[dict]:
    """Run a Cypher query against Axon's KuzuDB graph."""
    proc = await asyncio.create_subprocess_exec(
        "axon", "cypher", query, "--json",
        cwd=repo_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(
        proc.communicate(), timeout=60
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Axon cypher failed: {stderr.decode()}")
    return json.loads(stdout.decode())
