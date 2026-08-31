"""Single source of truth for floating-file candidate identification.

Rules 1-7 are consumed by AuditService (Scenario 2: existing-file suggestions).
Rules 1-8 are consumed by ClusterDiscoveryService (Scenario 3: new-folder proposals).
Rule 8 is the three-tier floating-zone test.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from enterprise_ai_companion.capabilities.indexing.document_repository import DocumentRepository
from enterprise_ai_companion.capabilities.indexing.file_indexer import EXCLUDED_DIRS
from enterprise_ai_companion.capabilities.organisation.recommendation_repository import (
    RecommendationRepository,
)

if TYPE_CHECKING:
    from enterprise_ai_companion.capabilities.indexing.file_watcher import WatcherService

logger = logging.getLogger(__name__)

_DOWNLOADS_PATH: Path = Path.home() / "Downloads"
_PAGE_SIZE = 100

# Filename tokens that identify personal/domestic documents.
# Files whose stem contains any of these words (split on _-.) are excluded.
_PERSONAL_FILENAME_TOKENS: frozenset[str] = frozenset({
    "personal", "home", "garden", "family", "renovation",
    "private", "hobby", "leisure",
})

# Temp/lock file prefixes — mirrors file_indexer._IGNORED_PREFIXES.
_IGNORED_PREFIXES: tuple[str, ...] = ("~$",)

# OS roots that must never appear in audit results — mirrors file_indexer._BLOCKED_ROOTS.
_BLOCKED_ROOTS: frozenset[Path] = frozenset({
    Path("C:/Windows"),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
    Path("C:/ProgramData"),
    Path("C:/System Volume Information"),
    Path("/etc"),
    Path("/sys"),
    Path("/proc"),
    Path("/dev"),
    Path("/boot"),
})


class FloatingFileFilter:
    """Identifies floating-file candidates from the document index.

    The filter is the single owner of the eligibility and floating-zone rules.
    AuditService calls ``get_eligible_docs()`` (rules 1-7).
    ClusterDiscoveryService calls ``get_floating_candidates()`` (rules 1-8).
    """

    DUMP_FOLDER_NAMES: frozenset[str] = frozenset({
        "misc", "miscellaneous", "temp", "temporary", "tmp", "unsorted",
        "new folder", "various", "other", "general", "dump", "inbox",
        "staging", "to sort", "random", "junk", "files", "stuff",
    })

    def __init__(
        self,
        document_repo: DocumentRepository,
        recommendation_repo: RecommendationRepository,
        watcher_service: "WatcherService | None" = None,
        system_index_paths: frozenset[str] = frozenset(),
    ) -> None:
        self._doc_repo = document_repo
        self._rec_repo = recommendation_repo
        self._watcher_service = watcher_service
        self._system_index_paths = system_index_paths

    async def get_eligible_docs(self) -> list[Any]:
        """Return indexed documents that pass rules 1-7.

        Used by AuditService to build its candidate list before scoring.
        The pending-recommendation snapshot is taken once at call time; docs
        added to the pending set during a caller's run loop are not re-filtered.
        """
        all_docs = await self._fetch_all_docs()
        pending_paths = await self._get_pending_paths()
        return [doc for doc in all_docs if self._passes_base_rules(doc, pending_paths)]

    async def get_floating_candidates(self, leaf_folders: list[str]) -> list[Any]:
        """Return indexed documents that pass rules 1-8.

        Used by ClusterDiscoveryService to identify files suitable for
        new-folder proposals. ``leaf_folders`` should come from
        ``SqliteGraphScoreAdapter.get_known_folder_paths()``.
        """
        eligible = await self.get_eligible_docs()
        leaf_set: set[str] = {str(Path(f).resolve()) for f in leaf_folders}
        workspace_roots = await self._get_workspace_roots()
        return [
            doc for doc in eligible
            if self.is_floating_zone(doc.file_path, leaf_set, workspace_roots)
        ]

    def is_floating_zone(
        self,
        file_path: str,
        leaf_folders: set[str],
        workspace_roots: set[str],
    ) -> bool:
        """Rule 8: three-tier floating-zone test.

        Tier (a) workspace root — the file's parent IS a watched workspace root.
               Fixes the flat-workspace case where a root has no subfolders and
               therefore cannot be an ancestor of any leaf (the original binary
               ancestor check would never trigger).
        Tier (b) ancestor — the file's parent is NOT in the leaf-folder set,
               meaning it is a directory that contains further subfolders and is
               not itself a meaningful destination.
        Tier (c) dump folder — the file's parent IS a leaf but its name signals
               an unorganised catch-all (misc, temp, inbox, etc.).
        """
        parent = str(Path(file_path).parent.resolve())

        if parent in workspace_roots:        # tier (a)
            return True
        if parent not in leaf_folders:       # tier (b)
            return True
        if Path(parent).name.lower() in self.DUMP_FOLDER_NAMES:  # tier (c)
            return True
        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _passes_base_rules(self, doc: Any, pending_paths: set[str]) -> bool:
        """Rules 2-7: return True only when the document is an audit candidate."""
        file_path: str = doc.file_path
        path = Path(file_path)

        # Rule 2: not under the Downloads folder (handled by the watcher pipeline).
        try:
            if path.parent.resolve().is_relative_to(_DOWNLOADS_PATH.resolve()):
                return False
        except (OSError, ValueError):
            pass

        # Rule 3: no personal/domestic filename tokens.
        stem_tokens = frozenset(
            path.stem.lower().replace("-", "_").replace(".", "_").split("_")
        )
        if stem_tokens & _PERSONAL_FILENAME_TOKENS:
            return False

        # Rule 4: temp/lock file prefixes (e.g. Office lock files ~$...).
        if path.name.startswith(_IGNORED_PREFIXES):
            return False

        # Rule 5: not under an excluded directory name or OS-blocked root.
        for part in path.parts:
            if part in EXCLUDED_DIRS:
                return False
        try:
            resolved = path.resolve()
            if any(resolved.is_relative_to(blocked) for blocked in _BLOCKED_ROOTS):
                return False
        except (OSError, ValueError):
            pass

        # Rule 6: not under an EAC system index path.
        if self._system_index_paths:
            try:
                resolved = path.resolve()
                for sp in self._system_index_paths:
                    if resolved.is_relative_to(Path(sp).resolve()):
                        return False
            except (OSError, ValueError):
                pass

        # Rule 7: no active pending recommendation for this path.
        if file_path in pending_paths:
            return False

        return True

    async def _fetch_all_docs(self) -> list[Any]:
        all_docs: list[Any] = []
        offset = 0
        while True:
            page = await self._doc_repo.list_all(limit=_PAGE_SIZE, offset=offset)
            if not page:
                break
            all_docs.extend(page)
            offset += _PAGE_SIZE
            if len(page) < _PAGE_SIZE:
                break
        return all_docs

    async def _get_pending_paths(self) -> set[str]:
        pending = await self._rec_repo.list_pending()
        return {rec.source_path for rec in pending}

    async def _get_workspace_roots(self) -> set[str]:
        if self._watcher_service is None:
            return set()
        folders = await self._watcher_service.list_folders()
        return {str(Path(f.path).resolve()) for f in folders}
