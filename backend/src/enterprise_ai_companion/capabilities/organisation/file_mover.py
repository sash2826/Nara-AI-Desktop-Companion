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


def _unique_path(path: str) -> str:
    """Return a non-existing path by appending (1), (2), … to the stem."""
    from pathlib import Path as _Path
    p = _Path(path)
    stem, suffix, parent = p.stem, p.suffix, p.parent
    counter = 1
    candidate = path
    while os.path.exists(candidate):
        candidate = str(parent / f"{stem} ({counter}){suffix}")
        counter += 1
    return candidate


class FileMover:
    """Moves indexed files and keeps SQLite records consistent."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def move(
        self,
        source_path: str,
        target_folder: str,
        conflict_strategy: str = "error",
    ) -> str:
        """Move *source_path* into *target_folder*.

        Args:
            source_path: Absolute path of the file to move.
            target_folder: Destination directory.
            conflict_strategy: What to do when a file with the same name
                already exists in the target folder.
                ``"error"``   — raise FileExistsError (default).
                ``"replace"`` — overwrite the existing file.
                ``"rename"``  — keep both by appending `` (N)`` to the stem.

        Returns the new absolute file path.

        Raises:
            FileNotFoundError: if source_path does not exist on disk.
            FileExistsError: if conflict_strategy is "error" and a file with
                the same name already exists in target_folder.
            OSError: for other filesystem errors.
        """
        if not os.path.isfile(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")

        filename = os.path.basename(source_path)
        new_path = os.path.join(target_folder, filename)

        os.makedirs(target_folder, exist_ok=True)

        if os.path.exists(new_path):
            if conflict_strategy == "replace":
                os.remove(new_path)
            elif conflict_strategy == "rename":
                new_path = _unique_path(new_path)
            else:
                raise FileExistsError(
                    f"A file named '{filename}' already exists in "
                    f"'{os.path.basename(target_folder)}'. "
                    "Choose Replace to overwrite it or Keep both to rename the incoming file."
                )

        # Move on disk first; if this fails, no DB record is corrupted.
        shutil.move(source_path, new_path)
        logger.info("Moved file: %s → %s", source_path, new_path)

        # Update the documents table in-place — preserves id, chunks, and
        # all graph_entities that reference this document via source_document_id.
        # workspace_path is also updated to the target folder so that
        # _get_canonical_set_for_folder queries (WHERE workspace_path = ?) can
        # find this document's entities when scoring future recommendations.
        # Wrapped in try-except: the file is already on disk at new_path, so a
        # SQLite failure here must not surface as a 500 to the caller.
        try:
            await self._conn.execute(
                "UPDATE documents SET file_path = ?, workspace_path = ? WHERE file_path = ?",
                (new_path, target_folder, source_path),
            )
            await self._conn.commit()
            logger.debug(
                "SQLite documents updated: file_path %s → %s, workspace_path → %s",
                source_path, new_path, target_folder,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "SQLite update failed after moving %s → %s: %s — "
                "re-indexing the file will reconcile the record.",
                source_path, new_path, exc,
            )

        return new_path
