"""Extract structured data from Axon's KuzuDB graph via Cypher queries."""

from __future__ import annotations

from dataclasses import dataclass

from src.axon_runner import run_axon_cypher


@dataclass
class AxonRawData:
    """Raw data extracted from Axon's graph."""

    symbols: list[dict]
    calls: list[dict]
    imports: list[dict]
    heritage: list[dict]


QUERIES = {
    "symbols": """
        MATCH (s:Symbol)
        RETURN s.id AS id, s.name AS name, s.kind AS kind,
               s.file AS file, s.line AS line, s.language AS language,
               s.complexity AS complexity, s.is_exported AS is_exported,
               s.community AS community, s.is_dead AS is_dead
    """,
    "calls": """
        MATCH (a:Symbol)-[r:CALLS]->(b:Symbol)
        RETURN a.id AS from_id, a.name AS from_name, a.kind AS from_kind,
               b.id AS to_id, b.name AS to_name, b.kind AS to_kind,
               r.file AS file, r.line AS line
    """,
    "imports": """
        MATCH (a:Symbol)-[:IMPORTS]->(b:Symbol)
        RETURN a.id AS from_id, a.name AS from_name,
               b.id AS to_id, b.name AS to_name
    """,
    "heritage": """
        MATCH (a:Symbol)-[r:INHERITS|IMPLEMENTS]->(b:Symbol)
        RETURN a.id AS from_id, a.name AS from_name,
               b.id AS to_id, b.name AS to_name, type(r) AS rel_type
    """,
}


async def extract_from_axon(repo_path: str) -> AxonRawData:
    """Run all extraction queries and return raw data."""
    return AxonRawData(
        symbols=await run_axon_cypher(repo_path, QUERIES["symbols"]),
        calls=await run_axon_cypher(repo_path, QUERIES["calls"]),
        imports=await run_axon_cypher(repo_path, QUERIES["imports"]),
        heritage=await run_axon_cypher(repo_path, QUERIES["heritage"]),
    )
