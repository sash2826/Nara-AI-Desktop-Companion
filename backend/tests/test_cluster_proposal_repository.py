"""Integration tests for ClusterProposalRepository.

Uses an in-memory SQLite database with the real migrations applied so that the
SQL schema is always tested against the actual migration file.
"""

from __future__ import annotations

import asyncio

import aiosqlite
import pytest

from enterprise_ai_companion.capabilities.organisation.cluster_proposal_repository import (
    ClusterProposal,
    ClusterProposalRepository,
)
from enterprise_ai_companion.infrastructure.database import _apply_migrations


# ---------------------------------------------------------------------------
# Fixture — in-memory database with migrations applied
# ---------------------------------------------------------------------------

@pytest.fixture
async def repo() -> ClusterProposalRepository:
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await _apply_migrations(conn)
    yield ClusterProposalRepository(conn)
    await conn.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_proposal(
    name: str = "Project Alpha",
    doc_ids: list[str] | None = None,
    paths: list[str] | None = None,
) -> tuple[str, list[str], list[str]]:
    return (
        name,
        doc_ids or ["doc-1", "doc-2"],
        paths or ["/files/report.pdf", "/files/notes.docx"],
    )


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

class TestCreate:
    async def test_returns_proposal_with_pending_status(
        self, repo: ClusterProposalRepository
    ) -> None:
        name, ids, paths = _make_proposal()
        proposal = await repo.create(name, ids, paths)
        assert isinstance(proposal, ClusterProposal)
        assert proposal.status == "pending"

    async def test_proposed_folder_name_stored(
        self, repo: ClusterProposalRepository
    ) -> None:
        proposal = await repo.create("Safety Reports", ["d1"], ["/f/a.pdf"])
        assert proposal.proposed_folder_name == "Safety Reports"

    async def test_document_ids_preserved(
        self, repo: ClusterProposalRepository
    ) -> None:
        ids = ["doc-a", "doc-b", "doc-c"]
        proposal = await repo.create("Test", ids, ["/f/x.pdf"])
        assert proposal.document_ids == ids

    async def test_file_paths_preserved(
        self, repo: ClusterProposalRepository
    ) -> None:
        paths = ["/a/b.pdf", "/c/d.docx"]
        proposal = await repo.create("Test", ["d1"], paths)
        assert proposal.file_paths == paths

    async def test_accepted_folder_is_none_on_create(
        self, repo: ClusterProposalRepository
    ) -> None:
        proposal = await repo.create(*_make_proposal())
        assert proposal.accepted_folder is None

    async def test_resolved_at_is_none_on_create(
        self, repo: ClusterProposalRepository
    ) -> None:
        proposal = await repo.create(*_make_proposal())
        assert proposal.resolved_at is None

    async def test_id_is_a_uuid_string(
        self, repo: ClusterProposalRepository
    ) -> None:
        proposal = await repo.create(*_make_proposal())
        assert len(proposal.id) == 36  # UUID4 hyphenated

    async def test_created_at_is_iso_string(
        self, repo: ClusterProposalRepository
    ) -> None:
        proposal = await repo.create(*_make_proposal())
        # Must parse without error; format is ISO 8601 with UTC offset.
        from datetime import datetime
        datetime.fromisoformat(proposal.created_at)


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

class TestGet:
    async def test_get_returns_created_proposal(
        self, repo: ClusterProposalRepository
    ) -> None:
        proposal = await repo.create(*_make_proposal())
        fetched = await repo.get(proposal.id)
        assert fetched is not None
        assert fetched.id == proposal.id

    async def test_get_unknown_id_returns_none(
        self, repo: ClusterProposalRepository
    ) -> None:
        result = await repo.get("00000000-0000-0000-0000-000000000000")
        assert result is None

    async def test_get_roundtrips_all_fields(
        self, repo: ClusterProposalRepository
    ) -> None:
        name, ids, paths = "Volvo Safety", ["d1", "d2"], ["/p/a.pdf", "/p/b.pdf"]
        original = await repo.create(name, ids, paths)
        fetched = await repo.get(original.id)
        assert fetched is not None
        assert fetched.proposed_folder_name == name
        assert fetched.document_ids == ids
        assert fetched.file_paths == paths
        assert fetched.created_at == original.created_at


# ---------------------------------------------------------------------------
# list_pending / count_pending
# ---------------------------------------------------------------------------

