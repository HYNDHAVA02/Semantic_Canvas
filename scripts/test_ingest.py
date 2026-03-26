"""Manual test script for the local ingestion pipeline.

Prerequisites:
  - axon CLI installed (pip install axoniq)
  - Git installed
  - Postgres running with semantic_canvas DB (docker compose up -d)
  - Ingestion deps installed (cd packages/ingestion && pip install -r requirements.txt)

Usage:
  python scripts/test_ingest.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add ingestion package to sys.path so we can import directly
_INGESTION_DIR = str(Path(__file__).resolve().parents[1] / "packages" / "ingestion")
sys.path.insert(0, _INGESTION_DIR)

from src.main import run_ingestion  # noqa: E402

PAYLOAD = {
    "project_id": "403f22ef-a063-42d3-bf6e-8c529eb05c0b",
    "repo_url": "https://github.com/pallets/click.git",
    "branch": "main",
}


def main() -> None:
    """Run ingestion with a test payload."""
    print(f"Running ingestion with payload: {PAYLOAD}")
    asyncio.run(run_ingestion(PAYLOAD))
    print("Ingestion complete!")


if __name__ == "__main__":
    main()
