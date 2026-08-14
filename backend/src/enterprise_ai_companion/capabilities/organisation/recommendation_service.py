"""Orchestrates placement recommendation creation and feedback learning for new Downloads files.

Called by the watcher's DebounceHandler after a new file in the OS Downloads
folder has been successfully indexed. Scores each watched folder, persists
the top-3 results, and logs the outcome.

Phase 09b additions:
  - Stores an entity_snapshot at creation time for later affinity weight updates.
  - record_accept / record_dismiss update entity-folder affinity weights via EMA.
  - record_correction detects and records watchdog-detected user corrections.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from enterprise_ai_companion.capabilities.organisation.affinity_repository import AffinityRepository
from enterprise_ai_companion.capabilities.organisation.placement_scorer import PlacementScorer
from enterprise_ai_companion.capabilities.organisation.recommendation_repository import (
    RecommendationRepository,
)

logger = logging.getLogger(__name__)

_DOWNLOADS_PATH = str(Path.home() / "Downloads")


def _parse_entity_snapshot(entity_snapshot: str | None) -> set[str]:
    """Deserialise the JSON entity snapshot to a set of names, or return empty set."""
    if not entity_snapshot:
        return set()
    try:
        names = json.loads(entity_snapshot)
        return set(names) if isinstance(names, list) else set()
    except (json.JSONDecodeError, TypeError):
        return set()


class RecommendationService:
    """Creates placement recommendations and maintains affinity learning from user feedback."""

    def __init__(
        self,
        recommendation_repo: RecommendationRepository,
        placement_scorer: PlacementScorer,
        watcher_service: object,  # WatcherService — forward reference avoids circular import
        affinity_repo: AffinityRepository,
    ) -> None:
        self._repo = recommendation_repo
        self._scorer = placement_scorer
        self._watcher = watcher_service
        self._affinity_repo = affinity_repo

    # ------------------------------------------------------------------
    # New-file pipeline
    # ------------------------------------------------------------------

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
        logger.info(
            "[PLACEMENT] process_new_file: %s | all watched folders: %s",
            file_path, [f.path for f in all_folders],
        )
        candidate_paths = [f.path for f in all_folders if f.path != _DOWNLOADS_PATH]

        if not candidate_paths:
            logger.info(
                "[PLACEMENT] No candidate folders for %s — no other watched folders registered",
                file_path,
            )
            return

        logger.info(
            "Scoring %d candidate folder(s) for %s (doc_id=%s)",
            len(candidate_paths), file_path, document_id,
        )

        scored = await self._scorer.score_all(document_id, candidate_paths)

        if not scored:
            logger.info(
                "No scoring signal for %s — dismissing any stale pending recommendation",
                file_path,
            )
            await self.dismiss_stale_for_path(file_path)
            return

        # Snapshot the entity names used during scoring so they can be replayed
        # when updating affinity weights on accept / dismiss / correction.
        entity_names = await self._scorer.get_document_entity_names_expanded(document_id)
        entity_snapshot = json.dumps(sorted(entity_names)) if entity_names else None

        await self._repo.create(file_path, scored, entity_snapshot=entity_snapshot)
        logger.info(
            "Recommendation created for %s: top folder=%s (score=%.3f, entities=%d)",
            file_path, scored[0]["folder"], scored[0]["score"], len(entity_names),
        )

    # ------------------------------------------------------------------
    # Feedback learning — called by the organisation router
    # ------------------------------------------------------------------

    async def record_accept(self, rec_id: str, folder: str) -> None:
        """Update affinity weights when a recommendation is accepted.

        Applies a positive EMA signal (1.0) for all entities in the snapshot
        against the accepted folder. Called by the router after the file has
        been physically moved and the repo status updated.
        """
        rec = await self._repo.get(rec_id)
        if rec is None:
            return
        entity_names = _parse_entity_snapshot(rec.entity_snapshot)
        if entity_names:
            await self._affinity_repo.update_weights_bulk(entity_names, folder, signal=1.0)
            logger.info(
                "Affinity updated (accept): folder=%s entities=%d", folder, len(entity_names)
            )

    async def record_dismiss(self, rec_id: str) -> None:
        """Update affinity weights when a recommendation is dismissed.

        Applies a negative EMA signal (0.0) for all entities in the snapshot
        against every candidate folder in the recommendation.
        """
        rec = await self._repo.get(rec_id)
        if rec is None:
            return
        entity_names = _parse_entity_snapshot(rec.entity_snapshot)
        if not entity_names:
            return
        for candidate in rec.recommendations:
            folder = candidate.get("folder")
            if folder:
                await self._affinity_repo.update_weights_bulk(entity_names, folder, signal=0.0)
        logger.info(
            "Affinity updated (dismiss): %d folder(s) suppressed, entities=%d",
            len(rec.recommendations), len(entity_names),
        )

    async def record_correction(self, source_path: str, dest_folder: str) -> None:
        """Handle a watchdog-detected user correction (file moved to a non-suggested folder).

        Only fires when:
        1. A pending recommendation exists for *source_path*.
        2. *dest_folder* is NOT one of the top-3 suggested folders (Q6=B).

        Marks the recommendation as 'corrected', then:
        - Applies a positive signal (1.0) for all entities against *dest_folder*.
        - Applies a negative signal (0.0) for all entities against each wrong suggestion.
        """
        try:
            await self._handle_correction(source_path, dest_folder)
        except Exception:
            logger.exception(
                "RecommendationService: error recording correction for %s → %s",
                source_path, dest_folder,
            )

    async def _handle_correction(self, source_path: str, dest_folder: str) -> None:
        rec = await self._repo.get_pending_by_source_path(source_path)
        if rec is None:
            return  # no pending rec for this file — nothing to learn from

        suggested_folders = {c.get("folder") for c in rec.recommendations}
        if dest_folder in suggested_folders:
            # User moved to a suggested folder without using the EAC UI — treat as
            # a silent accept (dismiss the pending rec; affinity already neutral).
            await self._repo.dismiss_by_source_path(source_path)
            logger.info(
                "Correction detected but dest is a suggested folder — treating as silent accept: %s",
                source_path,
            )
            return

        # Genuine correction: user explicitly chose a folder we didn't suggest.
        await self._repo.set_corrected(rec.id, dest_folder)

        entity_names = _parse_entity_snapshot(rec.entity_snapshot)
        if entity_names:
            await self._affinity_repo.update_weights_bulk(entity_names, dest_folder, signal=1.0)
            for folder in suggested_folders:
                if folder:
                    await self._affinity_repo.update_weights_bulk(
                        entity_names, folder, signal=0.0
                    )
            logger.info(
                "Correction recorded: %s → %s (suppressed %d wrong suggestion(s), entities=%d)",
                source_path, dest_folder, len(suggested_folders), len(entity_names),
            )

    # ------------------------------------------------------------------
    # Stale record cleanup
    # ------------------------------------------------------------------

    async def dismiss_stale_for_path(self, source_path: str) -> None:
        """Dismiss any pending recommendations for a file that has been deleted or moved away.

        Called by the watcher's on_deleted handler and by the reconcile startup
        sweep so that stale inbox entries are cleaned up automatically.
        """
        try:
            await self._repo.dismiss_by_source_path(source_path)
        except Exception:
            logger.exception(
                "RecommendationService: failed to auto-dismiss stale recommendation for %s",
                source_path,
            )
