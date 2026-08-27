"""Graph traversal engine for path-finding and connected component discovery.

Provides higher-level traversal operations above the GraphProvider interface.
Supports SQLiteGraphProvider (recursive CTE path-finding). Returns empty/not-found
results gracefully for NullGraphProvider.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from enterprise_ai_companion.capabilities.graph.graph_provider import GraphProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GraphPath:
    """A shortest path between two named entities."""
    source_name: str
    target_name: str
    node_names: list[str] = field(default_factory=list)
    length: int = 0
    found: bool = False


class TraversalEngine:
    """Implements path-finding and connected-component traversal.

    Detects the provider type at construction time and routes each operation
    to the appropriate implementation.
    """

    def __init__(self, graph_provider: GraphProvider) -> None:
        self._provider = graph_provider
        self._is_sqlite = hasattr(graph_provider, "_conn")

    async def find_path(self, source_name: str, target_name: str) -> GraphPath:
        """Find the shortest path between two named entities (max 6 hops).

        Returns:
            GraphPath — check .found to know whether a path exists.
        """
        if self._is_sqlite:
            return await self._find_path_sqlite(source_name, target_name)
        return GraphPath(source_name=source_name, target_name=target_name)

    async def get_connected_documents(self, entity_name: str) -> list[str]:
        """Return document IDs of all entities reachable from entity_name.

        Traverses the graph up to 2 hops from the named entity.
        """
        if self._is_sqlite:
            return await self._connected_documents_sqlite(entity_name)
        return []

    # ------------------------------------------------------------------
    # SQLite implementations
    # ------------------------------------------------------------------

    async def _find_path_sqlite(self, source_name: str, target_name: str) -> GraphPath:
        conn = self._provider._conn  # noqa: SLF001

        # Resolve names → IDs.
        async with conn.execute(
            "SELECT id FROM graph_entities WHERE lower(name) = lower(?) LIMIT 1",
            (source_name,),
        ) as cur:
            src_row = await cur.fetchone()

        async with conn.execute(
            "SELECT id FROM graph_entities WHERE lower(name) = lower(?) LIMIT 1",
            (target_name,),
        ) as cur:
            tgt_row = await cur.fetchone()

        if src_row is None or tgt_row is None:
            return GraphPath(source_name=source_name, target_name=target_name)

        src_id, tgt_id = src_row[0], tgt_row[0]
        if src_id == tgt_id:
            return GraphPath(
                source_name=source_name,
                target_name=target_name,
                node_names=[source_name],
                length=0,
                found=True,
            )

        # BFS via recursive CTE, tracking the path as a JSON-encoded list of IDs.
        # SQLite doesn't have array types so we encode the path as pipe-delimited text.
        sql = """
        WITH RECURSIVE bfs(id, path, depth) AS (
            SELECT ?, ?, 0
            UNION ALL
            SELECT
                CASE
                    WHEN r1.target_id IS NOT NULL THEN r1.target_id
                    ELSE r2.source_id
                END,
                bfs.path || '|' || CASE
                    WHEN r1.target_id IS NOT NULL THEN r1.target_id
                    ELSE r2.source_id
                END,
                bfs.depth + 1
            FROM bfs
            LEFT JOIN graph_relationships r1 ON r1.source_id = bfs.id
            LEFT JOIN graph_relationships r2 ON r2.target_id = bfs.id
            WHERE bfs.depth < 6
              AND bfs.path NOT LIKE '%' || CASE
                    WHEN r1.target_id IS NOT NULL THEN r1.target_id
                    ELSE r2.source_id
                END || '%'
              AND (r1.target_id IS NOT NULL OR r2.source_id IS NOT NULL)
        )
        SELECT path, depth FROM bfs WHERE id = ? ORDER BY depth LIMIT 1
        """
        try:
            async with conn.execute(sql, (src_id, src_id, tgt_id)) as cur:
                row = await cur.fetchone()
        except Exception as exc:
            logger.warning("TraversalEngine._find_path_sqlite failed: %s", exc)
            return GraphPath(source_name=source_name, target_name=target_name)

        if row is None:
            return GraphPath(source_name=source_name, target_name=target_name)

        path_ids = row[0].split("|")
        length = int(row[1])

        # Resolve IDs → names.
        placeholders = ",".join("?" * len(path_ids))
        async with conn.execute(
            f"SELECT id, name FROM graph_entities WHERE id IN ({placeholders})",
            path_ids,
        ) as cur:
            name_map = {r[0]: r[1] for r in await cur.fetchall()}

        node_names = [name_map.get(eid, eid) for eid in path_ids]

        return GraphPath(
            source_name=source_name,
            target_name=target_name,
            node_names=node_names,
            length=length,
            found=True,
        )

    async def _connected_documents_sqlite(self, entity_name: str) -> list[str]:
        """Delegate to the provider — it already implements 2-hop traversal."""
        return await self._provider.get_connected_documents(entity_name)

