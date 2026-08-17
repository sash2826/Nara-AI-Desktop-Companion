"""No-op graph provider used when Neo4j is unavailable.

Keeps the application fully functional without a running Neo4j instance.
Graph-dependent features silently return empty results rather than failing.
Replace with Neo4jProvider by setting EAC_GRAPH_PROVIDER=neo4j.
"""

from __future__ import annotations

import logging

from enterprise_ai_companion.capabilities.graph.graph_models import (
    Entity,
    GraphContext,
    Relationship,
)
from enterprise_ai_companion.capabilities.graph.graph_provider import GraphProvider

logger = logging.getLogger(__name__)


class NullGraphProvider(GraphProvider):
    async def initialize(self) -> None:
        logger.info("NullGraphProvider active — graph features disabled.")

    async def upsert_entity(self, entity: Entity) -> None:
        pass

    async def upsert_relationship(self, relationship: Relationship) -> None:
        pass

    async def get_context(self, entity_name: str, depth: int = 1) -> GraphContext | None:
        return None

    async def delete_by_document(self, document_id: str) -> None:
        pass

    async def health(self) -> bool:
        return True

    async def get_visualization(
        self,
        entity_name: str | None = None,
        depth: int = 2,
    ) -> dict:
        return {"nodes": [], "edges": []}

    async def search_entities(
        self,
        query: str,
        entity_type: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        return []  # type: ignore[return-value]

    async def get_connected_documents(self, entity_name: str) -> list[str]:
        return []

    async def link_shared_entities(self, max_shared_docs: int = 20) -> int:
        return 0

    async def close(self) -> None:
        pass
