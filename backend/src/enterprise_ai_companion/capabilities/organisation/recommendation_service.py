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
        watcher_service: object,  # WatcherService — forward reference avoids circular import
    ) -> None:
        self._repo = recommendation_repo
        self._scorer = placement_scorer
        self._watcher = watcher_service

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
        all_folders = await self._watcher.list_folders()
        candidate_paths = [
            f.path
            for f in all_folders
            if f.path != _DOWNLOADS_PATH
        ]

        if not candidate_paths:
            logger.debug(
                "No candidate folders for %s — no other watched folders registered", file_path
            )
            return

        logger.info(
            "Scoring %d candidate folder(s) for %s (doc_id=%s)",
            len(candidate_paths),
            file_path,
            document_id,
        )

        scored = await self._scorer.score_all(document_id, candidate_paths)

        if not scored:
            logger.info(
                "No scoring signal for %s — no recommendation created", file_path
            )
            return

        await self._repo.create(file_path, scored)
        logger.info(
            "Recommendation created for %s: top folder=%s (score=%.3f)",
            file_path,
            scored[0]["folder"],
            scored[0]["score"],
        )
