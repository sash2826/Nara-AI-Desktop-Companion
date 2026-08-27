"""Orchestrates placement recommendation creation for new Downloads files.

Called by the watcher's DebounceHandler after a new file in the OS Downloads
folder has been successfully indexed. Scores each watched folder, persists
the top-3 results, and logs the outcome.
"""

from __future__ import annotations

import logging
from pathlib import Path

from enterprise_ai_companion.capabilities.organisation.placement_scorer import PlacementScorer
from enterprise_ai_companion.capabilities.organisation.recommendation_repository import (
    RecommendationRepository,
)

logger = logging.getLogger(__name__)

# Resolved Downloads path — used to exclude the source folder from candidates.
_DOWNLOADS_PATH = str(Path.home() / "Downloads")


class RecommendationService:
    """Creates placement recommendations for newly-downloaded files."""

    def __init__(
        self,
        recommendation_repo: RecommendationRepository,
        placement_scorer: PlacementScorer,
    ) -> None:
        self._repo = recommendation_repo
        self._scorer = placement_scorer

    async def process_new_file(self, file_path: str, document_id: str) -> None:
        """Score candidate folders and persist a recommendation for *file_path*.

        Silently skips if:
        - No watched folders (other than Downloads) exist.
        - The scorer returns no non-zero scores.
        """
        try:
            await self._process(file_path, document_id)
        except Exception:
            logger.exception(
                "RecommendationService: unexpected error processing %s — skipping", file_path
            )

    async def _process(self, file_path: str, document_id: str) -> None:
        # Discover candidate folders from the actual subdirectory structure of
        # indexed documents. Using watched-root paths here caused new Downloads
        # files to be scored only against top-level roots like "Documents",
        # which contain the entire corpus and score trivially high.
        candidate_paths = await self._scorer.discover_candidate_folders(
            exclude_paths={_DOWNLOADS_PATH}
        )
        logger.info(
            "[PLACEMENT] process_new_file: %s | %d subfolder candidate(s)",
            file_path, len(candidate_paths),
        )

        if not candidate_paths:
            logger.info(
                "[PLACEMENT] No candidate folders for %s — no indexed subfolders found", file_path
            )
            return

        # Exclude the file's own parent and all ancestor directories — moving a
        # file to where it already lives (or to a parent that already contains
        # it) is never a meaningful recommendation.
        # is_relative_to(f) is True when file_parent == f OR file_parent is
        # nested inside f, catching both the exact-parent case and deeper ancestors.
        file_parent = Path(file_path).parent.resolve()
        candidate_paths = [
            f for f in candidate_paths
            if not file_parent.is_relative_to(Path(f).resolve())
        ]

        logger.info(
            "Scoring %d candidate folder(s) for %s (doc_id=%s)",
            len(candidate_paths),
            file_path,
            document_id,
        )

        scored = await self._scorer.score_all(document_id, candidate_paths, file_path=file_path)

        if not scored:
            logger.info(
                "No scoring signal for %s — dismissing any stale pending recommendation", file_path
            )
            # Dismiss any existing pending record produced by an older, less
            # selective scorer run. Without this, a re-dropped file keeps its
            # stale false-positive recommendation indefinitely.
            await self.dismiss_stale_for_path(file_path)
            return

        await self._repo.create(file_path, scored)
        logger.info(
            "Recommendation created for %s: top folder=%s (score=%.3f)",
            file_path,
            scored[0]["folder"],
            scored[0]["score"],
        )

    async def dismiss_stale_for_path(self, source_path: str) -> None:
        """Dismiss any pending recommendations for a file that has been deleted or moved away.

        Called by the watcher's on_deleted and on_moved handlers so that stale
        inbox entries are cleaned up automatically rather than surfacing a broken
        "Move here" action to the user.
        """
        try:
            await self._repo.dismiss_by_source_path(source_path)
        except Exception:
            logger.exception(
                "RecommendationService: failed to auto-dismiss stale recommendation for %s",
                source_path,
            )
