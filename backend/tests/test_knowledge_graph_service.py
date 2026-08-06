"""Tests for KnowledgeGraphService using NullGraphProvider (no Neo4j or LLM required)."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from enterprise_ai_companion.capabilities.graph.entity_extractor import _coerce_entity_type
from enterprise_ai_companion.capabilities.graph.graph_models import EntityType, RelationshipType
from enterprise_ai_companion.capabilities.graph.knowledge_graph_service import KnowledgeGraphService
from enterprise_ai_companion.capabilities.graph.null_graph_provider import NullGraphProvider
from enterprise_ai_companion.capabilities.graph.relationship_extractor import _coerce_rel_type

# Patch targets: extraction now happens inside EntityExtractor and RelationshipExtractor.
_ENTITY_LLM = "enterprise_ai_companion.capabilities.graph.entity_extractor.chat_complete"
_REL_LLM = "enterprise_ai_companion.capabilities.graph.relationship_extractor.chat_complete"

_ENTITY_PAYLOAD = json.dumps(
    {
        "entities": [
            {"name": "Volvo", "type": "Organization", "confidence": 0.9},
            {"name": "Sweden", "type": "Location", "confidence": 0.88},
        ]
    }
)

_REL_PAYLOAD = json.dumps(
    {
        "relationships": [
            {"source": "Volvo", "target": "Sweden", "type": "BELONGS_TO", "confidence": 0.85}
        ]
    }
)


@pytest.fixture
async def service() -> KnowledgeGraphService:
    provider = NullGraphProvider()
    await provider.initialize()
    return KnowledgeGraphService(provider)


class TestBuildFromChunks:
    async def test_does_not_raise_with_valid_llm_response(
        self, service: KnowledgeGraphService
    ) -> None:
        with (
            patch(_ENTITY_LLM, new_callable=AsyncMock, return_value=_ENTITY_PAYLOAD),
            patch(_REL_LLM, new_callable=AsyncMock, return_value=_REL_PAYLOAD),
        ):
            await service.build_from_chunks("doc1", ["Volvo is a company from Sweden."])

    async def test_tolerates_llm_failure(self, service: KnowledgeGraphService) -> None:
        with (
            patch(_ENTITY_LLM, new_callable=AsyncMock, side_effect=RuntimeError("network error")),
            patch(_REL_LLM, new_callable=AsyncMock, side_effect=RuntimeError("network error")),
        ):
            # Should not raise — graph building is best-effort
            await service.build_from_chunks("doc1", ["Some text."])

    async def test_tolerates_invalid_json_from_llm(
        self, service: KnowledgeGraphService
    ) -> None:
        with (
            patch(_ENTITY_LLM, new_callable=AsyncMock, return_value="this is not json"),
            patch(_REL_LLM, new_callable=AsyncMock, return_value="also not json"),
        ):
            await service.build_from_chunks("doc1", ["Some text."])

    async def test_handles_empty_chunks(self, service: KnowledgeGraphService) -> None:
        await service.build_from_chunks("doc1", [])

    async def test_skips_relationships_with_missing_entities(
        self, service: KnowledgeGraphService
    ) -> None:
        entity_payload = json.dumps(
            {"entities": [{"name": "Volvo", "type": "Organization", "confidence": 0.9}]}
        )
        rel_payload = json.dumps(
            {
                "relationships": [
                    {"source": "Volvo", "target": "Unknown", "type": "MENTIONS", "confidence": 0.7}
                ]
            }
        )
        with (
            patch(_ENTITY_LLM, new_callable=AsyncMock, return_value=entity_payload),
            patch(_REL_LLM, new_callable=AsyncMock, return_value=rel_payload),
        ):
            # "Unknown" is not in the entity list — relationship should be silently dropped.
            await service.build_from_chunks("doc1", ["text"])

    async def test_extracts_json_from_markdown_fence(
        self, service: KnowledgeGraphService
    ) -> None:
        fenced_entities = f"```json\n{_ENTITY_PAYLOAD}\n```"
        fenced_rels = f"```json\n{_REL_PAYLOAD}\n```"
        with (
            patch(_ENTITY_LLM, new_callable=AsyncMock, return_value=fenced_entities),
            patch(_REL_LLM, new_callable=AsyncMock, return_value=fenced_rels),
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
