"""Ingestion pipeline entry point.

Receives a job payload, orchestrates the full pipeline:
clone → axon analyze → extract → map → upsert → cleanup.

Runs as:
- Cloud Run Job in production (triggered by Cloud Tasks)
- Direct function call in local dev (triggered by LocalTaskQueue)
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import sys
import tempfile

from src.config import settings
from src.axon_runner import run_axon_analyze
from src.extractor import extract_from_axon
from src.mapper import map_axon_to_schema
from src.upserter import upsert_to_postgres

logger = logging.getLogger(__name__)


async def run_ingestion(payload: dict) -> None:
    """Run the full ingestion pipeline for a single repo.

    Args:
        payload: {
            "project_id": "uuid",
            "repo_url": "https://github.com/org/repo.git",
            "branch": "main",
            "clone_token": "ghp_..."  (optional, for private repos)
        }
    """
    project_id = payload["project_id"]
    repo_url = payload["repo_url"]
    branch = payload.get("branch", "main")
    clone_token = payload.get("clone_token")

    tmp_dir = tempfile.mkdtemp(prefix="sc-axon-")
    logger.info("Starting ingestion for project=%s repo=%s", project_id, repo_url)

    try:
        # 1. Shallow clone
        clone_url = repo_url
        if clone_token:
            # Insert token for private repo auth
            clone_url = repo_url.replace("https://", f"https://x:{clone_token}@")

        logger.info("Cloning %s (branch: %s) to %s", repo_url, branch, tmp_dir)
        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "--depth", "1", "--branch", branch, clone_url, tmp_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=settings.clone_timeout
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Git clone failed: {stderr.decode()}")

        # 2. Run Axon analysis
        logger.info("Running axon analyze...")
        await run_axon_analyze(tmp_dir)

        # 3. Extract symbols and relationships from Axon's graph
        logger.info("Extracting from Axon graph...")
        raw_data = await extract_from_axon(tmp_dir)

        # 4. Map Axon output to our schema
        logger.info("Mapping to schema...")
        entities, relationships = map_axon_to_schema(raw_data)

        # 5. Upsert to PostgreSQL
        logger.info("Upserting %d entities, %d relationships...", len(entities), len(relationships))
        await upsert_to_postgres(project_id, entities, relationships)

        logger.info("Ingestion complete for project=%s", project_id)

    except asyncio.TimeoutError:
        logger.error("Ingestion timed out for project=%s", project_id)
        raise
    except Exception:
        logger.exception("Ingestion failed for project=%s", project_id)
        raise
    finally:
        # 6. Cleanup
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    # When run as Cloud Run Job, payload comes from stdin or env
    import os

    payload_str = os.environ.get("TASK_PAYLOAD", "{}")
    if len(sys.argv) > 1:
        payload_str = sys.argv[1]

    payload = json.loads(payload_str)
    asyncio.run(run_ingestion(payload))
