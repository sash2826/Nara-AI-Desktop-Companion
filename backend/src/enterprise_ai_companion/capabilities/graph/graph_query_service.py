"""Unified query interface for the knowledge graph.

Consumers call GraphQueryService instead of using Neo4j Cypher directly.
This isolates all graph query logic from the API layer and makes the
queries testable independently of the router.

All methods degrade gracefully when the provider is unavailable (returns
None or empty collections rather than raising).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from enterprise_ai_companion.capabilities.graph.graph_models import (
    Entity,
    GraphContext,
    Relationship,
)
from enterprise_ai_companion.capabilities.graph.graph_provider import GraphProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EntitySearchResult:
    id: str
    name: str
    entity_type: str
    confidence: float
    source_document_id: str


@dataclass(frozen=True)
class GraphNeighborhood:
    """An entity and its N-hop neighbourhood."""
    root: Entity
    neighbours: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)


@dataclass(frozen=True)
class ConnectedDocuments:
    """Documents that contain a particular entity."""
    entity_name: str
    document_ids: list[str] = field(default_factory=list)


class GraphQueryService:
    """Provides high-level graph queries, abstracting Cypher from callers.

    Backed by the GraphProvider interface — works with both Neo4jProvider
    and NullGraphProvider (all methods return empty results for the null case).
    """

    def __init__(self, graph_provider: GraphProvider) -> None:
        self._graph = graph_provider

    async def get_entity(self, name: str) -> GraphContext | None:
        """Return the named entity and its direct neighbourhood (depth 1).

        Returns None when the entity is not found or the provider is offline.
        """
        try:
            return await self._graph.get_context(name, depth=1)
        except Exception as exc:
            logger.warning("GraphQueryService.get_entity(%r) failed: %s", name, exc)
            return None

    async def get_neighborhood(
        self, entity_name: str, depth: int = 2
    ) -> GraphNeighborhood | None:
        """Return entity plus N-hop neighbours.

        Args:
            entity_name: Exact entity name.
            depth: Traversal depth 1–3 (clamped internally).

        Returns:
            GraphNeighborhood or None if the entity does not exist.
        """
        depth = max(1, min(depth, 3))
        try:
            context = await self._graph.get_context(entity_name, depth=depth)
        except Exception as exc:
            logger.warning(
                "GraphQueryService.get_neighborhood(%r) failed: %s", entity_name, exc
            )
            return None

        if context is None:
            return None

        return GraphNeighborhood(
            root=context.entity,
            neighbours=context.related_entities,
            relationships=context.relationships,
        )

    async def search_entities(
        self,
        query: str,
        entity_type: str | None = None,
        limit: int = 10,
    ) -> list[EntitySearchResult]:
        """Substring entity name search, sorted by confidence descending.

        Args:
            query: Substring to search entity names for.
            entity_type: Optional entity type filter (e.g. "Person").
            limit: Maximum results to return (1–50).

        Returns:
            List of matching EntitySearchResult.
        """
        limit = max(1, min(limit, 50))
        try:
            results = await self._graph.search_entities(query, entity_type, limit)
            return [
                EntitySearchResult(
                    id=r["id"],
                    name=r["name"],
                    entity_type=r["entity_type"],
                    confidence=r["confidence"],
                    source_document_id=r["source_document_id"],
                )
                for r in results
            ]
        except Exception as exc:
            logger.warning(
                "GraphQueryService.search_entities(%r) failed: %s", query, exc
            )
            return []

    async def get_connected_documents(self, entity_name: str) -> list[str]:
        """Return all document IDs that contain the named entity (up to 2 hops).

        Used by ContextAssembler to expand retrieval via graph neighbours.
        Returns [] when the entity is not found or the provider is offline.
        """
        try:
            return await self._graph.get_connected_documents(entity_name)
        except Exception as exc:
            logger.warning(
                "GraphQueryService.get_connected_documents(%r) failed: %s",
                entity_name,
                exc,
            )
            return []
