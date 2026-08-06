"""Knowledge graph enrichment service.

Runs after entity and relationship extraction to improve graph quality:
  - Entity normalisation: builds a canonical lowercase key for deduplication.
  - Duplicate merging: entities with the same canonical name and type are
    merged — the lower-confidence node's relationships are re-pointed to
    the higher-confidence node, then the duplicate is deleted.
  - Confidence accumulation: stored confidence is updated to max(existing, new).

Works with both SQLiteGraphProvider and Neo4jProvider.  Falls back to a
no-op for NullGraphProvider.
"""

from __future__ import annotations

import logging
import re
import unicodedata
import uuid

from enterprise_ai_companion.capabilities.graph.graph_models import EntityType
from enterprise_ai_companion.capabilities.graph.graph_provider import GraphProvider

logger = logging.getLogger(__name__)

# Characters stripped from both ends of an entity name during normalisation.
_STRIP_PATTERN = re.compile(r"^[\s\W]+|[\s\W]+$")


def canonical_name(name: str) -> str:
    """Return a normalised lowercase key suitable for duplicate detection.

    Steps:
    1. Unicode NFC normalisation.
    2. Strip leading/trailing non-word characters and whitespace.
    3. Collapse internal whitespace runs to a single space.
    4. Lowercase.
    """
    normalised = unicodedata.normalize("NFC", name)
    normalised = _STRIP_PATTERN.sub("", normalised)
    normalised = re.sub(r"\s+", " ", normalised)
    return normalised.lower()


