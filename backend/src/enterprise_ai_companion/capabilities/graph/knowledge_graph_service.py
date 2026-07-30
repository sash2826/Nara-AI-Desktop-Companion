"""Extracts entities and relationships from text and writes them to the graph.

Entity extraction uses a single LLM call per chunk (structured JSON output).
On failure the service logs a warning and skips the chunk — graph building is
best-effort and must never block document indexing.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from enterprise_ai_companion.capabilities.ai.llm_client import chat_complete
from enterprise_ai_companion.capabilities.graph.graph_models import (
    Entity,
    EntityType,
    Relationship,
    RelationshipType,
)
from enterprise_ai_companion.capabilities.graph.graph_provider import GraphProvider

logger = logging.getLogger(__name__)

_ENTITY_TYPES = ", ".join(e.value for e in EntityType)
_REL_TYPES = ", ".join(r.value for r in RelationshipType)

_EXTRACTION_SYSTEM = (
    "You are a knowledge extraction engine. "
    "Given a text passage, extract named entities and relationships as JSON. "
    "Return ONLY valid JSON — no markdown, no commentary.\n\n"
    "Schema:\n"
    "{\n"
    '  "entities": [\n'
    '    {"name": "string", "type": "one of: ' + _ENTITY_TYPES + '"}\n'
    "  ],\n"
    '  "relationships": [\n'
    '    {"source": "entity name", "target": "entity name", "type": "one of: ' + _REL_TYPES + '"}\n'
    "  ]\n"
    "}"
)


class KnowledgeGraphService:
    """Orchestrates entity extraction and graph persistence for indexed documents.

    Designed for use inside the indexing pipeline — call build_from_chunks()
    after a document's chunks are saved to SQLite/Qdrant.
    """

    def __init__(self, graph_provider: GraphProvider) -> None:
        self._graph = graph_provider

    async def build_from_chunks(
        self,
        document_id: str,
        chunks: list[str],
    ) -> None:
        """Extract entities/relationships from each chunk and persist to the graph.

        Processing is best-effort: a failure on one chunk does not abort others.
        """
        for i, chunk_text in enumerate(chunks):
            try:
                await self._process_chunk(document_id, chunk_text)
            except Exception as exc:
                logger.warning(
                    "Graph extraction failed for document %s chunk %d: %s",
                    document_id,
                    i,
                    exc,
                )

    async def delete_document(self, document_id: str) -> None:
        """Remove all graph nodes sourced from this document."""
        await self._graph.delete_by_document(document_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _process_chunk(self, document_id: str, text: str) -> None:
        extracted = await self._extract(text)
        if not extracted:
            return

        raw_entities: list[dict[str, Any]] = extracted.get("entities", [])
        raw_rels: list[dict[str, Any]] = extracted.get("relationships", [])

        # Build a name→id map so we can construct relationships by name.
        name_to_id: dict[str, str] = {}
        for raw in raw_entities:
            name = str(raw.get("name", "")).strip()
            if not name:
                continue
            entity_type = _coerce_entity_type(raw.get("type", ""))
            entity_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{document_id}:{name}"))
            entity = Entity(
                id=entity_id,
                name=name,
                entity_type=entity_type,
                source_document_id=document_id,
            )
            await self._graph.upsert_entity(entity)
            name_to_id[name] = entity_id

        for raw in raw_rels:
            source_name = str(raw.get("source", "")).strip()
            target_name = str(raw.get("target", "")).strip()
            rel_type = _coerce_rel_type(raw.get("type", ""))

            source_id = name_to_id.get(source_name)
            target_id = name_to_id.get(target_name)
            if not source_id or not target_id:
                continue

            relationship = Relationship(
                source_id=source_id,
                target_id=target_id,
                relationship_type=rel_type,
            )
            await self._graph.upsert_relationship(relationship)

    async def _extract(self, text: str) -> dict[str, Any] | None:
        """Call the LLM and parse JSON output."""
        messages = [
            {"role": "system", "content": _EXTRACTION_SYSTEM},
            {"role": "user", "content": text[:3000]},  # cap to avoid token overrun
        ]
        try:
            raw = await chat_complete(messages, max_tokens=512, temperature=0.0)
        except Exception as exc:
            logger.debug("LLM call failed during entity extraction: %s", exc)
            return None

        try:
            return json.loads(raw)  # type: ignore[return-value]
        except json.JSONDecodeError:
            # Attempt to extract JSON from within a markdown code fence.
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(raw[start:end])  # type: ignore[return-value]
                except json.JSONDecodeError:
                    pass
            logger.debug("Failed to parse entity extraction response: %s", raw[:200])
            return None


# ------------------------------------------------------------------
# Coercion helpers
# ------------------------------------------------------------------

def _coerce_entity_type(value: Any) -> EntityType:
    try:
        return EntityType(str(value))
    except ValueError:
        return EntityType.CONCEPT


def _coerce_rel_type(value: Any) -> RelationshipType:
    try:
        return RelationshipType(str(value))
    except ValueError:
        return RelationshipType.RELATED_TO