class TestListAndCount:
    async def test_list_pending_empty_initially(
        self, repo: ClusterProposalRepository
    ) -> None:
        assert await repo.list_pending() == []

    async def test_count_pending_zero_initially(
        self, repo: ClusterProposalRepository
    ) -> None:
        assert await repo.count_pending() == 0

    async def test_list_pending_returns_created_proposals(
        self, repo: ClusterProposalRepository
    ) -> None:
        await repo.create(*_make_proposal("A"))
        await repo.create(*_make_proposal("B"))
        pending = await repo.list_pending()
        assert len(pending) == 2

    async def test_count_pending_reflects_creates(
        self, repo: ClusterProposalRepository
    ) -> None:
        await repo.create(*_make_proposal())
        await repo.create(*_make_proposal())
        assert await repo.count_pending() == 2

    async def test_list_pending_ordered_oldest_first(
        self, repo: ClusterProposalRepository
    ) -> None:
        p1 = await repo.create(*_make_proposal("First"))
        p2 = await repo.create(*_make_proposal("Second"))
        pending = await repo.list_pending()
        assert pending[0].id == p1.id
        assert pending[1].id == p2.id

    async def test_accepted_not_in_pending(
        self, repo: ClusterProposalRepository
    ) -> None:
        p = await repo.create(*_make_proposal())
        await repo.set_accepted(p.id, "/workspace/new-folder")
        pending = await repo.list_pending()
        assert all(x.id != p.id for x in pending)

    async def test_dismissed_not_in_pending(
        self, repo: ClusterProposalRepository
    ) -> None:
        p = await repo.create(*_make_proposal())
        await repo.set_dismissed(p.id)
        pending = await repo.list_pending()
        assert all(x.id != p.id for x in pending)

    async def test_count_decrements_after_dismiss(
        self, repo: ClusterProposalRepository
    ) -> None:
        p = await repo.create(*_make_proposal())
        assert await repo.count_pending() == 1
        await repo.set_dismissed(p.id)
        assert await repo.count_pending() == 0


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------

class TestListAll:
    async def test_list_all_includes_all_statuses(
        self, repo: ClusterProposalRepository
    ) -> None:
        p1 = await repo.create(*_make_proposal("Pending"))
        p2 = await repo.create(*_make_proposal("Accepted"))
        p3 = await repo.create(*_make_proposal("Dismissed"))
        await repo.set_accepted(p2.id, "/workspace/accepted-folder")
        await repo.set_dismissed(p3.id)

        all_proposals = await repo.list_all()
        ids = {p.id for p in all_proposals}
        assert {p1.id, p2.id, p3.id} == ids

    async def test_list_all_returns_newest_first(
        self, repo: ClusterProposalRepository
    ) -> None:
        p1 = await repo.create(*_make_proposal("First"))
        p2 = await repo.create(*_make_proposal("Second"))
        all_proposals = await repo.list_all()
        # newest first — p2 created after p1
        assert all_proposals[0].id == p2.id
        assert all_proposals[1].id == p1.id


# ---------------------------------------------------------------------------
# set_accepted
# ---------------------------------------------------------------------------

class TestSetAccepted:
    async def test_status_changes_to_accepted(
        self, repo: ClusterProposalRepository
    ) -> None:
        p = await repo.create(*_make_proposal())
        await repo.set_accepted(p.id, "/workspace/new-folder")
        fetched = await repo.get(p.id)
        assert fetched is not None
        assert fetched.status == "accepted"

    async def test_accepted_folder_is_stored(
        self, repo: ClusterProposalRepository
    ) -> None:
        p = await repo.create(*_make_proposal())
        await repo.set_accepted(p.id, "/workspace/my-folder")
        fetched = await repo.get(p.id)
        assert fetched is not None
        assert fetched.accepted_folder == "/workspace/my-folder"

    async def test_resolved_at_is_set(
        self, repo: ClusterProposalRepository
    ) -> None:
        from datetime import datetime
        p = await repo.create(*_make_proposal())
        await repo.set_accepted(p.id, "/workspace/new-folder")
        fetched = await repo.get(p.id)
        assert fetched is not None
        assert fetched.resolved_at is not None
        datetime.fromisoformat(fetched.resolved_at)  # must be valid ISO string


# ---------------------------------------------------------------------------
# set_dismissed
# ---------------------------------------------------------------------------

class TestSetDismissed:
    async def test_status_changes_to_dismissed(
        self, repo: ClusterProposalRepository
    ) -> None:
        p = await repo.create(*_make_proposal())
        await repo.set_dismissed(p.id)
        fetched = await repo.get(p.id)
        assert fetched is not None
        assert fetched.status == "dismissed"

    async def test_accepted_folder_remains_none_after_dismiss(
        self, repo: ClusterProposalRepository
    ) -> None:
        p = await repo.create(*_make_proposal())
        await repo.set_dismissed(p.id)
        fetched = await repo.get(p.id)
        assert fetched is not None
        assert fetched.accepted_folder is None

    async def test_resolved_at_is_set_on_dismiss(
        self, repo: ClusterProposalRepository
    ) -> None:
        from datetime import datetime
        p = await repo.create(*_make_proposal())
        await repo.set_dismissed(p.id)
        fetched = await repo.get(p.id)
        assert fetched is not None
        assert fetched.resolved_at is not None
        datetime.fromisoformat(fetched.resolved_at)
