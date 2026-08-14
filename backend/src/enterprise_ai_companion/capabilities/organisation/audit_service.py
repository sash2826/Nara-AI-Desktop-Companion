"""On-demand file organisation audit for existing indexed documents."""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from enterprise_ai_companion.capabilities.indexing.document_repository import DocumentRepository
from enterprise_ai_companion.capabilities.organisation.placement_scorer import PlacementScorer
from enterprise_ai_companion.capabilities.organisation.recommendation_repository import (
    RecommendationRepository,
)

if TYPE_CHECKING:
    from enterprise_ai_companion.capabilities.indexing.file_watcher import WatcherService

logger = logging.getLogger(__name__)

_DOWNLOADS_PATH = str(Path.home() / "Downloads")
_MIN_TOP_SCORE = 0.55
_MIN_SCORE_DELTA = 0.20
_PAGE_SIZE = 100


@dataclass
class AuditState:
    running: bool = False
    analysed: int = 0
    total: int = 0
    found: int = 0


class AuditService:
    """Iterates all indexed documents and surfaces reorganisation suggestions.

    Skips files in the Downloads folder (handled by Phase 09) and files that
    already have an active pending recommendation. Creates a pending rec when
    a non-current folder scores ≥ 0.55 with a delta ≥ 0.20 over the current
    folder score.
    """

    def __init__(
        self,
        document_repo: DocumentRepository,
        placement_scorer: PlacementScorer,
        recommendation_repo: RecommendationRepository,
        watcher_service: "WatcherService",
    ) -> None:
        self._doc_repo = document_repo
        self._scorer = placement_scorer
        self._rec_repo = recommendation_repo
        self._watcher = watcher_service
        self.state = AuditState()

    async def run_audit(self) -> None:
        """Start the audit. No-op if already running."""
        if self.state.running:
            logger.info("[AUDIT] Already running — ignoring duplicate request")
            return

        self.state = AuditState(running=True)
        logger.info("[AUDIT] Organisation audit started")

        try:
            await self._run()
        except Exception as exc:
            logger.exception("[AUDIT] Audit failed: %s", exc)
        finally:
            self.state.running = False
            logger.info(
                "[AUDIT] Complete — analysed %d, found %d suggestion(s)",
                self.state.analysed,
                self.state.found,
            )

    async def _run(self) -> None:
        watched = await self._watcher.list_folders()
        candidate_paths = [f.path for f in watched if f.path != _DOWNLOADS_PATH]
        if not candidate_paths:
            logger.info("[AUDIT] No candidate folders — nothing to audit")
            return

        pending = await self._rec_repo.list_pending()
        pending_paths: set[str] = {rec.source_path for rec in pending}

        # Paginate through all indexed documents
        all_docs = []
        offset = 0
        while True:
            page = await self._doc_repo.list_all(limit=_PAGE_SIZE, offset=offset)
            if not page:
                break
            all_docs.extend(page)
            offset += _PAGE_SIZE
            if len(page) < _PAGE_SIZE:
                break

        eligible = [doc for doc in all_docs if doc.workspace_path != _DOWNLOADS_PATH]
        self.state.total = len(eligible)
        logger.info("[AUDIT] %d eligible file(s) to analyse", self.state.total)

        for doc in eligible:
            await self._score_doc(doc, candidate_paths, pending_paths)
            self.state.analysed += 1
            await asyncio.sleep(0)  # yield so FastAPI stays responsive

    async def _score_doc(
        self, doc, candidate_paths: list[str], pending_paths: set[str]
    ) -> None:
        if doc.file_path in pending_paths:
            return

        current_folder = str(Path(doc.file_path).parent)

        # Include current folder in scoring to compute delta
        all_folders = list({*candidate_paths, current_folder})
        scores = await self._scorer.score_all(doc.id, all_folders)
        if not scores:
            return

        current_score = next(
            (s["score"] for s in scores if s["folder"] == current_folder), 0.0
        )
        non_current = [s for s in scores if s["folder"] != current_folder]
        if not non_current:
            return

        top = non_current[0]
        if top["score"] < _MIN_TOP_SCORE:
            return
        if (top["score"] - current_score) < _MIN_SCORE_DELTA:
            return

        await self._rec_repo.create(doc.file_path, non_current[:3])
        pending_paths.add(doc.file_path)
        self.state.found += 1
        logger.info(
            "[AUDIT] Suggestion: %s → %s (score=%.2f delta=%.2f)",
            os.path.basename(doc.file_path),
            os.path.basename(top["folder"]),
            top["score"],
            top["score"] - current_score,
        )
