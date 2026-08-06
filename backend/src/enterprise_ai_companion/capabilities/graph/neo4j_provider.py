"""Neo4j-backed knowledge graph provider.

Uses the official Neo4j Python async driver (>=5.0) over the Bolt protocol.
Connection parameters come exclusively from environment variables — credentials
never appear in source code.

Environment variables:
    EAC_NEO4J_URI      Bolt URI, default bolt://localhost:7687
    EAC_NEO4J_USER     Username, default neo4j
    EAC_NEO4J_PASSWORD Password, default eac-dev-password (override in production)
"""

from __future__ import annotations

import logging
import os
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase

from enterprise_ai_companion.capabilities.graph.graph_models import (
    Entity,
    EntityType,
    GraphContext,
    Relationship,
    RelationshipType,
)
from enterprise_ai_companion.capabilities.graph.graph_provider import GraphProvider

logger = logging.getLogger(__name__)

_DEFAULT_URI = "bolt://localhost:7687"
_DEFAULT_USER = "neo4j"
_DEFAULT_PASSWORD = "eac-dev-password"


def _uri() -> str:
    return os.environ.get("EAC_NEO4J_URI", _DEFAULT_URI)


def _auth() -> tuple[str, str]:
    user = os.environ.get("EAC_NEO4J_USER", _DEFAULT_USER)
    password = os.environ.get("EAC_NEO4J_PASSWORD", _DEFAULT_PASSWORD)
    return user, password


