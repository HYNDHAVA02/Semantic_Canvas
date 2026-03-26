"""Extract structured data from Axon's KuzuDB graph via Cypher queries."""

from __future__ import annotations

from dataclasses import dataclass

from src.axon_runner import run_axon_cypher


@dataclass
class AxonRawData:
    """Raw data extracted from Axon's graph."""

    symbols: list[dict[str, object]]
    calls: list[dict[str, object]]
    imports: list[dict[str, object]]
    heritage: list[dict[str, object]]


# Axon's schema uses separate node tables (Function, Method, Class, File, etc.)
# and a single CodeRelation edge table with a rel_type property.
# We UNION the symbol tables into a unified list matching our entity schema.
QUERIES = {
    "symbols": """
        MATCH (f:Function)
        RETURN f.id AS id, f.name AS name, 'function' AS kind,
               f.file_path AS file, f.start_line AS line, f.language AS language,
               f.is_exported AS is_exported, f.is_dead AS is_dead
        UNION ALL
        MATCH (m:Method)
        RETURN m.id AS id, m.name AS name, 'method' AS kind,
               m.file_path AS file, m.start_line AS line, m.language AS language,
               m.is_exported AS is_exported, m.is_dead AS is_dead
        UNION ALL
        MATCH (c:Class)
        RETURN c.id AS id, c.name AS name, 'class' AS kind,
               c.file_path AS file, c.start_line AS line, c.language AS language,
               c.is_exported AS is_exported, c.is_dead AS is_dead
    """,
    "calls": """
        MATCH (a)-[r:CodeRelation]->(b)
        WHERE r.rel_type = 'calls'
        RETURN a.id AS from_id, a.name AS from_name, label(a) AS from_kind,
               b.id AS to_id, b.name AS to_name, label(b) AS to_kind
    """,
    "imports": """
        MATCH (a:File)-[r:CodeRelation]->(b)
        WHERE r.rel_type = 'uses_type'
        RETURN a.id AS from_id, a.name AS from_name,
               b.id AS to_id, b.name AS to_name
    """,
    "heritage": """
        MATCH (a)-[r:CodeRelation]->(b)
        WHERE r.rel_type = 'extends'
        RETURN a.id AS from_id, a.name AS from_name,
               b.id AS to_id, b.name AS to_name, r.rel_type AS rel_type
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
