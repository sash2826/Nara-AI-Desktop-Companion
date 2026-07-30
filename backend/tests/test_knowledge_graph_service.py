"""Tests for KnowledgeGraphService using NullGraphProvider (no Neo4j or LLM required)."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from enterprise_ai_companion.capabilities.graph.graph_models import EntityType, RelationshipType
from enterprise_ai_companion.capabilities.graph.knowledge_graph_service import (
    KnowledgeGraphService,
    _coerce_entity_type,
    _coerce_rel_type,
)
from enterprise_ai_companion.capabilities.graph.null_graph_provider import NullGraphProvider


@pytest.fixture
async def service() -> KnowledgeGraphService:
    provider = NullGraphProvider()
    await provider.initialize()
    return KnowledgeGraphService(provider)


_VALID_EXTRACTION = {
    "entities": [
        {"name": "Volvo", "type": "Organization"},
        {"name": "Sweden", "type": "Location"},
    ],
    "relationships": [
        {"source": "Volvo", "target": "Sweden", "type": "BELONGS_TO"},
    ],
}


class TestBuildFromChunks:
    async def test_does_not_raise_with_valid_llm_response(
        self, service: KnowledgeGraphService
    ) -> None:
        with patch(
            "enterprise_ai_companion.capabilities.graph.knowledge_graph_service.chat_complete",
            new_callable=AsyncMock,
            return_value=json.dumps(_VALID_EXTRACTION),
        ):
            await service.build_from_chunks("doc1", ["Volvo is a company from Sweden."])

    async def test_tolerates_llm_failure(self, service: KnowledgeGraphService) -> None:
        with patch(
            "enterprise_ai_companion.capabilities.graph.knowledge_graph_service.chat_complete",
            new_callable=AsyncMock,
            side_effect=RuntimeError("network error"),
        ):
            # Should not raise — graph building is best-effort
            await service.build_from_chunks("doc1", ["Some text."])

    async def test_tolerates_invalid_json_from_llm(
        self, service: KnowledgeGraphService
    ) -> None:
        with patch(
            "enterprise_ai_companion.capabilities.graph.knowledge_graph_service.chat_complete",
            new_callable=AsyncMock,
            return_value="this is not json",
        ):
            await service.build_from_chunks("doc1", ["Some text."])

    async def test_handles_empty_chunks(self, service: KnowledgeGraphService) -> None:
        await service.build_from_chunks("doc1", [])

    async def test_skips_relationships_with_missing_entities(
        self, service: KnowledgeGraphService
    ) -> None:
        extraction = {
            "entities": [{"name": "Volvo", "type": "Organization"}],
            "relationships": [
                {"source": "Volvo", "target": "Unknown", "type": "MENTIONS"},
            ],
        }
        with patch(
            "enterprise_ai_companion.capabilities.graph.knowledge_graph_service.chat_complete",
            new_callable=AsyncMock,
            return_value=json.dumps(extraction),
        ):
            await service.build_from_chunks("doc1", ["text"])

    async def test_extracts_json_from_markdown_fence(
        self, service: KnowledgeGraphService
    ) -> None:
        fenced = f"```json\n{json.dumps(_VALID_EXTRACTION)}\n```"
        with patch(
            "enterprise_ai_companion.capabilities.graph.knowledge_graph_service.chat_complete",
            new_callable=AsyncMock,
            return_value=fenced,
        ):
            await service.build_from_chunks("doc1", ["Volvo is from Sweden."])

    async def test_delete_document_does_not_raise(
        self, service: KnowledgeGraphService
    ) -> None:
        await service.delete_document("doc1")


class TestCoercionHelpers:
    def test_coerce_valid_entity_type(self) -> None:
        assert _coerce_entity_type("Person") == EntityType.PERSON

    def test_coerce_unknown_entity_type_falls_back_to_concept(self) -> None:
        assert _coerce_entity_type("WeirdThing") == EntityType.CONCEPT

    def test_coerce_valid_rel_type(self) -> None:
        assert _coerce_rel_type("MENTIONS") == RelationshipType.MENTIONS

    def test_coerce_unknown_rel_type_falls_back_to_related_to(self) -> None:
        assert _coerce_rel_type("UNKNOWN_REL") == RelationshipType.RELATED_TO
