"""Unit tests for FloatingFileFilter.

All tests use in-memory fakes — no database, no filesystem access required
(only path string manipulation and resolve(), which normalises without I/O).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from enterprise_ai_companion.capabilities.organisation.floating_file_filter import (
    FloatingFileFilter,
)

# ---------------------------------------------------------------------------
# Shared path constants — all resolved through Path so string comparisons match
# ---------------------------------------------------------------------------
_HOME = Path.home()
_WORKSPACE = _HOME / "TestEACWorkspace"
_FINANCE = _WORKSPACE / "Finance"
_MISC = _WORKSPACE / "misc"
_FINANCE_2024 = _FINANCE / "2024"
_DOWNLOADS = _HOME / "Downloads"


def _doc(file_path: str | Path) -> SimpleNamespace:
    """Minimal document object sufficient for FloatingFileFilter."""
    return SimpleNamespace(id="test-id", file_path=str(file_path))


# ---------------------------------------------------------------------------
# Fake collaborators
# ---------------------------------------------------------------------------

class _FakeDocRepo:
    def __init__(self, docs: list) -> None:
        self._docs = docs

    async def list_all(self, limit: int, offset: int) -> list:
        return self._docs[offset : offset + limit]


class _FakeRecRepo:
    def __init__(self, pending_paths: list[str] | None = None) -> None:
        self._pending = [
            SimpleNamespace(source_path=p) for p in (pending_paths or [])
        ]

    async def list_pending(self) -> list:
        return self._pending


class _FakeWatcher:
    def __init__(self, roots: list[str]) -> None:
        self._roots = roots

    async def list_folders(self) -> list:
        return [SimpleNamespace(path=r) for r in self._roots]


def _make_filter(
    docs: list | None = None,
    pending: list[str] | None = None,
    roots: list[str] | None = None,
    system_index_paths: frozenset[str] = frozenset(),
) -> FloatingFileFilter:
    return FloatingFileFilter(
        document_repo=_FakeDocRepo(docs or []),
        recommendation_repo=_FakeRecRepo(pending),
        watcher_service=_FakeWatcher(roots or []) if roots is not None else None,
        system_index_paths=system_index_paths,
    )


# ===========================================================================
# is_floating_zone — Rule 8
# ===========================================================================

class TestIsFloatingZone:
    """Synchronous tests for the three-tier Rule 8 logic."""

    def _leaf_and_roots(
        self,
        roots: list[str],
        leaves: list[str],
    ) -> tuple[set[str], set[str]]:
        leaf_set = {str(Path(f).resolve()) for f in leaves}
        root_set = {str(Path(r).resolve()) for r in roots}
        return leaf_set, root_set

    def test_workspace_root_is_floating_tier_a(self) -> None:
        """File sitting directly in a watched workspace root → floating (tier a)."""
        file = str(_WORKSPACE / "report.pdf")
        leaves, roots = self._leaf_and_roots(
            roots=[str(_WORKSPACE)],
            leaves=[str(_FINANCE)],
        )
        flt = _make_filter()
        assert flt.is_floating_zone(file, leaves, roots) is True

    def test_organised_leaf_folder_not_floating(self) -> None:
        """File in a real leaf folder with a non-dump name → not floating."""
        file = str(_FINANCE / "report.pdf")
        leaves, roots = self._leaf_and_roots(
            roots=[str(_WORKSPACE)],
            leaves=[str(_FINANCE)],
        )
        flt = _make_filter()
        assert flt.is_floating_zone(file, leaves, roots) is False

    def test_ancestor_folder_is_floating_tier_b(self) -> None:
        """File in an ancestor folder that has sub-leaf children → floating (tier b)."""
        # Finance is NOT a leaf (Finance/2024 is the leaf); file sits in Finance.
        file = str(_FINANCE / "report.pdf")
        leaves, roots = self._leaf_and_roots(
            roots=[str(_WORKSPACE)],
            leaves=[str(_FINANCE_2024)],
        )
        flt = _make_filter()
        assert flt.is_floating_zone(file, leaves, roots) is True

    def test_dump_folder_name_is_floating_tier_c(self) -> None:
        """File in a leaf folder named 'misc' → floating (tier c)."""
        file = str(_MISC / "report.pdf")
        leaves, roots = self._leaf_and_roots(
            roots=[str(_WORKSPACE)],
            leaves=[str(_MISC)],
        )
        flt = _make_filter()
        assert flt.is_floating_zone(file, leaves, roots) is True

    def test_dump_folder_names_case_insensitive(self) -> None:
        """Dump folder check is case-insensitive (e.g. 'Temp' matches 'temp')."""
        folder = _WORKSPACE / "Temp"
        file = str(folder / "file.pdf")
        leaves, roots = self._leaf_and_roots(
            roots=[str(_WORKSPACE)],
            leaves=[str(folder)],
        )
        flt = _make_filter()
        assert flt.is_floating_zone(file, leaves, roots) is True

    def test_empty_workspace_roots_falls_through_to_tier_b(self) -> None:
        """With no workspace roots, tier (a) is skipped; tier (b) applies."""
        file = str(_FINANCE / "report.pdf")
        leaves, roots = self._leaf_and_roots(
            roots=[],
            leaves=[str(_FINANCE_2024)],  # Finance is NOT a leaf
        )
        flt = _make_filter()
        # Finance is not in the leaf set → floating via tier (b)
        assert flt.is_floating_zone(file, leaves, roots) is True


# ===========================================================================
# get_eligible_docs — Rules 2-7
# ===========================================================================

class TestGetEligibleDocs:

    @pytest.mark.asyncio
    async def test_normal_doc_is_included(self) -> None:
        """A document with no disqualifying attributes is returned."""
        doc = _doc(_FINANCE / "Budget_2024.pdf")
        flt = _make_filter(docs=[doc])
        result = await flt.get_eligible_docs()
        assert result == [doc]

    @pytest.mark.asyncio
    async def test_downloads_doc_is_excluded(self) -> None:
        """Rule 2: files under the Downloads folder are excluded."""
        doc = _doc(_DOWNLOADS / "Invoice.pdf")
        flt = _make_filter(docs=[doc])
        result = await flt.get_eligible_docs()
        assert result == []

    @pytest.mark.asyncio
    async def test_personal_token_doc_is_excluded(self) -> None:
        """Rule 3: files with personal filename tokens are excluded."""
        doc = _doc(_FINANCE / "home_renovation_plan.pdf")
        flt = _make_filter(docs=[doc])
        result = await flt.get_eligible_docs()
        assert result == []

    @pytest.mark.asyncio
    async def test_personal_token_with_dashes_is_excluded(self) -> None:
        """Rule 3: token splitting handles dashes and dots as delimiters."""
        doc = _doc(_FINANCE / "garden-planning.docx")
        flt = _make_filter(docs=[doc])
        result = await flt.get_eligible_docs()
        assert result == []

    @pytest.mark.asyncio
    async def test_lock_file_prefix_is_excluded(self) -> None:
        """Rule 4: Office lock files (~$...) are excluded."""
        doc = _doc(_FINANCE / "~$Budget_2024.xlsx")
        flt = _make_filter(docs=[doc])
        result = await flt.get_eligible_docs()
        assert result == []

    @pytest.mark.asyncio
    async def test_pending_recommendation_is_excluded(self) -> None:
        """Rule 7: files with an active pending recommendation are excluded."""
        path = str(_FINANCE / "Budget_2024.pdf")
        doc = _doc(path)
        flt = _make_filter(docs=[doc], pending=[path])
        result = await flt.get_eligible_docs()
        assert result == []

    @pytest.mark.asyncio
    async def test_system_index_path_is_excluded(self) -> None:
        """Rule 6: files under EAC_SYSTEM_INDEX_PATHS are excluded."""
        system_root = str(_WORKSPACE / "SystemDocs")
        doc = _doc(Path(system_root) / "internal.pdf")
        flt = _make_filter(
            docs=[doc],
            system_index_paths=frozenset({system_root}),
        )
        result = await flt.get_eligible_docs()
        assert result == []

    @pytest.mark.asyncio
    async def test_mix_of_eligible_and_excluded(self) -> None:
        """Only eligible documents pass through when mixed with excluded ones."""
        eligible = _doc(_FINANCE / "Budget_2024.pdf")
        excluded_downloads = _doc(_DOWNLOADS / "Invoice.pdf")
        excluded_personal = _doc(_FINANCE / "family_photos.pdf")
        flt = _make_filter(docs=[eligible, excluded_downloads, excluded_personal])
        result = await flt.get_eligible_docs()
        assert result == [eligible]

    @pytest.mark.asyncio
    async def test_pagination_collects_all_docs(self) -> None:
        """Documents spanning multiple pages are all returned."""
        docs = [_doc(_FINANCE / f"doc_{i}.pdf") for i in range(250)]
        flt = _make_filter(docs=docs)
        result = await flt.get_eligible_docs()
        assert len(result) == 250


# ===========================================================================
# get_floating_candidates — Rules 1-8
# ===========================================================================

class TestGetFloatingCandidates:

    @pytest.mark.asyncio
    async def test_workspace_root_file_is_candidate(self) -> None:
        """File sitting in a watched workspace root passes rules 1-8."""
        doc = _doc(_WORKSPACE / "Orphaned_Report.pdf")
        flt = _make_filter(docs=[doc], roots=[str(_WORKSPACE)])
        result = await flt.get_floating_candidates(leaf_folders=[str(_FINANCE)])
        assert result == [doc]

    @pytest.mark.asyncio
    async def test_organised_file_is_not_candidate(self) -> None:
        """File in a real leaf folder with a sensible name is NOT a candidate."""
        doc = _doc(_FINANCE / "Budget_2024.pdf")
        flt = _make_filter(docs=[doc], roots=[str(_WORKSPACE)])
        result = await flt.get_floating_candidates(leaf_folders=[str(_FINANCE)])
        assert result == []

    @pytest.mark.asyncio
    async def test_eligible_rules_applied_before_rule8(self) -> None:
        """Downloads files are excluded before the floating-zone check runs."""
        doc = _doc(_DOWNLOADS / "Invoice.pdf")
        flt = _make_filter(docs=[doc], roots=[str(_DOWNLOADS)])
        # Even though Downloads IS a workspace root (tier a would pass),
        # rule 2 excludes it first.
        result = await flt.get_floating_candidates(leaf_folders=[])
        assert result == []
