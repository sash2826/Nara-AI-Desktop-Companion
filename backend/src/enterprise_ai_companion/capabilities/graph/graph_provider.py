"""Abstract interface for the knowledge graph provider.

Business logic depends on this interface — never on Neo4j directly.
This allows the NullGraphProvider stub to keep the app runnable without
a running Neo4j instance, and enables future provider swaps without
touching any capability code.
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
    async def delete_by_document(self, document_id: str) -> None:
        """Remove all entities and relationships sourced from a document."""

    @abstractmethod
    async def health(self) -> bool:
        """Return True if the provider is connected and operational."""

    @abstractmethod
    async def close(self) -> None:
        """Release all connections."""
