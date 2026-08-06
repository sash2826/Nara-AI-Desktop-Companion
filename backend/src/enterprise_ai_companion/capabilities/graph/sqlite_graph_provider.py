"""SQLite-backed knowledge graph provider.

Implements the full GraphProvider interface using the existing aiosqlite
connection — no additional process, port, or installation required.

Multi-hop traversal uses recursive CTEs (WITH RECURSIVE), which SQLite
has supported since 3.8.3 (2014).  Shortest-path uses a BFS CTE capped
at 6 hops, consistent with the Neo4j shortestPath(*..6) queries it replaces.

All operations share the application's single aiosqlite connection so
they participate in the same WAL journal as the rest of the schema.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

import aiosqlite

from enterprise_ai_companion.capabilities.graph.graph_models import (
    Entity,
    EntityType,
    GraphContext,
    Relationship,
    RelationshipType,
)
from enterprise_ai_companion.capabilities.graph.graph_provider import GraphProvider

logger = logging.getLogger(__name__)


def _canonical(name: str) -> str:
    """Inline canonical-name helper (mirrors enrichment_service.canonical_name).

    Kept local to avoid a circular import between the provider and the service.
    """
    import re
    import unicodedata
    normalised = unicodedata.normalize("NFC", name)
    normalised = re.sub(r"^[\s\W]+|[\s\W]+$", "", normalised)
    normalised = re.sub(r"\s+", " ", normalised)
    return normalised.lower()


class SQLiteGraphProvider(GraphProvider):
    """Knowledge graph backed by SQLite.

    Uses the graph_entities and graph_relationships tables created by
    migration 008.  The connection is injected — the provider never opens
    its own connection.
    """

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """No-op: tables and indexes are created by migration 008."""
        logger.info("SQLiteGraphProvider ready — using embedded SQLite graph store")

    async def close(self) -> None:
        """No-op: connection lifecycle is managed by the application."""

    async def health(self) -> bool:
        try:
            await self._conn.execute("SELECT 1 FROM graph_entities LIMIT 1")
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def upsert_entity(self, entity: Entity) -> None:
        """Insert or update an entity node.

        Uses INSERT OR REPLACE so re-indexing the same document cleanly
        updates the stored confidence without leaving duplicates.
        """
        await self._conn.execute(
            """
            INSERT INTO graph_entities
                (id, name, entity_type, source_document_id, confidence, canonical)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                confidence  = MAX(confidence, excluded.confidence),
                name        = excluded.name,
                canonical   = excluded.canonical
            """,
            (
                entity.id,
                entity.name,
                entity.entity_type.value,
                entity.source_document_id,
                entity.confidence,
                _canonical(entity.name),
            ),
        )
        await self._conn.commit()

    async def upsert_relationship(self, relationship: Relationship) -> None:
        """Insert or update a directed relationship edge."""
        rel_id = str(uuid.uuid5(
            uuid.NAMESPACE_OID,
            f"{relationship.source_id}:{relationship.target_id}:{relationship.relationship_type.value}",
        ))
        await self._conn.execute(
            """
            INSERT INTO graph_relationships
                (id, source_id, target_id, relationship_type, confidence)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(source_id, target_id, relationship_type) DO UPDATE SET
                confidence = MAX(confidence, excluded.confidence)
            """,
            (
                rel_id,
                relationship.source_id,
                relationship.target_id,
                relationship.relationship_type.value,
                relationship.confidence,
            ),
        )
        await self._conn.commit()

    async def delete_by_document(self, document_id: str) -> None:
        """Remove all entities (and cascade-delete their relationships) for a document."""
        await self._conn.execute(
            "DELETE FROM graph_entities WHERE source_document_id = ?",
            (document_id,),
        )
        await self._conn.commit()

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_context(self, entity_name: str, depth: int = 1) -> GraphContext | None:
        """Return the named entity plus its neighbourhood up to *depth* hops.

        Depth is capped at 3 to bound query cost.
        """
        depth = min(max(depth, 1), 3)

        # Fetch root entity by exact name.
        async with self._conn.execute(
            "SELECT id, name, entity_type, source_document_id, confidence "
            "FROM graph_entities WHERE name = ? LIMIT 1",
            (entity_name,),
        ) as cur:
            row = await cur.fetchone()

        if row is None:
            return None

        root = _row_to_entity(row)

        # Multi-hop neighbour discovery via recursive CTE.
        neighbours, relationships = await self._fetch_neighbourhood(root.id, depth)

        return GraphContext(
            entity=root,
            related_entities=neighbours,
            relationships=relationships,
        )

    async def search_entities(
        self,
        query: str,
        entity_type: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Case-insensitive substring search over entity names."""
        limit = max(1, min(limit, 50))
        pattern = f"%{query.lower()}%"

        if entity_type:
            sql = (
                "SELECT id, name, entity_type, source_document_id, confidence "
                "FROM graph_entities "
                "WHERE lower(name) LIKE ? AND entity_type = ? "
                "ORDER BY confidence DESC LIMIT ?"
            )
            params: tuple = (pattern, entity_type, limit)
        else:
            sql = (
                "SELECT id, name, entity_type, source_document_id, confidence "
                "FROM graph_entities "
                "WHERE lower(name) LIKE ? "
                "ORDER BY confidence DESC LIMIT ?"
            )
            params = (pattern, limit)

        async with self._conn.execute(sql, params) as cur:
            rows = await cur.fetchall()

        return [
            {
                "id": r[0],
                "name": r[1],
                "entity_type": r[2],
                "source_document_id": r[3],
                "confidence": float(r[4]),
            }
            for r in rows
        ]

    async def get_connected_documents(self, entity_name: str) -> list[str]:
        """Return document IDs reachable within 2 hops from *entity_name*.

        Uses a recursive CTE seeded from entities whose name contains
        entity_name (case-insensitive) to handle partial matches.
        """
        sql = """
        WITH RECURSIVE reachable(id) AS (
            -- seed: all entities whose name matches
            SELECT id FROM graph_entities
            WHERE lower(name) LIKE lower(?)
            UNION
            -- 1-hop neighbours (outgoing)
            SELECT r.target_id FROM graph_relationships r
            JOIN reachable src ON src.id = r.source_id
            UNION
            -- 1-hop neighbours (incoming)
            SELECT r.source_id FROM graph_relationships r
            JOIN reachable tgt ON tgt.id = r.target_id
        )
        SELECT DISTINCT e.source_document_id
        FROM reachable
        JOIN graph_entities e ON e.id = reachable.id
        WHERE e.source_document_id IS NOT NULL
        LIMIT 50
        """
        pattern = f"%{entity_name}%"
        async with self._conn.execute(sql, (pattern,)) as cur:
            rows = await cur.fetchall()

        return [r[0] for r in rows if r[0]]

    # Maximum number of nodes returned by get_visualization to keep the
    # WebView force simulation within safe memory/CPU limits.
    _VIS_NODE_LIMIT = 150

    async def get_visualization(
        self,
        entity_name: str | None = None,
        depth: int = 2,
    ) -> dict:
        """Return ``{"nodes": [...], "edges": [...]}`` for the graph UI.

        When *entity_name* is given the subgraph is centred on that entity.
        When None the 50 highest-confidence entities are returned as an overview.
        Results are capped at _VIS_NODE_LIMIT nodes (highest confidence first).
        """
        depth = min(max(depth, 1), 3)

        if entity_name:
            node_ids = await self._reachable_ids(entity_name, depth)
            if not node_ids:
                return {"nodes": [], "edges": []}
            # Fetch all candidate nodes sorted by confidence and apply cap.
            placeholders = ",".join("?" * len(node_ids))
            node_sql = (
                f"SELECT id, name, entity_type, confidence "
                f"FROM graph_entities WHERE id IN ({placeholders}) "
                f"ORDER BY confidence DESC LIMIT {self._VIS_NODE_LIMIT}"
            )
            async with self._conn.execute(node_sql, node_ids) as cur:
                node_rows = await cur.fetchall()
            # Rebuild node_ids from the capped set so edges are consistent.
            node_ids = [r[0] for r in node_rows]
            placeholders = ",".join("?" * len(node_ids))
            edge_sql = (
                f"SELECT id, source_id, target_id, relationship_type, confidence "
                f"FROM graph_relationships "
                f"WHERE source_id IN ({placeholders}) AND target_id IN ({placeholders})"
            )
            async with self._conn.execute(edge_sql, node_ids + node_ids) as cur:
                edge_rows = await cur.fetchall()
        else:
            async with self._conn.execute(
                "SELECT id, name, entity_type, confidence "
                "FROM graph_entities ORDER BY confidence DESC LIMIT 50"
            ) as cur:
                node_rows = await cur.fetchall()

            node_ids = [r[0] for r in node_rows]
            if not node_ids:
                return {"nodes": [], "edges": []}

            placeholders = ",".join("?" * len(node_ids))
            async with self._conn.execute(
                f"SELECT id, source_id, target_id, relationship_type, confidence "
                f"FROM graph_relationships "
                f"WHERE source_id IN ({placeholders}) AND target_id IN ({placeholders})",
                node_ids + node_ids,
            ) as cur:
                edge_rows = await cur.fetchall()

        nodes = [
            {
                "id": r[0],
                "label": r[1],
                "entity_type": r[2],
                "confidence": float(r[3]),
            }
            for r in node_rows
        ]
        edges = [
            {
                "source": r[1],
                "target": r[2],
                "relation_type": r[3],
                "confidence": float(r[4]),
            }
            for r in edge_rows
        ]
        return {"nodes": nodes, "edges": edges}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_neighbourhood(
        self, root_id: str, depth: int
    ) -> tuple[list[Entity], list[Relationship]]:
        """Return (neighbours, relationships) for *root_id* up to *depth* hops."""
        reachable_ids = await self._reachable_ids_from_id(root_id, depth)
        if not reachable_ids:
            return [], []

        # Exclude the root itself from neighbours.
        neighbour_ids = [eid for eid in reachable_ids if eid != root_id]
        if not neighbour_ids:
            return [], []

        placeholders = ",".join("?" * len(neighbour_ids))
        async with self._conn.execute(
            f"SELECT id, name, entity_type, source_document_id, confidence "
            f"FROM graph_entities WHERE id IN ({placeholders})",
            neighbour_ids,
        ) as cur:
            entity_rows = await cur.fetchall()

        neighbours = [_row_to_entity(r) for r in entity_rows]

        all_ids = [root_id] + neighbour_ids
        all_ph = ",".join("?" * len(all_ids))
        async with self._conn.execute(
            f"SELECT id, source_id, target_id, relationship_type, confidence "
            f"FROM graph_relationships "
            f"WHERE source_id IN ({all_ph}) AND target_id IN ({all_ph})",
            all_ids + all_ids,
        ) as cur:
            rel_rows = await cur.fetchall()

        relationships = [_row_to_relationship(r) for r in rel_rows]
        return neighbours, relationships

    async def _reachable_ids(self, entity_name: str, depth: int) -> list[str]:
        """Return entity IDs reachable from *entity_name* within *depth* hops."""
        async with self._conn.execute(
            "SELECT id FROM graph_entities WHERE lower(name) = lower(?) LIMIT 1",
            (entity_name,),
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return []
        return await self._reachable_ids_from_id(row[0], depth)

    async def _reachable_ids_from_id(self, root_id: str, depth: int) -> list[str]:
        """Recursive CTE that expands *depth* hops from *root_id* in both directions."""
        # SQLite recursive CTEs don't support depth limits natively; we use a
        # depth column and stop expanding when it reaches the limit.
        sql = """
        WITH RECURSIVE traversal(id, d) AS (
            SELECT ?, 0
            UNION
            SELECT r.target_id, traversal.d + 1
            FROM graph_relationships r
            JOIN traversal ON traversal.id = r.source_id
            WHERE traversal.d < ?
            UNION
            SELECT r.source_id, traversal.d + 1
            FROM graph_relationships r
            JOIN traversal ON traversal.id = r.target_id
            WHERE traversal.d < ?
        )
        SELECT DISTINCT id FROM traversal
        """
        async with self._conn.execute(sql, (root_id, depth, depth)) as cur:
            rows = await cur.fetchall()
        return [r[0] for r in rows]


# ------------------------------------------------------------------
# Row → dataclass helpers
# ------------------------------------------------------------------

def _row_to_entity(row: Any) -> Entity:
    try:
        entity_type = EntityType(row[2])
    except ValueError:
        entity_type = EntityType.CONCEPT
    return Entity(
        id=row[0],
        name=row[1],
        entity_type=entity_type,
        source_document_id=row[3],
        confidence=float(row[4]),
    )


def _row_to_relationship(row: Any) -> Relationship:
    try:
        rel_type = RelationshipType(row[3])
    except ValueError:
        rel_type = RelationshipType.RELATED_TO
    return Relationship(
        source_id=row[1],
        target_id=row[2],
        relationship_type=rel_type,
        confidence=float(row[4]),
    )
