"""Unit tests for ClusterDiscoveryService.

All dependencies are replaced by lightweight in-memory fakes so no database,
Qdrant, or filesystem access is required.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from typing import Any

import pytest

from enterprise_ai_companion.capabilities.organisation.cluster_discovery_service import (
    ClusterDiscoveryService,
)
from enterprise_ai_companion.capabilities.organisation.cluster_engine import ClusterEngine
from enterprise_ai_companion.capabilities.organisation.cluster_proposal_repository import (
    ClusterProposal,
    ClusterProposalRepository,
)
from enterprise_ai_companion.capabilities.organisation.cluster_scorer import ClusterScorer
from enterprise_ai_companion.capabilities.organisation.document_vector_service import (
    DocumentVectorService,
)
from enterprise_ai_companion.capabilities.organisation.floating_file_filter import (
    FloatingFileFilter,
)
from enterprise_ai_companion.capabilities.organisation.folder_naming_service import (
    FolderNamingService,
)
from enterprise_ai_companion.capabilities.organisation.placement_ports import GraphScorePort
from enterprise_ai_companion.capabilities.organisation.recommendation_repository import (
    RecommendationRepository,
)
import aiosqlite
from enterprise_ai_companion.infrastructure.database import _apply_migrations


# ---------------------------------------------------------------------------
# Fakes — minimal viable stubs
# ---------------------------------------------------------------------------

@dataclass
class _FakeDoc:
    id: str
    file_path: str
    file_hash: str = ""
    workspace_path: str = ""


class _FakeWatcher:
    def __init__(self, paths: list[str]) -> None:
        self._paths = paths

    async def list_folders(self):  # type: ignore[override]
        @dataclass
        class _Folder:
            path: str
        return [_Folder(p) for p in self._paths]


class _FakeFloatingFilter:
    def __init__(self, docs: list[_FakeDoc]) -> None:
        self._docs = docs

    async def get_floating_candidates(self, leaf_folders: list[str]) -> list[_FakeDoc]:
        return self._docs


class _FakeVectorService:
    def __init__(self, vectors: dict[str, list[float]]) -> None:
        self._vectors = vectors

    async def get_vectors(self, doc_ids: list[str]) -> dict[str, list[float]]:
        return {d: self._vectors[d] for d in doc_ids if d in self._vectors}


class _FakeGraphPort(GraphScorePort):
    def __init__(self, entities: dict[str, set[str]]) -> None:
        self._entities = entities

    async def get_canonicals_for_document(self, document_id: str) -> set[str]:
        return self._entities.get(document_id, set())

    async def get_canonicals_for_folder(self, folder_path: str) -> set[str]:
        return set()

    async def get_known_folder_paths(self) -> list[str]:
        return []


class _FakeFileMover:
    """Fake FileMover that performs real OS moves so file-presence tests work."""

    def __init__(self) -> None:
        self.moves: list[tuple[str, str]] = []

    async def move(
        self, source_path: str, target_folder: str, conflict_strategy: str = "error"
    ) -> str:
        import shutil as _shutil
        self.moves.append((source_path, target_folder))
        if os.path.isfile(source_path):
            os.makedirs(target_folder, exist_ok=True)
            dest = os.path.join(target_folder, os.path.basename(source_path))
            _shutil.move(source_path, dest)
            return dest
        return os.path.join(target_folder, os.path.basename(source_path))


# ---------------------------------------------------------------------------
# Helper — build a real in-memory repo for the proposal gate tests
# ---------------------------------------------------------------------------

async def _make_proposal_repo() -> ClusterProposalRepository:
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await _apply_migrations(conn)
    return ClusterProposalRepository(conn)


async def _make_rec_repo() -> RecommendationRepository:
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await _apply_migrations(conn)
    return RecommendationRepository(conn)


def _make_service(
    docs: list[_FakeDoc],
    *,
    vectors: dict[str, list[float]] | None = None,
    entities: dict[str, set[str]] | None = None,
    distance_threshold: float = 0.5,
    proposal_repo: ClusterProposalRepository | None = None,
    file_mover: _FakeFileMover | None = None,
    rec_repo: RecommendationRepository | None = None,
    watcher_paths: list[str] | None = None,
) -> tuple[ClusterDiscoveryService, _FakeFileMover]:
    if vectors is None:
        # All docs get the same vector → distance 0 → always one big cluster
        vectors = {d.id: [1.0, 0.0] for d in docs}
    if entities is None:
        entities = {d.id: {"alpha"} for d in docs}
    mover = file_mover or _FakeFileMover()

    graph_port = _FakeGraphPort(entities)
    scorer = ClusterScorer(graph_port, entity_weight=0.75)
    engine = ClusterEngine(distance_threshold=distance_threshold)
    naming = FolderNamingService(graph_port, llm_enabled=False)

    svc = ClusterDiscoveryService(
        floating_filter=_FakeFloatingFilter(docs),
        vector_service=_FakeVectorService(vectors),
        cluster_scorer=scorer,
        cluster_engine=engine,
        naming_service=naming,
        proposal_repo=proposal_repo,  # type: ignore[arg-type]
        watcher_service=_FakeWatcher(watcher_paths or ["/workspace"]),
        file_mover=mover,
        recommendation_repo=rec_repo,  # type: ignore[arg-type]
    )
    return svc, mover


# ---------------------------------------------------------------------------
# discover_proposals
# ---------------------------------------------------------------------------

class TestDiscoverProposals:
    async def test_no_docs_returns_empty(self) -> None:
        repo = await _make_proposal_repo()
        svc, _ = _make_service([], proposal_repo=repo)
        result = await svc.discover_proposals()
        assert result == []

    async def test_single_doc_returns_empty(self) -> None:
        repo = await _make_proposal_repo()
        svc, _ = _make_service([_FakeDoc("d1", "/f/a.pdf")], proposal_repo=repo)
        result = await svc.discover_proposals()
        assert result == []

    async def test_two_close_docs_create_one_proposal(self) -> None:
        repo = await _make_proposal_repo()
        docs = [_FakeDoc("d1", "/f/a.pdf"), _FakeDoc("d2", "/f/b.pdf")]
        # Identical vectors → distance 0 → merged
        vectors = {"d1": [1.0, 0.0], "d2": [1.0, 0.0]}
        svc, _ = _make_service(docs, vectors=vectors, proposal_repo=repo)
        result = await svc.discover_proposals()
        assert len(result) == 1
        assert set(result[0].document_ids) == {"d1", "d2"}

    async def test_proposal_has_correct_file_paths(self) -> None:
        repo = await _make_proposal_repo()
        docs = [_FakeDoc("d1", "/f/a.pdf"), _FakeDoc("d2", "/f/b.pdf")]
        vectors = {"d1": [1.0, 0.0], "d2": [1.0, 0.0]}
        svc, _ = _make_service(docs, vectors=vectors, proposal_repo=repo)
        result = await svc.discover_proposals()
        assert len(result) == 1
        assert set(result[0].file_paths) == {"/f/a.pdf", "/f/b.pdf"}

    async def test_proposal_status_is_pending(self) -> None:
        repo = await _make_proposal_repo()
        docs = [_FakeDoc("d1", "/f/a.pdf"), _FakeDoc("d2", "/f/b.pdf")]
        vectors = {"d1": [1.0, 0.0], "d2": [1.0, 0.0]}
        svc, _ = _make_service(docs, vectors=vectors, proposal_repo=repo)
        result = await svc.discover_proposals()
        assert result[0].status == "pending"

    async def test_far_docs_produce_no_proposals(self) -> None:
        repo = await _make_proposal_repo()
        docs = [_FakeDoc("d1", "/f/a.pdf"), _FakeDoc("d2", "/f/b.pdf")]
        # Orthogonal vectors → cosine=0; disjoint entities → overlap=0 → distance=1
        vectors = {"d1": [1.0, 0.0], "d2": [0.0, 1.0]}
        entities = {"d1": {"alpha"}, "d2": {"beta"}}
        svc, _ = _make_service(
            docs,
            vectors=vectors,
            entities=entities,
            distance_threshold=0.3,
            proposal_repo=repo,
        )
        result = await svc.discover_proposals()
        assert result == []


class TestProposalGate:
    async def test_duplicate_cluster_is_skipped(self) -> None:
        repo = await _make_proposal_repo()
        docs = [_FakeDoc("d1", "/f/a.pdf"), _FakeDoc("d2", "/f/b.pdf")]
        vectors = {"d1": [1.0, 0.0], "d2": [1.0, 0.0]}
        svc, _ = _make_service(docs, vectors=vectors, proposal_repo=repo)

        first = await svc.discover_proposals()
        assert len(first) == 1

        # Second run with same docs — gate should suppress duplicate.
        second = await svc.discover_proposals()
        assert second == []

    async def test_new_docs_in_cluster_bypasses_gate(self) -> None:
        repo = await _make_proposal_repo()
        # First run: d1+d2 cluster
        docs1 = [_FakeDoc("d1", "/f/a.pdf"), _FakeDoc("d2", "/f/b.pdf")]
        vectors1 = {"d1": [1.0, 0.0], "d2": [1.0, 0.0]}
        svc1, _ = _make_service(docs1, vectors=vectors1, proposal_repo=repo)
        await svc1.discover_proposals()

        # Second run: d1+d2+d3 cluster (superset) → different frozenset → new proposal
        docs2 = [
            _FakeDoc("d1", "/f/a.pdf"),
            _FakeDoc("d2", "/f/b.pdf"),
            _FakeDoc("d3", "/f/c.pdf"),
        ]
        vectors2 = {"d1": [1.0, 0.0], "d2": [1.0, 0.0], "d3": [1.0, 0.0]}
        svc2, _ = _make_service(docs2, vectors=vectors2, proposal_repo=repo)
        second = await svc2.discover_proposals()
        # The d1+d2+d3 cluster is a different set → should create a proposal
        assert len(second) == 1
        assert set(second[0].document_ids) == {"d1", "d2", "d3"}


# ---------------------------------------------------------------------------
# accept_proposal
# ---------------------------------------------------------------------------

class TestAcceptProposal:
    async def test_accept_updates_status(self) -> None:
        proposal_repo = await _make_proposal_repo()
        rec_repo = await _make_rec_repo()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create real files so FileMover won't skip them.
            f1 = os.path.join(tmpdir, "a.pdf")
            f2 = os.path.join(tmpdir, "b.pdf")
            open(f1, "w").close()
            open(f2, "w").close()

            docs = [_FakeDoc("d1", f1), _FakeDoc("d2", f2)]
            vectors = {"d1": [1.0, 0.0], "d2": [1.0, 0.0]}
            svc, _ = _make_service(
                docs,
                vectors=vectors,
                proposal_repo=proposal_repo,
                rec_repo=rec_repo,
            )
            proposals = await svc.discover_proposals()
            assert len(proposals) == 1

            target_folder = os.path.join(tmpdir, "NewFolder")
            updated = await svc.accept_proposal(proposals[0].id, target_folder)
            assert updated.status == "accepted"
            assert updated.accepted_folder == target_folder

    async def test_accept_creates_target_folder(self) -> None:
        proposal_repo = await _make_proposal_repo()
        rec_repo = await _make_rec_repo()

        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = os.path.join(tmpdir, "a.pdf")
            open(f1, "w").close()
            f2 = os.path.join(tmpdir, "b.pdf")
            open(f2, "w").close()

            docs = [_FakeDoc("d1", f1), _FakeDoc("d2", f2)]
            vectors = {"d1": [1.0, 0.0], "d2": [1.0, 0.0]}
            svc, _ = _make_service(
                docs, vectors=vectors, proposal_repo=proposal_repo, rec_repo=rec_repo
            )
            proposals = await svc.discover_proposals()

            target = os.path.join(tmpdir, "CreatedFolder")
            await svc.accept_proposal(proposals[0].id, target)
            assert os.path.isdir(target)

    async def test_accept_moves_files(self) -> None:
        proposal_repo = await _make_proposal_repo()
        rec_repo = await _make_rec_repo()

        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = os.path.join(tmpdir, "a.pdf")
            open(f1, "w").close()
            f2 = os.path.join(tmpdir, "b.pdf")
            open(f2, "w").close()

            docs = [_FakeDoc("d1", f1), _FakeDoc("d2", f2)]
            vectors = {"d1": [1.0, 0.0], "d2": [1.0, 0.0]}
            svc, _ = _make_service(
                docs, vectors=vectors, proposal_repo=proposal_repo, rec_repo=rec_repo
            )
            proposals = await svc.discover_proposals()

            target = os.path.join(tmpdir, "Moved")
            await svc.accept_proposal(proposals[0].id, target)
            # Original locations should no longer exist.
            assert not os.path.isfile(f1)
            assert not os.path.isfile(f2)
            # Files should be in the target folder.
            assert os.path.isfile(os.path.join(target, "a.pdf"))
            assert os.path.isfile(os.path.join(target, "b.pdf"))

    async def test_accept_skips_missing_files(self) -> None:
        proposal_repo = await _make_proposal_repo()
        rec_repo = await _make_rec_repo()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only one of the two files.
            f1 = os.path.join(tmpdir, "present.pdf")
            open(f1, "w").close()
            f2 = os.path.join(tmpdir, "gone.pdf")  # does not exist

            docs = [_FakeDoc("d1", f1), _FakeDoc("d2", f2)]
            vectors = {"d1": [1.0, 0.0], "d2": [1.0, 0.0]}
            svc, _ = _make_service(
                docs, vectors=vectors, proposal_repo=proposal_repo, rec_repo=rec_repo
            )
            proposals = await svc.discover_proposals()
            target = os.path.join(tmpdir, "Output")
            # Must not raise even though f2 doesn't exist.
            updated = await svc.accept_proposal(proposals[0].id, target)
            assert updated.status == "accepted"

    async def test_accept_unknown_id_raises(self) -> None:
        proposal_repo = await _make_proposal_repo()
        rec_repo = await _make_rec_repo()
        svc, _ = _make_service([], proposal_repo=proposal_repo, rec_repo=rec_repo)
        with pytest.raises(ValueError, match="not found"):
            await svc.accept_proposal("00000000-0000-0000-0000-000000000000", "/tmp/x")

    async def test_accept_already_accepted_raises(self) -> None:
        proposal_repo = await _make_proposal_repo()
        rec_repo = await _make_rec_repo()

        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = os.path.join(tmpdir, "a.pdf")
            open(f1, "w").close()
            f2 = os.path.join(tmpdir, "b.pdf")
            open(f2, "w").close()

            docs = [_FakeDoc("d1", f1), _FakeDoc("d2", f2)]
            svc, _ = _make_service(
                docs,
                vectors={"d1": [1.0, 0.0], "d2": [1.0, 0.0]},
                proposal_repo=proposal_repo,
                rec_repo=rec_repo,
            )
            proposals = await svc.discover_proposals()
            target = os.path.join(tmpdir, "Dest")
            await svc.accept_proposal(proposals[0].id, target)

            with pytest.raises(ValueError, match="already accepted"):
                await svc.accept_proposal(proposals[0].id, target)


# ---------------------------------------------------------------------------
# dismiss_proposal
# ---------------------------------------------------------------------------

class TestDismissProposal:
    async def test_dismiss_updates_status(self) -> None:
        proposal_repo = await _make_proposal_repo()
        docs = [_FakeDoc("d1", "/f/a.pdf"), _FakeDoc("d2", "/f/b.pdf")]
        vectors = {"d1": [1.0, 0.0], "d2": [1.0, 0.0]}
        svc, _ = _make_service(docs, vectors=vectors, proposal_repo=proposal_repo)
        proposals = await svc.discover_proposals()
        assert len(proposals) == 1

        await svc.dismiss_proposal(proposals[0].id)
        fetched = await proposal_repo.get(proposals[0].id)
        assert fetched is not None
        assert fetched.status == "dismissed"

    async def test_dismiss_unknown_id_raises(self) -> None:
        proposal_repo = await _make_proposal_repo()
        svc, _ = _make_service([], proposal_repo=proposal_repo)
        with pytest.raises(ValueError, match="not found"):
            await svc.dismiss_proposal("00000000-0000-0000-0000-000000000000")

    async def test_dismiss_already_dismissed_raises(self) -> None:
        proposal_repo = await _make_proposal_repo()
        docs = [_FakeDoc("d1", "/f/a.pdf"), _FakeDoc("d2", "/f/b.pdf")]
        vectors = {"d1": [1.0, 0.0], "d2": [1.0, 0.0]}
        svc, _ = _make_service(docs, vectors=vectors, proposal_repo=proposal_repo)
        proposals = await svc.discover_proposals()

        await svc.dismiss_proposal(proposals[0].id)
        with pytest.raises(ValueError, match="already dismissed"):
            await svc.dismiss_proposal(proposals[0].id)