class Neo4jProvider(GraphProvider):
    """Knowledge graph backend powered by Neo4j Community 5.x.

    Relationships are stored as directed Bolt edges keyed by RelationshipType.
    Entity merges are idempotent — calling upsert_entity twice with the same id
    updates properties rather than creating duplicates.
    """

    def __init__(self) -> None:
        self._driver: AsyncDriver | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Connect to Neo4j and create uniqueness constraints + indexes."""
        self._driver = AsyncGraphDatabase.driver(_uri(), auth=_auth())
        await self._driver.verify_connectivity()
        await self._apply_schema()
        logger.info("Neo4jProvider connected to %s", _uri())

    async def close(self) -> None:
        if self._driver is not None:
            await self._driver.close()
            self._driver = None

    async def health(self) -> bool:
        if self._driver is None:
            return False
        try:
            await self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Schema bootstrap
    # ------------------------------------------------------------------

    async def _apply_schema(self) -> None:
        """Create uniqueness constraint on Entity.id (idempotent in Neo4j 5)."""
        async with self._driver.session() as session:  # type: ignore[union-attr]
            await session.run(
                "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS "
                "FOR (e:Entity) REQUIRE e.id IS UNIQUE"
            )
            await session.run(
                "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)"
            )

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def upsert_entity(self, entity: Entity) -> None:
        """Merge entity node — creates on first call, updates on subsequent calls."""
        props: dict[str, Any] = {
            "id": entity.id,
            "name": entity.name,
            "entity_type": entity.entity_type.value,
            "source_document_id": entity.source_document_id,
            "confidence": entity.confidence,
            **entity.properties,
        }
        cypher = (
            "MERGE (e:Entity {id: $id}) "
            "SET e += $props, e.entity_type = $entity_type"
        )
        async with self._driver.session() as session:  # type: ignore[union-attr]
            await session.run(
                cypher,
                id=entity.id,
                props=props,
                entity_type=entity.entity_type.value,
            )

    async def upsert_relationship(self, relationship: Relationship) -> None:
        """Create or update a directed relationship between two entity nodes.

        Both nodes must already exist (created via upsert_entity). The relationship
        type is embedded as a Neo4j relationship type label.
        """
        rel_type = relationship.relationship_type.value
        props: dict[str, Any] = {
            "confidence": relationship.confidence,
            **relationship.properties,
        }
        cypher = (
            f"MATCH (src:Entity {{id: $src_id}}), (tgt:Entity {{id: $tgt_id}}) "
            f"MERGE (src)-[r:{rel_type}]->(tgt) "
            f"SET r += $props"
        )
        async with self._driver.session() as session:  # type: ignore[union-attr]
            await session.run(
                cypher,
                src_id=relationship.source_id,
                tgt_id=relationship.target_id,
                props=props,
            )

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_context(self, entity_name: str, depth: int = 1) -> GraphContext | None:
        """Return the named entity plus its neighbourhood up to `depth` hops.

        Depth is capped at 3 to prevent runaway traversals on large graphs.
        """
        depth = min(depth, 3)
        cypher = (
            "MATCH (root:Entity {name: $name}) "
            f"OPTIONAL MATCH (root)-[r*1..{depth}]-(neighbour:Entity) "
            "RETURN root, collect(DISTINCT neighbour) AS neighbours, "
            "collect(DISTINCT r) AS rel_lists"
        )
        async with self._driver.session() as session:  # type: ignore[union-attr]
            result = await session.run(cypher, name=entity_name)
            record = await result.single()

        if record is None:
            return None

        root_node = record["root"]
        entity = _node_to_entity(root_node)

        related_entities = [
            _node_to_entity(n)
            for n in record["neighbours"]
            if n is not None
        ]

        # rel_lists is a list of lists (variable-length path relationships)
        seen_rel_keys: set[tuple[str, str, str]] = set()
        relationships: list[Relationship] = []
        for path_rels in record["rel_lists"]:
            if path_rels is None:
                continue
            rels = path_rels if isinstance(path_rels, list) else [path_rels]
            for rel in rels:
                rel_obj = _rel_to_relationship(rel)
                key = (rel_obj.source_id, rel_obj.target_id, rel_obj.relationship_type.value)
                if key not in seen_rel_keys:
                    seen_rel_keys.add(key)
                    relationships.append(rel_obj)

        return GraphContext(
            entity=entity,
            related_entities=related_entities,
            relationships=relationships,
        )

    async def get_visualization(
        self,
        entity_name: str | None = None,
        depth: int = 2,
    ) -> dict:
        """Return ``{"nodes": [...], "edges": [...]}`` for the graph UI.

        When *entity_name* is given the subgraph is centred on that entity.
        When *None* the most-connected 50 entities are returned as an overview.
        Session A (Epic 5.1+) will enrich this with confidence scores once the
        ExtractedEntity schema is in place. Until then confidence defaults to 1.0.
        """
        depth = min(max(depth, 1), 3)

        if entity_name:
            cypher = (
                "MATCH (root:Entity {name: $name}) "
                f"OPTIONAL MATCH path = (root)-[r*1..{depth}]-(n:Entity) "
                "RETURN collect(DISTINCT root) + collect(DISTINCT n) AS nodes, "
                "       collect(DISTINCT r) AS rel_lists"
            )
            params: dict = {"name": entity_name}
        else:
            cypher = (
                "MATCH (e:Entity) "
                "OPTIONAL MATCH (e)-[r]->(:Entity) "
                "WITH e, count(r) AS deg "
                "ORDER BY deg DESC LIMIT 50 "
                "MATCH (e)-[rel]->(tgt:Entity) "
                "RETURN collect(DISTINCT e) + collect(DISTINCT tgt) AS nodes, "
                "       collect(DISTINCT rel) AS rel_lists"
            )
            params = {}

        async with self._driver.session() as session:  # type: ignore[union-attr]
            result = await session.run(cypher, **params)
            record = await result.single()

        if record is None:
            return {"nodes": [], "edges": []}

        seen_node_ids: set[str] = set()
        nodes: list[dict] = []
        for node in record["nodes"]:
            if node is None:
                continue
            props = dict(node.items())
            nid = props.get("id", str(node.element_id))
            if nid in seen_node_ids:
                continue
            seen_node_ids.add(nid)
            nodes.append({
                "id": nid,
                "label": props.get("name", nid),
                "entity_type": props.get("entity_type", "unknown"),
                "confidence": float(props.get("confidence", 1.0)),
            })

        seen_edge_keys: set[tuple[str, str, str]] = set()
        edges: list[dict] = []
        for path_rels in record["rel_lists"]:
            if path_rels is None:
                continue
            rels = path_rels if isinstance(path_rels, list) else [path_rels]
            for rel in rels:
                props = dict(rel.items())
                src = str(rel.start_node.element_id)
                tgt = str(rel.end_node.element_id)
                rtype = rel.type
                key = (src, tgt, rtype)
                if key in seen_edge_keys:
                    continue
                seen_edge_keys.add(key)
                edges.append({
                    "source": src,
                    "target": tgt,
                    "relation_type": rtype,
                    "confidence": float(props.get("confidence", 1.0)),
                })

        return {"nodes": nodes, "edges": edges}

    async def search_entities(
        self,
        query: str,
        entity_type: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Return entities whose names contain *query* (case-insensitive substring).

        Args:
            query: Substring to search for.
            entity_type: Optional entity type filter.
            limit: Maximum results (1–50).

        Returns:
            List of dicts with id, name, entity_type, confidence, source_document_id.
        """
        if entity_type:
            cypher = (
                "MATCH (e:Entity) "
                "WHERE toLower(e.name) CONTAINS toLower($query) "
                "  AND e.entity_type = $entity_type "
                "RETURN e.id AS id, e.name AS name, e.entity_type AS entity_type, "
                "       e.confidence AS confidence, e.source_document_id AS source_document_id "
                "ORDER BY e.confidence DESC LIMIT $limit"
            )
            params: dict = {"query": query, "entity_type": entity_type, "limit": limit}
        else:
            cypher = (
                "MATCH (e:Entity) "
                "WHERE toLower(e.name) CONTAINS toLower($query) "
                "RETURN e.id AS id, e.name AS name, e.entity_type AS entity_type, "
                "       e.confidence AS confidence, e.source_document_id AS source_document_id "
                "ORDER BY e.confidence DESC LIMIT $limit"
            )
            params = {"query": query, "limit": limit}

        async with self._driver.session() as session:  # type: ignore[union-attr]
            result = await session.run(cypher, **params)
            records = await result.data()

        return [
            {
                "id": r["id"],
                "name": r["name"],
                "entity_type": r["entity_type"] or "Concept",
                "confidence": float(r["confidence"] or 1.0),
                "source_document_id": r["source_document_id"] or "",
            }
            for r in records
        ]

    async def get_connected_documents(self, entity_name: str) -> list[str]:
        """Return document IDs of all entities reachable (up to 2 hops) from entity_name."""
        cypher = (
            "MATCH (root:Entity {name: $name})-[*0..2]-(neighbour:Entity) "
            "WHERE neighbour.source_document_id IS NOT NULL "
            "RETURN collect(DISTINCT neighbour.source_document_id) AS doc_ids"
        )
        async with self._driver.session() as session:  # type: ignore[union-attr]
            result = await session.run(cypher, name=entity_name)
            record = await result.single()

        if record is None:
            return []
        return [str(d) for d in (record["doc_ids"] or []) if d]

    # ------------------------------------------------------------------
    # Delete operations
    # ------------------------------------------------------------------

    async def delete_by_document(self, document_id: str) -> None:
        """Remove all entity nodes (and their relationships) sourced from document_id."""
        cypher = (
            "MATCH (e:Entity {source_document_id: $doc_id}) "
            "DETACH DELETE e"
        )
        async with self._driver.session() as session:  # type: ignore[union-attr]
            await session.run(cypher, doc_id=document_id)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _node_to_entity(node: Any) -> Entity:
    props = dict(node.items())
    try:
        entity_type = EntityType(props.get("entity_type", "Concept"))
    except ValueError:
        entity_type = EntityType.CONCEPT

    extra = {
        k: v for k, v in props.items()
        if k not in {"id", "name", "entity_type", "source_document_id"}
    }
    return Entity(
        id=props["id"],
        name=props["name"],
        entity_type=entity_type,
        source_document_id=props.get("source_document_id", ""),
        properties=extra,
    )


def _rel_to_relationship(rel: Any) -> Relationship:
    rel_type_str: str = rel.type
    try:
        rel_type = RelationshipType(rel_type_str)
    except ValueError:
        rel_type = RelationshipType.RELATED_TO

    props = {k: v for k, v in dict(rel.items()).items()}
    start_node_id = str(rel.start_node.element_id)
    end_node_id = str(rel.end_node.element_id)

    return Relationship(
        source_id=start_node_id,
        target_id=end_node_id,
        relationship_type=rel_type,
        properties=props,
    )
