"""Repository for persisting and querying discovered abbreviations.

Abbreviation rows are written by the indexing pipeline after each file is
processed and read back at query time by the ``QueryPreprocessor`` to
supplement its static expansion dictionary.

The table schema is defined in ``database/migrations/006_abbreviations.sql``.
The composite primary key ``(abbreviation, document_id)`` ensures that
re-indexing a document replaces its existing rows cleanly via
``INSERT OR REPLACE``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import aiosqlite

from enterprise_ai_companion.capabilities.retrieval.abbreviation_extractor import (
    AbbreviationMatch,
)

logger = logging.getLogger(__name__)


class AbbreviationRepository:
    """Async repository for the ``abbreviations`` table.

    Args:
        conn: An open ``aiosqlite.Connection`` managed by the application
            lifespan.  The repository never opens or closes the connection.
    """

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def save_batch(
        self,
        document_id: str,
        matches: list[AbbreviationMatch],
    ) -> None:
        """Persist a batch of abbreviation matches for a single document.

        Uses ``INSERT OR REPLACE`` so re-indexing the same document cleanly
        overwrites its previous entries.  Call ``delete_by_document`` first if
        you need to remove abbreviations that no longer appear in the updated
        file.

        Args:
            document_id: UUID of the parent document (must exist in
                ``documents`` table).
            matches: Extracted abbreviation–definition pairs.
        """
        if not matches:
            return

        now = datetime.now(timezone.utc).isoformat()
        rows = [
            (m.abbreviation, m.definition, document_id, now)
            for m in matches
        ]

        await self._conn.executemany(
            """
            INSERT OR REPLACE INTO abbreviations
                (abbreviation, definition, document_id, discovered_at)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )
        await self._conn.commit()
        logger.debug(
            "Saved %d abbreviation(s) for document %s", len(rows), document_id
        )

    async def delete_by_document(self, document_id: str) -> None:
        """Remove all abbreviation rows for the given document.

        Called before re-indexing a document so stale abbreviations that no
        longer appear in the updated content are not retained.

        Args:
            document_id: UUID of the parent document.
        """
        await self._conn.execute(
            "DELETE FROM abbreviations WHERE document_id = ?",
            (document_id,),
        )
        await self._conn.commit()
        logger.debug("Deleted abbreviations for document %s", document_id)

    async def load_all(self) -> dict[str, list[str]]:
        """Load all discovered abbreviations across every document.

        Returns a mapping suitable for passing directly to
        ``QueryPreprocessor.merge_expansions()``.

        Returns:
            ``{lowercase_abbreviation: [definition, ...]}`` where each value
            list is deduplicated and preserves insertion order.  An
            abbreviation found with different definitions across multiple
            documents will have all definitions listed.
        """
        async with self._conn.execute(
            "SELECT DISTINCT abbreviation, definition FROM abbreviations"
        ) as cursor:
            rows = await cursor.fetchall()

        result: dict[str, list[str]] = {}
        for abbr, definition in rows:
            if abbr not in result:
                result[abbr] = []
            if definition not in result[abbr]:
                result[abbr].append(definition)

        logger.debug("Loaded %d unique abbreviation entries from DB", len(result))
        return result
