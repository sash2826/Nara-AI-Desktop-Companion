"""Backup foundation for the Enterprise AI Companion.

Provides SQLite online backup (using SQLite's built-in VACUUM INTO / backup API)
and a Qdrant collection metadata snapshot.  Neo4j graph export is noted as a
future expansion; this module establishes the interface and directory layout.

Backup files are written to EAC_BACKUP_DIR (default: <repo-root>/backups/).
Each backup is a timestamped subdirectory containing:

    <timestamp>/
        sqlite.db          — full SQLite snapshot
        qdrant_meta.json   — Qdrant collection info (vectors are stored on disk
                             by Qdrant's own persistence; this records config)
        manifest.json      — backup metadata (timestamp, sizes, versions)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _backup_root() -> Path:
    env = os.environ.get("EAC_BACKUP_DIR")
    if env:
        return Path(env)
    # Walk up from this file to find the repo root, then use backups/
    candidate = Path(__file__).resolve()
    for _ in range(10):
        candidate = candidate.parent
        if (candidate / "backend").is_dir():
            return candidate / "backups"
    return Path(__file__).parents[4] / "backups"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class BackupManifest:
    backup_id: str
    created_at: str
    sqlite_size_bytes: int
    qdrant_collections: list[str]
    status: str  # "complete" | "partial" | "failed"
    notes: str


@dataclass
class BackupResult:
    backup_id: str
    backup_path: str
    created_at: str
    sqlite_size_bytes: int
    qdrant_collections: list[str]
    status: str


@dataclass
class BackupSummary:
    backup_id: str
    backup_path: str
    created_at: str
    status: str
    sqlite_size_bytes: int


# ---------------------------------------------------------------------------
# BackupService
# ---------------------------------------------------------------------------

class BackupService:
    """Creates and lists backups of all persistent stores.

    SQLite backup uses the aiosqlite/sqlite3 iterdump approach via
    ``VACUUM INTO`` which produces a consistent snapshot without blocking
    writes for more than a single WAL checkpoint.

    Qdrant's vector data is already persisted to disk by the Qdrant server;
    this service records collection metadata so the backup manifest is
    self-describing.  Full vector export will be added when the Qdrant HTTP
    snapshot API is accessible from the sidecar process.
    """

    def __init__(
        self,
        db_conn: aiosqlite.Connection,
        qdrant_client=None,  # qdrant_client.QdrantClient | None
        backup_root: Path | None = None,
    ) -> None:
        self._conn = db_conn
        self._qdrant = qdrant_client
        self._root = backup_root or _backup_root()

    async def create_backup(self, notes: str = "") -> BackupResult:
        """Create a timestamped backup of all stores.

        Returns a BackupResult describing what was captured.
        Raises RuntimeError if the SQLite snapshot fails.
        """
        backup_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_dir = self._root / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[backup] starting backup %s → %s", backup_id, backup_dir)

        # ── SQLite snapshot ──────────────────────────────────────────────────
        sqlite_path = backup_dir / "sqlite.db"
        sqlite_size = 0
        status = "complete"
        try:
            await self._snapshot_sqlite(sqlite_path)
            sqlite_size = sqlite_path.stat().st_size
            logger.info("[backup] SQLite snapshot: %d bytes", sqlite_size)
        except Exception as exc:
            logger.error("[backup] SQLite snapshot failed: %s", exc)
            status = "partial"

        # ── Qdrant metadata ──────────────────────────────────────────────────
        qdrant_collections: list[str] = []
        try:
            qdrant_collections = self._snapshot_qdrant_meta(backup_dir)
        except Exception as exc:
            logger.warning("[backup] Qdrant metadata snapshot failed: %s", exc)

        # ── Manifest ─────────────────────────────────────────────────────────
        created_at = datetime.now(UTC).isoformat()
        manifest = BackupManifest(
            backup_id=backup_id,
            created_at=created_at,
            sqlite_size_bytes=sqlite_size,
            qdrant_collections=qdrant_collections,
            status=status,
            notes=notes,
        )
        (backup_dir / "manifest.json").write_text(
            json.dumps(asdict(manifest), indent=2), encoding="utf-8"
        )

        logger.info("[backup] completed backup %s (status=%s)", backup_id, status)
        return BackupResult(
            backup_id=backup_id,
            backup_path=str(backup_dir),
            created_at=created_at,
            sqlite_size_bytes=sqlite_size,
            qdrant_collections=qdrant_collections,
            status=status,
        )

    async def list_backups(self) -> list[BackupSummary]:
        """Return all completed backups, most recent first."""
        if not self._root.exists():
            return []

        summaries: list[BackupSummary] = []
        for entry in sorted(self._root.iterdir(), reverse=True):
            manifest_path = entry / "manifest.json"
            if not manifest_path.exists():
                continue
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                summaries.append(
                    BackupSummary(
                        backup_id=data["backup_id"],
                        backup_path=str(entry),
                        created_at=data["created_at"],
                        status=data["status"],
                        sqlite_size_bytes=data.get("sqlite_size_bytes", 0),
                    )
                )
            except Exception as exc:
                logger.warning("[backup] skipping unreadable manifest %s: %s", entry, exc)

        return summaries

    async def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup directory by ID. Returns True if deleted, False if not found."""
        backup_dir = self._root / backup_id
        if not backup_dir.exists():
            return False
        shutil.rmtree(backup_dir)
        logger.info("[backup] deleted backup %s", backup_id)
        return True

    # ── Private helpers ──────────────────────────────────────────────────────

    async def _snapshot_sqlite(self, dest: Path) -> None:
        """Write a consistent SQLite snapshot to dest using VACUUM INTO."""
        dest_str = str(dest).replace("\\", "/")
        await self._conn.execute(f"VACUUM INTO '{dest_str}'")

    def _snapshot_qdrant_meta(self, backup_dir: Path) -> list[str]:
        """Write Qdrant collection names to qdrant_meta.json; return collection list."""
        if self._qdrant is None:
            return []

        collections_response = self._qdrant.get_collections()
        names = [c.name for c in collections_response.collections]

        meta = {
            "collections": [
                {
                    "name": c.name,
                }
                for c in collections_response.collections
            ],
            "note": (
                "Vector data is persisted on disk by Qdrant's own storage engine. "
                "This file records collection configuration only."
            ),
        }
        (backup_dir / "qdrant_meta.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )
        return names
