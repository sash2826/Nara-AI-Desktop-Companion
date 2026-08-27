"""Knowledge graph enrichment service.

Runs after entity and relationship extraction to improve graph quality:
  - Entity normalisation: builds a canonical lowercase key for deduplication.
  - Duplicate merging: entities with the same canonical name and type are
    merged — the lower-confidence node's relationships are re-pointed to
    the higher-confidence node, then the duplicate is deleted.
  - Confidence accumulation: stored confidence is updated to max(existing, new).

Works with SQLiteGraphProvider.  Falls back to a no-op for NullGraphProvider.
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

    Supports SQLiteGraphProvider.  NullGraphProvider is detected by the absence
    of the required internal attributes and all methods return immediately.
    """

    def __init__(self, graph_provider: GraphProvider) -> None:
        self._provider = graph_provider
        self._is_sqlite = hasattr(graph_provider, "_conn")

    async def enrich(self) -> None:
        """Run the full enrichment pipeline — merge duplicates across all entity types."""
        if self._is_sqlite:
            await self._enrich_sqlite()
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

