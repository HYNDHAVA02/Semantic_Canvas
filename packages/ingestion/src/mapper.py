"""Map Axon's raw output to our PostgreSQL schema types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.extractor import AxonRawData


@dataclass
class MappedEntity:
    """An entity ready for upserting into PostgreSQL."""

    axon_id: str
    name: str
    kind: str
    source_ref: str | None
    metadata: dict[str, Any]


@dataclass
class MappedRelationship:
    """A relationship ready for upserting into PostgreSQL."""

    from_axon_id: str
    to_axon_id: str
    kind: str
    metadata: dict[str, Any]


KIND_MAP = {
    "function": "function",
    "method": "function",
    "class": "class",
    "module": "module",
    "file": "module",
    "interface": "class",
    "type_alias": "class",
    "enum": "class",
}

REL_KIND_MAP = {
    "CALLS": "calls",
    "IMPORTS": "imports",
    "INHERITS": "inherits",
    "IMPLEMENTS": "implements",
}


def map_axon_to_schema(
    raw: AxonRawData,
) -> tuple[list[MappedEntity], list[MappedRelationship]]:
    """Transform raw Axon data into our schema types."""
    entities: list[MappedEntity] = []
    for sym in raw.symbols:
        metadata: dict[str, Any] = {}
        for key in ("file", "line", "language", "complexity", "is_exported", "community"):
            if sym.get(key) is not None:
                metadata[key] = sym[key]
        metadata["is_dead_code"] = sym.get("is_dead", False)
        metadata["axon_id"] = sym["id"]

        entities.append(MappedEntity(
            axon_id=sym["id"],
            name=sym["name"],
            kind=KIND_MAP.get(sym["kind"], "function"),
            source_ref=sym.get("file"),
            metadata=metadata,
        ))

    relationships: list[MappedRelationship] = []

    for call in raw.calls:
        meta: dict[str, Any] = {}
        if call.get("file"):
            meta["file"] = call["file"]
        if call.get("line"):
            meta["line"] = call["line"]
        relationships.append(MappedRelationship(
            from_axon_id=call["from_id"],
            to_axon_id=call["to_id"],
            kind="calls",
            metadata=meta,
        ))

    for imp in raw.imports:
        relationships.append(MappedRelationship(
            from_axon_id=imp["from_id"],
            to_axon_id=imp["to_id"],
            kind="imports",
            metadata={},
        ))

    for h in raw.heritage:
        relationships.append(MappedRelationship(
            from_axon_id=h["from_id"],
            to_axon_id=h["to_id"],
            kind=REL_KIND_MAP.get(h.get("rel_type", ""), "inherits"),
            metadata={},
        ))

    return entities, relationships
