"""Tests for the Axon-to-schema mapper."""

from __future__ import annotations

import json
from pathlib import Path

from src.extractor import AxonRawData
from src.mapper import map_axon_to_schema

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text())


def make_raw_data() -> AxonRawData:
    return AxonRawData(
        symbols=load_fixture("sample_symbols.json"),
        calls=load_fixture("sample_calls.json"),
        imports=[],
        heritage=[],
    )


class TestMapper:

    def test_maps_symbols_to_entities(self) -> None:
        """Each Axon symbol becomes a MappedEntity."""
        entities, _ = map_axon_to_schema(make_raw_data())
        assert len(entities) == 5

        names = {e.name for e in entities}
        assert "processOrder" in names
        assert "validateCard" in names
        assert "OrderService" in names

    def test_maps_function_kind(self) -> None:
        """Axon 'function' maps to our 'function' kind."""
        entities, _ = map_axon_to_schema(make_raw_data())
        process_order = next(e for e in entities if e.name == "processOrder")
        assert process_order.kind == "function"

    def test_maps_class_kind(self) -> None:
        """Axon 'class' maps to our 'class' kind."""
        entities, _ = map_axon_to_schema(make_raw_data())
        order_service = next(e for e in entities if e.name == "OrderService")
        assert order_service.kind == "class"

    def test_dead_code_flag(self) -> None:
        """Dead code flag is preserved in metadata."""
        entities, _ = map_axon_to_schema(make_raw_data())
        legacy = next(e for e in entities if e.name == "legacyHelper")
        assert legacy.metadata["is_dead_code"] is True

    def test_maps_calls_to_relationships(self) -> None:
        """Axon CALLS edges become 'calls' relationships."""
        _, relationships = map_axon_to_schema(make_raw_data())
        calls = [r for r in relationships if r.kind == "calls"]
        assert len(calls) == 3

    def test_call_metadata_includes_location(self) -> None:
        """Call relationships include file and line in metadata."""
        _, relationships = map_axon_to_schema(make_raw_data())
        first_call = relationships[0]
        assert "file" in first_call.metadata
        assert "line" in first_call.metadata

    def test_empty_input(self) -> None:
        """Empty Axon data produces empty output."""
        raw = AxonRawData(symbols=[], calls=[], imports=[], heritage=[])
        entities, relationships = map_axon_to_schema(raw)
        assert entities == []
        assert relationships == []
