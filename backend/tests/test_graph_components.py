"""Tests for Phase 05 graph pipeline components.

Covers: EntityExtractor, RelationshipExtractor, EnrichmentService,
GraphStateRepository, GraphQueryService, and TraversalEngine.
All tests run without Neo4j or a live LLM.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import aiosqlite
import pytest

from enterprise_ai_companion.capabilities.graph.entity_extractor import EntityExtractor
from enterprise_ai_companion.capabilities.graph.graph_models import (
    Entity,
    EntityType,
    GraphContext,
    Relationship,
    RelationshipType,
)
from enterprise_ai_companion.capabilities.graph.graph_query_service import GraphQueryService
from enterprise_ai_companion.capabilities.graph.null_graph_provider import NullGraphProvider
from enterprise_ai_companion.capabilities.graph.relationship_extractor import RelationshipExtractor
from enterprise_ai_companion.capabilities.graph.traversal_engine import TraversalEngine


# ---------------------------------------------------------------------------
# EntityExtractor
# ---------------------------------------------------------------------------


class TestEntityExtractor:
    """Unit tests for EntityExtractor — all LLM calls are mocked."""

    def _make_extractor(self) -> EntityExtractor:
        return EntityExtractor()

    async def test_returns_entities_from_valid_json(self) -> None:
        payload = json.dumps(
            {
                "entities": [
                    {"name": "Volvo", "type": "Organization", "confidence": 0.95},
                    {"name": "Sweden", "type": "Location", "confidence": 0.88},
                ]
            }
        )
        extractor = self._make_extractor()
        with patch(
            "enterprise_ai_companion.capabilities.graph.entity_extractor.chat_complete",
            new_callable=AsyncMock,
            return_value=payload,
        ):
            entities = await extractor.extract("Volvo is a company from Sweden.")

        assert len(entities) == 2
        names = {e.name for e in entities}
        assert "Volvo" in names
        assert "Sweden" in names

    async def test_strips_markdown_code_fence(self) -> None:
        payload = "```json\n" + json.dumps(
            {"entities": [{"name": "Gothenburg", "type": "Location", "confidence": 0.9}]}
        ) + "\n```"
        extractor = self._make_extractor()
        with patch(
            "enterprise_ai_companion.capabilities.graph.entity_extractor.chat_complete",
            new_callable=AsyncMock,
            return_value=payload,
        ):
            entities = await extractor.extract("Gothenburg is in Sweden.")

        assert len(entities) == 1
        assert entities[0].name == "Gothenburg"

    async def test_returns_empty_on_invalid_json(self) -> None:
        extractor = self._make_extractor()
        with patch(
            "enterprise_ai_companion.capabilities.graph.entity_extractor.chat_complete",
            new_callable=AsyncMock,
            return_value="this is not json",
        ):
            entities = await extractor.extract("Some text.")

        assert entities == []

    async def test_returns_empty_on_llm_failure(self) -> None:
        extractor = self._make_extractor()
        with patch(
            "enterprise_ai_companion.capabilities.graph.entity_extractor.chat_complete",
            new_callable=AsyncMock,
            side_effect=RuntimeError("network error"),
        ):
            entities = await extractor.extract("Some text.")

        assert entities == []

    async def test_deduplicates_by_lowercase_name(self) -> None:
        payload = json.dumps(
            {
                "entities": [
                    {"name": "Volvo", "type": "Organization", "confidence": 0.9},
                    {"name": "volvo", "type": "Organization", "confidence": 0.7},
                ]
            }
        )
        extractor = self._make_extractor()
        with patch(
            "enterprise_ai_companion.capabilities.graph.entity_extractor.chat_complete",
            new_callable=AsyncMock,
            return_value=payload,
        ):
            entities = await extractor.extract("Volvo is also called volvo.")

        assert len(entities) == 1
        # Higher confidence retained
        assert entities[0].confidence == 0.9

    async def test_confidence_clamped_to_unit_interval(self) -> None:
        payload = json.dumps(
            {"entities": [{"name": "X", "type": "Concept", "confidence": 1.5}]}
        )
        extractor = self._make_extractor()
        with patch(
            "enterprise_ai_companion.capabilities.graph.entity_extractor.chat_complete",
            new_callable=AsyncMock,
            return_value=payload,
        ):
            entities = await extractor.extract("X is a thing.")

        assert entities[0].confidence == 1.0

    async def test_returns_empty_for_empty_text(self) -> None:
        extractor = self._make_extractor()
        entities = await extractor.extract("")
        assert entities == []

    async def test_skips_missing_name_field(self) -> None:
        payload = json.dumps(
            {"entities": [{"type": "Organization", "confidence": 0.9}]}
        )
        extractor = self._make_extractor()
        with patch(
            "enterprise_ai_companion.capabilities.graph.entity_extractor.chat_complete",
            new_callable=AsyncMock,
            return_value=payload,
        ):
            entities = await extractor.extract("Some org.")

        assert entities == []


# ---------------------------------------------------------------------------
# RelationshipExtractor
# ---------------------------------------------------------------------------


class TestRelationshipExtractor:
    """Unit tests for RelationshipExtractor."""

    def _make_extractor(self) -> RelationshipExtractor:
        return RelationshipExtractor()

    async def test_returns_empty_when_fewer_than_two_entities(self) -> None:
        extractor = self._make_extractor()
        from enterprise_ai_companion.capabilities.graph.graph_models import ExtractedEntity
        one_entity = [
            ExtractedEntity(
                name="Volvo",
                entity_type=EntityType.ORGANIZATION,
                confidence=0.9,
            )
        ]
        rels = await extractor.extract("Volvo text.", one_entity)
        assert rels == []

    async def test_returns_relationship_from_valid_json(self) -> None:
        from enterprise_ai_companion.capabilities.graph.graph_models import ExtractedEntity

        entities = [
            ExtractedEntity(
                name="Volvo",
                entity_type=EntityType.ORGANIZATION,
                confidence=0.9,
            ),
            ExtractedEntity(
                name="Sweden",
                entity_type=EntityType.LOCATION,
                confidence=0.88,
            ),
        ]
        payload = json.dumps(
            {
                "relationships": [
                    {
                        "source": "Volvo",
                        "target": "Sweden",
                        "type": "BELONGS_TO",
                        "confidence": 0.85,
                    }
                ]
            }
        )
        extractor = self._make_extractor()
        with patch(
            "enterprise_ai_companion.capabilities.graph.relationship_extractor.chat_complete",
            new_callable=AsyncMock,
            return_value=payload,
        ):
            rels = await extractor.extract("Volvo is from Sweden.", entities)

        assert len(rels) == 1
        assert rels[0].source_name == "Volvo"
        assert rels[0].target_name == "Sweden"

    async def test_rejects_source_not_in_entity_list(self) -> None:
        from enterprise_ai_companion.capabilities.graph.graph_models import ExtractedEntity

        entities = [
            ExtractedEntity(
                name="Volvo",
                entity_type=EntityType.ORGANIZATION,
                confidence=0.9,
            ),
            ExtractedEntity(
                name="Sweden",
                entity_type=EntityType.LOCATION,
                confidence=0.88,
            ),
        ]
        payload = json.dumps(
            {
                "relationships": [
                    {
                        "source": "HallucinatedEntity",
                        "target": "Sweden",
                        "type": "MENTIONS",
                        "confidence": 0.7,
                    }
                ]
            }
        )
        extractor = self._make_extractor()
        with patch(
            "enterprise_ai_companion.capabilities.graph.relationship_extractor.chat_complete",
            new_callable=AsyncMock,
            return_value=payload,
        ):
            rels = await extractor.extract("Some text.", entities)

        assert rels == []

    async def test_deduplicates_relationships(self) -> None:
        from enterprise_ai_companion.capabilities.graph.graph_models import ExtractedEntity

        entities = [
            ExtractedEntity(name="A", entity_type=EntityType.CONCEPT, confidence=0.9),
            ExtractedEntity(name="B", entity_type=EntityType.CONCEPT, confidence=0.9),
        ]
        payload = json.dumps(
            {
                "relationships": [
                    {"source": "A", "target": "B", "type": "RELATED_TO", "confidence": 0.8},
                    {"source": "A", "target": "B", "type": "RELATED_TO", "confidence": 0.7},
                ]
            }
        )
        extractor = self._make_extractor()
        with patch(
            "enterprise_ai_companion.capabilities.graph.relationship_extractor.chat_complete",
            new_callable=AsyncMock,
            return_value=payload,
        ):
            rels = await extractor.extract("A relates to B.", entities)

        assert len(rels) == 1

    async def test_returns_empty_on_llm_failure(self) -> None:
        from enterprise_ai_companion.capabilities.graph.graph_models import ExtractedEntity

        entities = [
            ExtractedEntity(name="A", entity_type=EntityType.CONCEPT, confidence=0.9),
            ExtractedEntity(name="B", entity_type=EntityType.CONCEPT, confidence=0.9),
        ]
        extractor = self._make_extractor()
        with patch(
            "enterprise_ai_companion.capabilities.graph.relationship_extractor.chat_complete",
            new_callable=AsyncMock,
            side_effect=RuntimeError("timeout"),
        ):
            rels = await extractor.extract("A and B.", entities)

        assert rels == []


# ---------------------------------------------------------------------------
# EnrichmentService — canonical_name function
# ---------------------------------------------------------------------------


class TestCanonicalName:
    def test_lowercases_and_strips_whitespace(self) -> None:
        from enterprise_ai_companion.capabilities.graph.enrichment_service import canonical_name

        assert canonical_name("  Volvo AB  ") == "volvo ab"

    def test_strips_trailing_punctuation(self) -> None:
        from enterprise_ai_companion.capabilities.graph.enrichment_service import canonical_name

        # Trailing non-word characters are stripped; internal hyphens are preserved.
        assert canonical_name("Volvo-AB!") == "volvo-ab"
        assert canonical_name("  !Volvo!  ") == "volvo"

    def test_collapses_multiple_spaces(self) -> None:
        from enterprise_ai_companion.capabilities.graph.enrichment_service import canonical_name

        assert canonical_name("volvo   group") == "volvo group"

    def test_normalises_unicode(self) -> None:
        from enterprise_ai_companion.capabilities.graph.enrichment_service import canonical_name

        # NFC normalisation: combining diacritics collapsed into precomposed form
        import unicodedata
        composed = "café"          # café (precomposed)
        decomposed = "café"       # cafe + combining acute accent
        assert canonical_name(composed) == canonical_name(decomposed)


# ---------------------------------------------------------------------------
# GraphStateRepository
# ---------------------------------------------------------------------------


class TestGraphStateRepository:
    """Integration tests using an in-memory SQLite database."""

    async def _make_db(self) -> aiosqlite.Connection:
        conn = await aiosqlite.connect(":memory:")
        await conn.execute(
            """
            CREATE TABLE graph_state (
                document_id TEXT NOT NULL PRIMARY KEY,
                file_hash   TEXT NOT NULL,
                built_at    TEXT NOT NULL
            )
            """
        )
        await conn.commit()
        return conn

    async def test_get_returns_none_when_missing(self) -> None:
        from enterprise_ai_companion.capabilities.graph.graph_state_repository import (
            GraphStateRepository,
        )

        conn = await self._make_db()
        repo = GraphStateRepository(conn)
        result = await repo.get_by_document("nonexistent")
        assert result is None
        await conn.close()

    async def test_save_and_retrieve(self) -> None:
        from enterprise_ai_companion.capabilities.graph.graph_state_repository import (
            GraphStateRepository,
        )

        conn = await self._make_db()
        repo = GraphStateRepository(conn)
        await repo.save("doc1", "abc123")
        state = await repo.get_by_document("doc1")
        assert state is not None
        assert state.document_id == "doc1"
        assert state.file_hash == "abc123"
        await conn.close()

    async def test_save_replaces_existing(self) -> None:
        from enterprise_ai_companion.capabilities.graph.graph_state_repository import (
            GraphStateRepository,
        )

        conn = await self._make_db()
        repo = GraphStateRepository(conn)
        await repo.save("doc1", "hash_v1")
        await repo.save("doc1", "hash_v2")
        state = await repo.get_by_document("doc1")
        assert state is not None
        assert state.file_hash == "hash_v2"
        await conn.close()

    async def test_delete_removes_entry(self) -> None:
        from enterprise_ai_companion.capabilities.graph.graph_state_repository import (
            GraphStateRepository,
        )

        conn = await self._make_db()
        repo = GraphStateRepository(conn)
        await repo.save("doc1", "hash1")
        await repo.delete_by_document("doc1")
        result = await repo.get_by_document("doc1")
        assert result is None
        await conn.close()

    async def test_delete_is_idempotent(self) -> None:
        from enterprise_ai_companion.capabilities.graph.graph_state_repository import (
            GraphStateRepository,
        )

        conn = await self._make_db()
        repo = GraphStateRepository(conn)
        await repo.delete_by_document("nonexistent")  # must not raise
        await conn.close()


# ---------------------------------------------------------------------------
# GraphQueryService — graceful degradation with NullGraphProvider
# ---------------------------------------------------------------------------


class TestGraphQueryService:
    async def test_get_entity_returns_none_for_null_provider(self) -> None:
        svc = GraphQueryService(NullGraphProvider())
        result = await svc.get_entity("Volvo")
        assert result is None

    async def test_get_neighborhood_returns_none_for_null_provider(self) -> None:
        svc = GraphQueryService(NullGraphProvider())
        result = await svc.get_neighborhood("Volvo", depth=2)
        assert result is None

    async def test_search_entities_returns_empty_for_null_provider(self) -> None:
        svc = GraphQueryService(NullGraphProvider())
        results = await svc.search_entities("Volvo")
        assert results == []

    async def test_get_connected_documents_returns_empty_for_null_provider(self) -> None:
        svc = GraphQueryService(NullGraphProvider())
        doc_ids = await svc.get_connected_documents("Volvo")
        assert doc_ids == []

    async def test_get_entity_returns_context_when_provider_has_data(self) -> None:
        mock_provider = AsyncMock()
        entity = Entity(
            id="e1",
            name="Volvo",
            entity_type=EntityType.ORGANIZATION,
            source_document_id="doc1",
            properties={},
        )
        mock_provider.get_context = AsyncMock(
            return_value=GraphContext(
                entity=entity, related_entities=[], relationships=[]
            )
        )
        svc = GraphQueryService(mock_provider)
        result = await svc.get_entity("Volvo")
        assert result is not None
        assert result.entity.name == "Volvo"


# ---------------------------------------------------------------------------
# TraversalEngine — graceful degradation
# ---------------------------------------------------------------------------


class TestTraversalEngine:
    async def test_find_path_returns_not_found_for_null_provider(self) -> None:
        engine = TraversalEngine(NullGraphProvider())
        path = await engine.find_path("Volvo", "Sweden")
        assert path.found is False
        assert path.source_name == "Volvo"
        assert path.target_name == "Sweden"

    async def test_get_connected_documents_returns_empty_for_null_provider(self) -> None:
        engine = TraversalEngine(NullGraphProvider())
        doc_ids = await engine.get_connected_documents("Volvo")
        assert doc_ids == []

    async def test_find_path_length_zero_when_no_path(self) -> None:
        engine = TraversalEngine(NullGraphProvider())
        path = await engine.find_path("A", "B")
        assert path.length == 0
        assert path.node_names == []
