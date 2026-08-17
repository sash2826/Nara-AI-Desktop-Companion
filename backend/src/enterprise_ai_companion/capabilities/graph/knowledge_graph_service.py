"""Orchestrates entity/relationship extraction and graph persistence for indexed documents.

The extraction pipeline per chunk:
  1. EntityExtractor  — LLM call → list[ExtractedEntity]
  2. RelationshipExtractor — LLM call → list[ExtractedRelationship]
  3. Persist entities → Neo4j (or NullGraphProvider)
  4. Persist relationships → Neo4j

All steps are best-effort: a failure on one chunk never aborts the others and
never propagates up to the caller (FileIndexer wraps the call in its own guard).
"""

from __future__ import annotations

import logging
import uuid

from enterprise_ai_companion.capabilities.graph.enrichment_service import EnrichmentService
from enterprise_ai_companion.capabilities.graph.entity_extractor import EntityExtractor
from enterprise_ai_companion.capabilities.graph.graph_models import (
    Entity,
    ExtractedEntity,
    Relationship,
)
from enterprise_ai_companion.capabilities.graph.graph_provider import GraphProvider
from enterprise_ai_companion.capabilities.graph.relationship_extractor import RelationshipExtractor

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Orchestrates entity extraction and graph persistence for indexed documents.

    Designed for use inside the indexing pipeline — call build_from_chunks()
    after a document's chunks are saved to SQLite/Qdrant.
    """

    def __init__(
        self,
        graph_provider: GraphProvider,
        entity_extractor: EntityExtractor | None = None,
        relationship_extractor: RelationshipExtractor | None = None,
        enrichment_service: EnrichmentService | None = None,
    ) -> None:
        self._graph = graph_provider
        self._entity_extractor = entity_extractor or EntityExtractor()
        self._relationship_extractor = relationship_extractor or RelationshipExtractor()
        self._enrichment = enrichment_service or EnrichmentService(graph_provider)

    async def build_from_chunks(
        self,
        document_id: str,
        chunks: list[str],
    ) -> None:
        """Extract entities/relationships from each chunk and persist to the graph.

        After all chunks are processed, runs the enrichment pass (duplicate
        merge, confidence update). Processing is best-effort throughout.
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

        # Enrichment is best-effort — failure must not propagate to FileIndexer.
        try:
            await self._enrichment.enrich()
        except Exception as exc:
            logger.warning("Graph enrichment failed for document %s: %s", document_id, exc)

    async def delete_document(self, document_id: str) -> None:
        """Remove all graph nodes and relationships sourced from this document."""
        await self._graph.delete_by_document(document_id)

    async def link_shared_entities(self, max_shared_docs: int = 20) -> int:
        """Create SIMILAR_TO edges between entities sharing a canonical name across documents.

        Best called once after a full workspace index rather than after each file.
        Returns the number of new edges created.
        """
        try:
            return await self._graph.link_shared_entities(max_shared_docs)
        except Exception as exc:
            logger.warning("link_shared_entities failed: %s", exc)
            return 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _process_chunk(self, document_id: str, text: str) -> None:
        # Step 1 — entity extraction.
        extracted_entities = await self._entity_extractor.extract(text)
        if not extracted_entities:
            return

        # Step 2 — build name→id map and persist entities.
        name_to_id: dict[str, str] = {}
        for extracted in extracted_entities:
            entity_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{document_id}:{extracted.name}"))
            entity = Entity(
                id=entity_id,
                name=extracted.name,
                entity_type=extracted.entity_type,
                source_document_id=document_id,
                confidence=extracted.confidence,
            )
            await self._graph.upsert_entity(entity)
            name_to_id[extracted.name] = entity_id
            # Map by lowercase for relationship lookup resilience.
            name_to_id[extracted.name.lower()] = entity_id

        # Step 3 — relationship extraction (best-effort; failure does not lose entities).
        try:
            extracted_rels = await self._relationship_extractor.extract(
                text, extracted_entities
            )
        except Exception as exc:
            logger.warning(
                "Relationship extraction failed for document %s: %s", document_id, exc
            )
            extracted_rels = []

        # Step 4 — persist relationships.
        for extracted_rel in extracted_rels:
            source_id = name_to_id.get(extracted_rel.source_name) or name_to_id.get(
                extracted_rel.source_name.lower()
            )
            target_id = name_to_id.get(extracted_rel.target_name) or name_to_id.get(
                extracted_rel.target_name.lower()
            )
            if not source_id or not target_id:
                continue

            relationship = Relationship(
                source_id=source_id,
                target_id=target_id,
                relationship_type=extracted_rel.relationship_type,
                confidence=extracted_rel.confidence,
            )
            await self._graph.upsert_relationship(relationship)
