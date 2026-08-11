"""Physical file mover for accepted placement recommendations.

Moves a file from its current location to the target folder, then updates
the SQLite documents table in-place so all chunk associations, IDs, and
Qdrant vector point IDs remain valid. No re-indexing is required.

Note: The Qdrant payload does NOT store document_path directly — it is
looked up from SQLite at search time. Only the SQLite record needs updating.
"""

from __future__ import annotations

import logging
import os
import shutil

import aiosqlite

logger = logging.getLogger(__name__)


class FileMover:
    """Moves indexed files and keeps SQLite records consistent."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def move(self, source_path: str, target_folder: str) -> str:
        """Move *source_path* into *target_folder*.

        Returns the new absolute file path.

        Raises:
            FileNotFoundError: if source_path does not exist on disk.
            FileExistsError: if a file with the same name already exists in target_folder.
            OSError: for other filesystem errors.
        """
        if not os.path.isfile(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")

        filename = os.path.basename(source_path)
        new_path = os.path.join(target_folder, filename)

        if os.path.exists(new_path):
            raise FileExistsError(
                f"A file named '{filename}' already exists in '{target_folder}'. "
                "Resolve the conflict before accepting this recommendation."
            )

        os.makedirs(target_folder, exist_ok=True)

        # Move on disk first; if this fails, no DB record is corrupted.
        shutil.move(source_path, new_path)
        logger.info("Moved file: %s → %s", source_path, new_path)

        # Update the documents table in-place — preserves id, chunks, and
        # all graph_entities that reference this document via source_document_id.
        await self._conn.execute(
            "UPDATE documents SET file_path = ? WHERE file_path = ?",
            (new_path, source_path),
        )
        await self._conn.commit()
        logger.debug("SQLite documents.file_path updated: %s → %s", source_path, new_path)

        return new_path