class EnrichmentService:
    """Post-extraction enrichment for the knowledge graph.

    Supports SQLiteGraphProvider and Neo4jProvider.  NullGraphProvider is
    detected by the absence of the required internal attributes and all
    methods return immediately.
    """

    def __init__(self, graph_provider: GraphProvider) -> None:
        self._provider = graph_provider
        # Detect provider type by capability rather than isinstance() to avoid
        # import coupling between this service and both provider modules.
        self._is_sqlite = hasattr(graph_provider, "_conn")
        self._is_neo4j = hasattr(graph_provider, "_driver")

    async def enrich(self) -> None:
        """Run the full enrichment pipeline — merge duplicates across all entity types."""
        if self._is_sqlite:
            await self._enrich_sqlite()
        elif self._is_neo4j:
            await self._enrich_neo4j()
        # NullGraphProvider: do nothing

    # ------------------------------------------------------------------
    # SQLite enrichment
    # ------------------------------------------------------------------

    async def _enrich_sqlite(self) -> None:
        conn = self._provider._conn  # noqa: SLF001
        try:
            for entity_type in EntityType:
                await self._merge_duplicates_sqlite(conn, entity_type)
        except Exception as exc:
            logger.warning("EnrichmentService._enrich_sqlite() failed: %s", exc)

    async def _merge_duplicates_sqlite(self, conn, entity_type: EntityType) -> None:
        import aiosqlite  # noqa: PLC0415 — local import avoids top-level dep

        async with conn.execute(
            "SELECT id, name, confidence FROM graph_entities WHERE entity_type = ?",
            (entity_type.value,),
        ) as cur:
            records = await cur.fetchall()

        # Group by canonical name in Python.
        groups: dict[str, list[tuple]] = {}
        for row in records:
            key = canonical_name(str(row[1]))
            groups.setdefault(key, []).append(row)

        for key, members in groups.items():
            if len(members) < 2:
                continue

            canonical = max(members, key=lambda r: (float(r[2] or 0), r[0]))
            duplicates = [m for m in members if m[0] != canonical[0]]

            for dup in duplicates:
                dup_id, canonical_id = dup[0], canonical[0]
                try:
                    # Collect relationships that need re-pointing before modifying anything.
                    async with conn.execute(
                        "SELECT id, source_id, target_id, relationship_type, confidence "
                        "FROM graph_relationships "
                        "WHERE (source_id = ? AND target_id != ?) "
                        "   OR (target_id = ? AND source_id != ?)",
                        (dup_id, canonical_id, dup_id, canonical_id),
                    ) as cur:
                        affected = await cur.fetchall()

                    # Delete the old rows first so we can re-insert with correct IDs.
                    await conn.execute(
                        "DELETE FROM graph_relationships WHERE source_id = ? OR target_id = ?",
                        (dup_id, dup_id),
                    )

                    # Re-insert with re-pointed endpoints and recomputed uuid5 id.
                    for row in affected:
                        old_src = canonical_id if row[1] == dup_id else row[1]
                        old_tgt = canonical_id if row[2] == dup_id else row[2]
                        if old_src == old_tgt:
                            continue  # skip self-loops
                        new_id = str(uuid.uuid5(
                            uuid.NAMESPACE_OID,
                            f"{old_src}:{old_tgt}:{row[3]}",
                        ))
                        await conn.execute(
                            "INSERT OR IGNORE INTO graph_relationships "
                            "(id, source_id, target_id, relationship_type, confidence) "
                            "VALUES (?, ?, ?, ?, ?)",
                            (new_id, old_src, old_tgt, row[3], row[4]),
                        )

                    # Delete the duplicate node (CASCADE removes any remaining edges).
                    await conn.execute(
                        "DELETE FROM graph_entities WHERE id = ?", (dup_id,)
                    )
                    await conn.commit()
                    logger.debug(
                        "Merged duplicate entity '%s' (%s) → id=%s",
                        dup[1], entity_type.value, canonical_id,
                    )
                except Exception as exc:
                    logger.warning(
                        "Failed to merge duplicate entity %s → %s: %s",
                        dup_id, canonical_id, exc,
                    )

    # ------------------------------------------------------------------
    # Neo4j enrichment (unchanged from previous implementation)
    # ------------------------------------------------------------------

    async def _enrich_neo4j(self) -> None:
        try:
            for entity_type in EntityType:
                await self._merge_duplicates_neo4j(entity_type)
        except Exception as exc:
            logger.warning("EnrichmentService._enrich_neo4j() failed: %s", exc)

    async def _merge_duplicates_neo4j(self, entity_type: EntityType) -> None:
        from enterprise_ai_companion.capabilities.graph.neo4j_provider import Neo4jProvider  # noqa: PLC0415
        provider: Neo4jProvider = self._provider  # type: ignore[assignment]
        driver = provider._driver  # noqa: SLF001
        if driver is None:
            return

        fetch_cypher = (
            "MATCH (e:Entity {entity_type: $entity_type}) "
            "RETURN e.id AS id, e.name AS name, e.confidence AS confidence"
        )
        async with driver.session() as session:
            result = await session.run(fetch_cypher, entity_type=entity_type.value)
            records = await result.data()

        groups: dict[str, list[dict]] = {}
        for record in records:
            key = canonical_name(str(record["name"]))
            groups.setdefault(key, []).append(record)

        for key, members in groups.items():
            if len(members) < 2:
                continue
            canonical = max(members, key=lambda r: (float(r["confidence"] or 0), r["id"]))
            duplicates = [m for m in members if m["id"] != canonical["id"]]
            for dup in duplicates:
                await self._merge_node_into_neo4j(driver, dup["id"], canonical["id"])
                logger.debug(
                    "Merged duplicate entity '%s' (%s) → canonical id=%s",
                    dup["name"], entity_type.value, canonical["id"],
                )

    async def _merge_node_into_neo4j(self, driver, duplicate_id: str, canonical_id: str) -> None:
        async with driver.session() as session:
            await session.run(
                "MATCH (dup:Entity {id: $dup_id})-[r]->(other) "
                "WHERE other.id <> $canonical_id "
                "MATCH (canonical:Entity {id: $canonical_id}) "
                "MERGE (canonical)-[r2]->(other) "
                "ON CREATE SET r2 = properties(r)",
                dup_id=duplicate_id, canonical_id=canonical_id,
            )
            await session.run(
                "MATCH (other)-[r]->(dup:Entity {id: $dup_id}) "
                "WHERE other.id <> $canonical_id "
                "MATCH (canonical:Entity {id: $canonical_id}) "
                "MERGE (other)-[r2]->(canonical) "
                "ON CREATE SET r2 = properties(r)",
                dup_id=duplicate_id, canonical_id=canonical_id,
            )
            await session.run(
                "MATCH (e:Entity {id: $dup_id}) DETACH DELETE e",
                dup_id=duplicate_id,
            )
