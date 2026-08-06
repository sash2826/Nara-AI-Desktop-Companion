"""Abstract interface for the knowledge graph provider.

Business logic depends on this interface — never on a specific backend.
This allows SQLiteGraphProvider, NullGraphProvider, and Neo4jProvider to
be swapped without touching any capability code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from enterprise_ai_companion.capabilities.graph.graph_models import (
    Entity,
    GraphContext,
    Relationship,
)


class GraphProvider(ABC):
    """Defines the contract for all graph storage backends."""

    @abstractmethod
    async def initialize(self) -> None:
        """Set up indexes and constraints. Safe to call multiple times."""

    @abstractmethod
    async def upsert_entity(self, entity: Entity) -> None:
        """Create or update an entity node."""

    @abstractmethod
    async def upsert_relationship(self, relationship: Relationship) -> None:
        """Create or update a relationship between two entity nodes."""

    @abstractmethod
    async def get_context(self, entity_name: str, depth: int = 1) -> GraphContext | None:
        """Return the entity and its neighbourhood up to `depth` hops."""

    @abstractmethod
    async def search_entities(
        self,
        query: str,
        entity_type: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Return entities whose names contain *query* (case-insensitive).

        Each dict has keys: id, name, entity_type, confidence, source_document_id.
        Returns [] when no matches are found.
        """

    @abstractmethod
    async def get_connected_documents(self, entity_name: str) -> list[str]:
        """Return document IDs reachable from *entity_name* within 2 hops.

        Returns [] when the entity is not found.
        """

    @abstractmethod
    async def delete_by_document(self, document_id: str) -> None:
        """Remove all entities and relationships sourced from a document."""

    @abstractmethod
    async def health(self) -> bool:
        """Return True if the provider is connected and operational."""

    @abstractmethod
    async def get_visualization(
        self,
        entity_name: str | None = None,
        depth: int = 2,
    ) -> dict:
        """Return serialisable ``{"nodes": [...], "edges": [...]}`` for the UI.

        When *entity_name* is provided the subgraph is centred on that entity.
        When *None* an overview of the most-connected nodes is returned.
        Implementations must return an empty dict structure rather than raising
        when the graph is empty.
        """

    @abstractmethod
    async def close(self) -> None:
        """Release all connections."""
