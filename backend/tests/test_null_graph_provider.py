"""Tests for NullGraphProvider — verifies the no-op contract."""

import pytest

from enterprise_ai_companion.capabilities.graph.graph_models import (
    Entity,
    EntityType,
    Relationship,
    RelationshipType,
)
from enterprise_ai_companion.capabilities.graph.null_graph_provider import NullGraphProvider


@pytest.fixture
async def provider() -> NullGraphProvider:
    p = NullGraphProvider()
    await p.initialize()
    return p


class TestNullGraphProvider:
    async def test_initialize_does_not_raise(self) -> None:
        p = NullGraphProvider()
        await p.initialize()

    async def test_health_returns_true(self, provider: NullGraphProvider) -> None:
        assert await provider.health() is True

    async def test_upsert_entity_is_noop(self, provider: NullGraphProvider) -> None:
        entity = Entity(
            id="e1",
            name="Test",
            entity_type=EntityType.CONCEPT,
            source_document_id="doc1",
        )
        await provider.upsert_entity(entity)  # must not raise

    async def test_upsert_relationship_is_noop(self, provider: NullGraphProvider) -> None:
        rel = Relationship(
            source_id="e1",
            target_id="e2",
            relationship_type=RelationshipType.RELATED_TO,
        )
        await provider.upsert_relationship(rel)  # must not raise

    async def test_get_context_returns_none(self, provider: NullGraphProvider) -> None:
        result = await provider.get_context("anything")
        assert result is None

    async def test_delete_by_document_is_noop(self, provider: NullGraphProvider) -> None:
        await provider.delete_by_document("doc1")  # must not raise

    async def test_close_does_not_raise(self, provider: NullGraphProvider) -> None:
        await provider.close()
