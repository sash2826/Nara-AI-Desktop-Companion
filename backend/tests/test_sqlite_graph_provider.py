"""Tests for SQLiteGraphProvider — all run in-memory, no external services."""

from __future__ import annotations

import uuid

import aiosqlite
import pytest

from enterprise_ai_companion.capabilities.graph.graph_models import (
    Entity,
    EntityType,
    Relationship,
    RelationshipType,
)
from enterprise_ai_companion.capabilities.graph.sqlite_graph_provider import SQLiteGraphProvider


# ---------------------------------------------------------------------------
# Fixture: in-memory database with the graph schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS graph_entities (
    id                  TEXT NOT NULL PRIMARY KEY,
    name                TEXT NOT NULL,
    entity_type         TEXT NOT NULL,
    source_document_id  TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    confidence          REAL NOT NULL DEFAULT 1.0,
    canonical           TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_graph_entities_document ON graph_entities(source_document_id);
CREATE INDEX IF NOT EXISTS idx_graph_entities_canonical ON graph_entities(canonical, entity_type);
CREATE INDEX IF NOT EXISTS idx_graph_entities_name ON graph_entities(name);

CREATE TABLE IF NOT EXISTS graph_relationships (
    id                  TEXT NOT NULL PRIMARY KEY,
    source_id           TEXT NOT NULL REFERENCES graph_entities(id) ON DELETE CASCADE,
    target_id           TEXT NOT NULL REFERENCES graph_entities(id) ON DELETE CASCADE,
    relationship_type   TEXT NOT NULL,
    confidence          REAL NOT NULL DEFAULT 1.0,
    UNIQUE (source_id, target_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_graph_relationships_source ON graph_relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_graph_relationships_target ON graph_relationships(target_id);
"""


async def _make_provider() -> tuple[SQLiteGraphProvider, aiosqlite.Connection]:
    conn = await aiosqlite.connect(":memory:")
    await conn.execute("PRAGMA foreign_keys=ON")
    await conn.executescript(_SCHEMA)
    await conn.commit()
    provider = SQLiteGraphProvider(conn)
    await provider.initialize()
    return provider, conn


def _entity(name: str, doc_id: str = "doc1", entity_type: EntityType = EntityType.ORGANIZATION, confidence: float = 0.9) -> Entity:
    eid = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{doc_id}:{name}"))
    return Entity(
        id=eid,
        name=name,
        entity_type=entity_type,
        source_document_id=doc_id,
        confidence=confidence,
    )


def _rel(source: Entity, target: Entity, rel_type: RelationshipType = RelationshipType.RELATED_TO) -> Relationship:
    return Relationship(
        source_id=source.id,
        target_id=target.id,
        relationship_type=rel_type,
        confidence=0.8,
    )


async def _seed_doc(conn: aiosqlite.Connection, doc_id: str = "doc1") -> None:
    await conn.execute("INSERT OR IGNORE INTO documents (id) VALUES (?)", (doc_id,))
    await conn.commit()


# ---------------------------------------------------------------------------
# health
# ---------------------------------------------------------------------------

class TestHealth:
    async def test_returns_true_when_schema_present(self) -> None:
        provider, conn = await _make_provider()
        assert await provider.health() is True
        await conn.close()


# ---------------------------------------------------------------------------
# upsert_entity
# ---------------------------------------------------------------------------

class TestUpsertEntity:
    async def test_inserts_new_entity(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn)
        e = _entity("Volvo")
        await provider.upsert_entity(e)

        async with conn.execute("SELECT name FROM graph_entities WHERE id = ?", (e.id,)) as cur:
            row = await cur.fetchone()
        assert row is not None
        assert row[0] == "Volvo"
        await conn.close()

    async def test_upsert_updates_confidence_to_max(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn)
        e_low = _entity("Volvo", confidence=0.5)
        e_high = _entity("Volvo", confidence=0.95)
        await provider.upsert_entity(e_low)
        await provider.upsert_entity(e_high)

        async with conn.execute("SELECT confidence FROM graph_entities WHERE id = ?", (e_low.id,)) as cur:
            row = await cur.fetchone()
        assert float(row[0]) == pytest.approx(0.95)
        await conn.close()

    async def test_stores_canonical_name(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn)
        e = _entity("  Volvo AB!  ")
        await provider.upsert_entity(e)

        async with conn.execute("SELECT canonical FROM graph_entities WHERE id = ?", (e.id,)) as cur:
            row = await cur.fetchone()
        assert row[0] == "volvo ab"
        await conn.close()


# ---------------------------------------------------------------------------
# upsert_relationship
# ---------------------------------------------------------------------------

class TestUpsertRelationship:
    async def test_inserts_relationship(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn)
        volvo = _entity("Volvo")
        sweden = _entity("Sweden", entity_type=EntityType.LOCATION)
        await provider.upsert_entity(volvo)
        await provider.upsert_entity(sweden)
        await provider.upsert_relationship(_rel(volvo, sweden, RelationshipType.BELONGS_TO))

        async with conn.execute("SELECT relationship_type FROM graph_relationships") as cur:
            rows = await cur.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "BELONGS_TO"
        await conn.close()

    async def test_duplicate_relationship_updates_confidence(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn)
        a = _entity("A")
        b = _entity("B")
        await provider.upsert_entity(a)
        await provider.upsert_entity(b)
        r1 = Relationship(source_id=a.id, target_id=b.id, relationship_type=RelationshipType.RELATED_TO, confidence=0.5)
        r2 = Relationship(source_id=a.id, target_id=b.id, relationship_type=RelationshipType.RELATED_TO, confidence=0.9)
        await provider.upsert_relationship(r1)
        await provider.upsert_relationship(r2)

        async with conn.execute("SELECT COUNT(*), MAX(confidence) FROM graph_relationships") as cur:
            row = await cur.fetchone()
        assert row[0] == 1  # no duplicate row
        assert float(row[1]) == pytest.approx(0.9)
        await conn.close()


# ---------------------------------------------------------------------------
# delete_by_document
# ---------------------------------------------------------------------------

class TestDeleteByDocument:
    async def test_removes_entities_for_document(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn, "doc1")
        await _seed_doc(conn, "doc2")
        e1 = _entity("Volvo", doc_id="doc1")
        e2 = _entity("Sweden", doc_id="doc2", entity_type=EntityType.LOCATION)
        await provider.upsert_entity(e1)
        await provider.upsert_entity(e2)
        await provider.delete_by_document("doc1")

        async with conn.execute("SELECT id FROM graph_entities") as cur:
            rows = await cur.fetchall()
        ids = {r[0] for r in rows}
        assert e1.id not in ids
        assert e2.id in ids
        await conn.close()

    async def test_cascade_deletes_relationships(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn)
        volvo = _entity("Volvo")
        sweden = _entity("Sweden", entity_type=EntityType.LOCATION)
        await provider.upsert_entity(volvo)
        await provider.upsert_entity(sweden)
        await provider.upsert_relationship(_rel(volvo, sweden))
        await provider.delete_by_document("doc1")

        async with conn.execute("SELECT COUNT(*) FROM graph_relationships") as cur:
            row = await cur.fetchone()
        assert row[0] == 0
        await conn.close()


# ---------------------------------------------------------------------------
# get_context
# ---------------------------------------------------------------------------

class TestGetContext:
    async def test_returns_none_for_unknown_entity(self) -> None:
        provider, conn = await _make_provider()
        result = await provider.get_context("NonExistent")
        assert result is None
        await conn.close()

    async def test_returns_entity_with_neighbours(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn)
        volvo = _entity("Volvo")
        sweden = _entity("Sweden", entity_type=EntityType.LOCATION)
        await provider.upsert_entity(volvo)
        await provider.upsert_entity(sweden)
        await provider.upsert_relationship(_rel(volvo, sweden, RelationshipType.BELONGS_TO))

        context = await provider.get_context("Volvo", depth=1)
        assert context is not None
        assert context.entity.name == "Volvo"
        neighbour_names = {e.name for e in context.related_entities}
        assert "Sweden" in neighbour_names
        assert len(context.relationships) == 1
        await conn.close()

    async def test_respects_depth(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn)
        a = _entity("A")
        b = _entity("B")
        c = _entity("C", entity_type=EntityType.CONCEPT)
        await provider.upsert_entity(a)
        await provider.upsert_entity(b)
        await provider.upsert_entity(c)
        await provider.upsert_relationship(_rel(a, b))
        await provider.upsert_relationship(_rel(b, c))

        # depth=1 should not include C
        context1 = await provider.get_context("A", depth=1)
        assert context1 is not None
        names1 = {e.name for e in context1.related_entities}
        assert "B" in names1
        assert "C" not in names1

        # depth=2 should include C
        context2 = await provider.get_context("A", depth=2)
        assert context2 is not None
        names2 = {e.name for e in context2.related_entities}
        assert "C" in names2
        await conn.close()


# ---------------------------------------------------------------------------
# search_entities
# ---------------------------------------------------------------------------

class TestSearchEntities:
    async def test_returns_matching_entities(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn)
        await provider.upsert_entity(_entity("Volvo Group"))
        await provider.upsert_entity(_entity("Volvo Cars"))
        await provider.upsert_entity(_entity("Sweden", entity_type=EntityType.LOCATION))

        results = await provider.search_entities("volvo")
        names = {r["name"] for r in results}
        assert "Volvo Group" in names
        assert "Volvo Cars" in names
        assert "Sweden" not in names
        await conn.close()

    async def test_filters_by_entity_type(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn)
        await provider.upsert_entity(_entity("Volvo", entity_type=EntityType.ORGANIZATION))
        await provider.upsert_entity(_entity("Volvo Project", entity_type=EntityType.PROJECT))

        results = await provider.search_entities("volvo", entity_type="Organization")
        assert len(results) == 1
        assert results[0]["entity_type"] == "Organization"
        await conn.close()

    async def test_returns_empty_for_no_match(self) -> None:
        provider, conn = await _make_provider()
        results = await provider.search_entities("xyzzy")
        assert results == []
        await conn.close()

    async def test_sorted_by_confidence_descending(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn)
        low = _entity("Alpha", confidence=0.3)
        high = _entity("Alphabet", confidence=0.9)
        await provider.upsert_entity(low)
        await provider.upsert_entity(high)

        results = await provider.search_entities("alpha")
        assert results[0]["confidence"] >= results[-1]["confidence"]
        await conn.close()


# ---------------------------------------------------------------------------
# get_connected_documents
# ---------------------------------------------------------------------------

class TestGetConnectedDocuments:
    async def test_returns_empty_for_unknown_entity(self) -> None:
        provider, conn = await _make_provider()
        result = await provider.get_connected_documents("NonExistent")
        assert result == []
        await conn.close()

    async def test_returns_directly_connected_document(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn, "doc1")
        await _seed_doc(conn, "doc2")
        volvo = _entity("Volvo", doc_id="doc1")
        sweden = _entity("Sweden", doc_id="doc2", entity_type=EntityType.LOCATION)
        await provider.upsert_entity(volvo)
        await provider.upsert_entity(sweden)
        await provider.upsert_relationship(_rel(volvo, sweden))

        doc_ids = await provider.get_connected_documents("Volvo")
        assert "doc1" in doc_ids
        assert "doc2" in doc_ids
        await conn.close()


# ---------------------------------------------------------------------------
# get_visualization
# ---------------------------------------------------------------------------

class TestGetVisualization:
    async def test_returns_empty_when_no_entities(self) -> None:
        provider, conn = await _make_provider()
        result = await provider.get_visualization()
        assert result == {"nodes": [], "edges": []}
        await conn.close()

    async def test_returns_nodes_and_edges(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn)
        volvo = _entity("Volvo")
        sweden = _entity("Sweden", entity_type=EntityType.LOCATION)
        await provider.upsert_entity(volvo)
        await provider.upsert_entity(sweden)
        await provider.upsert_relationship(_rel(volvo, sweden))

        result = await provider.get_visualization()
        assert len(result["nodes"]) == 2
        assert len(result["edges"]) == 1
        await conn.close()

    async def test_focal_entity_subgraph(self) -> None:
        provider, conn = await _make_provider()
        await _seed_doc(conn)
        volvo = _entity("Volvo")
        sweden = _entity("Sweden", entity_type=EntityType.LOCATION)
        unrelated = _entity("Unrelated", entity_type=EntityType.CONCEPT)
        await provider.upsert_entity(volvo)
        await provider.upsert_entity(sweden)
        await provider.upsert_entity(unrelated)
        await provider.upsert_relationship(_rel(volvo, sweden))

        result = await provider.get_visualization(entity_name="Volvo", depth=1)
        node_labels = {n["label"] for n in result["nodes"]}
        assert "Volvo" in node_labels
        assert "Sweden" in node_labels
        assert "Unrelated" not in node_labels
        await conn.close()
