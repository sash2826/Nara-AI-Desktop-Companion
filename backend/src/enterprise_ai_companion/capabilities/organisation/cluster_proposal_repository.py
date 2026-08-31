"""CRUD repository for cluster-based folder-creation proposals (migration 016).

A ClusterProposal is created by ClusterDiscoveryService when a semantic cluster
of floating files is detected. It stays 'pending' until the user accepts (the
files are physically moved and the new folder is created) or dismisses it via
the Organise dashboard. Accepted proposals record the final folder path, which
may differ from the original proposed name if the user edits it.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClusterProposal:
    """A single folder-creation proposal derived from a semantic cluster."""

    id: str
    status: str  # "pending" | "accepted" | "dismissed"
    proposed_folder_name: str
    document_ids: list[str]
    file_paths: list[str]
    accepted_folder: str | None
    created_at: str
    resolved_at: str | None


class ClusterProposalRepository:
    """Persists and retrieves cluster-based folder proposals from SQLite."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create(
        self,
        proposed_folder_name: str,
        document_ids: list[str],
        file_paths: list[str],
    ) -> ClusterProposal:
        """Persist a new pending proposal and return it."""
        proposal_id = str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat()

        await self._conn.execute(
            """
            INSERT INTO cluster_proposals
                (id, status, proposed_folder_name, document_ids, file_paths,
                 accepted_folder, created_at, resolved_at)
            VALUES (?, 'pending', ?, ?, ?, NULL, ?, NULL)
            """,
            (
                proposal_id,
                proposed_folder_name,
                json.dumps(document_ids),
                json.dumps(file_paths),
                created_at,
            ),
        )
        await self._conn.commit()

        logger.info(
            "Created cluster proposal %s: folder=%r, %d file(s)",
            proposal_id,
            proposed_folder_name,
            len(file_paths),
        )
        return ClusterProposal(
            id=proposal_id,
            status="pending",
            proposed_folder_name=proposed_folder_name,
            document_ids=list(document_ids),
            file_paths=list(file_paths),
            accepted_folder=None,
            created_at=created_at,
            resolved_at=None,
        )

    async def get(self, proposal_id: str) -> ClusterProposal | None:
        """Return a single proposal by ID, or None if not found."""
        async with self._conn.execute(
            "SELECT id, status, proposed_folder_name, document_ids, file_paths, "
            "accepted_folder, created_at, resolved_at "
            "FROM cluster_proposals WHERE id = ?",
            (proposal_id,),
        ) as cur:
            row = await cur.fetchone()

        if row is None:
            return None
        return _row_to_proposal(row)

    async def list_pending(self) -> list[ClusterProposal]:
        """Return all proposals with status='pending', oldest first."""
        async with self._conn.execute(
            "SELECT id, status, proposed_folder_name, document_ids, file_paths, "
            "accepted_folder, created_at, resolved_at "
            "FROM cluster_proposals WHERE status = 'pending' ORDER BY created_at ASC"
        ) as cur:
            rows = await cur.fetchall()
        return [_row_to_proposal(r) for r in rows]

    async def list_all(self) -> list[ClusterProposal]:
        """Return all proposals regardless of status, newest first."""
        async with self._conn.execute(
            "SELECT id, status, proposed_folder_name, document_ids, file_paths, "
            "accepted_folder, created_at, resolved_at "
            "FROM cluster_proposals ORDER BY created_at DESC"
        ) as cur:
            rows = await cur.fetchall()
        return [_row_to_proposal(r) for r in rows]

    async def count_pending(self) -> int:
        """Return the number of pending proposals."""
        async with self._conn.execute(
            "SELECT COUNT(*) FROM cluster_proposals WHERE status = 'pending'"
        ) as cur:
            row = await cur.fetchone()
        return int(row[0]) if row else 0

    async def set_accepted(self, proposal_id: str, accepted_folder: str) -> None:
        """Mark a proposal as accepted, recording the folder that was created."""
        resolved_at = datetime.now(UTC).isoformat()
        await self._conn.execute(
            "UPDATE cluster_proposals "
            "SET status='accepted', accepted_folder=?, resolved_at=? WHERE id=?",
            (accepted_folder, resolved_at, proposal_id),
        )
        await self._conn.commit()
        logger.info(
            "Cluster proposal %s accepted → %s", proposal_id, accepted_folder
        )

    async def set_dismissed(self, proposal_id: str) -> None:
        """Mark a proposal as dismissed (no folder created)."""
        resolved_at = datetime.now(UTC).isoformat()
        await self._conn.execute(
            "UPDATE cluster_proposals "
            "SET status='dismissed', resolved_at=? WHERE id=?",
            (resolved_at, proposal_id),
        )
        await self._conn.commit()
        logger.info("Cluster proposal %s dismissed", proposal_id)


def _row_to_proposal(row: Any) -> ClusterProposal:
    def _load_json_list(value: Any) -> list[str]:
        try:
            parsed = json.loads(value) if value else []
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    return ClusterProposal(
        id=row[0],
        status=row[1],
        proposed_folder_name=row[2],
        document_ids=_load_json_list(row[3]),
        file_paths=_load_json_list(row[4]),
        accepted_folder=row[5],
        created_at=row[6],
        resolved_at=row[7],
    )
