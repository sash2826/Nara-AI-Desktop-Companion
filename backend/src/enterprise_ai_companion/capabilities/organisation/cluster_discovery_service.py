"""Orchestrates the intelligent folder-discovery pipeline (Phase 10 Scenario 3).

Ties together FloatingFileFilter, DocumentVectorService, ClusterScorer,
ClusterEngine, FolderNamingService, and ClusterProposalRepository to:
  1. Identify floating files that have no clear home folder.
  2. Group them semantically via agglomerative clustering.
  3. Propose a new folder per cluster with a deterministic (or optional LLM)
     name derived from canonical entity labels.
  4. Let the user accept (files are physically moved) or dismiss each proposal.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from enterprise_ai_companion.capabilities.organisation.cluster_engine import (
    ClusterEngine,
)
from enterprise_ai_companion.capabilities.organisation.cluster_proposal_repository import (
    ClusterProposal,
    ClusterProposalRepository,
)
from enterprise_ai_companion.capabilities.organisation.cluster_scorer import (
    ClusterScorer,
)
from enterprise_ai_companion.capabilities.organisation.document_vector_service import (
    DocumentVectorService,
)
from enterprise_ai_companion.capabilities.organisation.floating_file_filter import (
    FloatingFileFilter,
)
from enterprise_ai_companion.capabilities.organisation.folder_naming_service import (
    FolderNamingService,
)
from enterprise_ai_companion.capabilities.organisation.recommendation_repository import (
    RecommendationRepository,
)

if TYPE_CHECKING:
    from enterprise_ai_companion.capabilities.indexing.file_watcher import WatcherService
    from enterprise_ai_companion.capabilities.organisation.file_mover import FileMover

logger = logging.getLogger(__name__)


class ClusterDiscoveryService:
    """End-to-end pipeline: floating files → semantic clusters → folder proposals.

    The proposal gate prevents duplicate proposals: if a pending proposal
    already covers the exact same set of documents, no new proposal is created.
    The caller (API router) surfaces proposals to the Organise dashboard.
    """

    def __init__(
        self,
        floating_filter: FloatingFileFilter,
        vector_service: DocumentVectorService,
        cluster_scorer: ClusterScorer,
        cluster_engine: ClusterEngine,
        naming_service: FolderNamingService,
        proposal_repo: ClusterProposalRepository,
        watcher_service: "WatcherService",
        file_mover: "FileMover",
        recommendation_repo: RecommendationRepository,
    ) -> None:
        self._filter = floating_filter
        self._vectors = vector_service
        self._scorer = cluster_scorer
        self._engine = cluster_engine
        self._naming = naming_service
        self._proposals = proposal_repo
        self._watcher = watcher_service
        self._mover = file_mover
        self._recs = recommendation_repo

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    async def discover_proposals(self) -> list[ClusterProposal]:
        """Run the full clustering pipeline and return newly-created proposals.

        Already-pending proposals for the same document set are skipped
        (proposal gate). Returns an empty list if fewer than 2 floating
        documents exist or if clustering produces no clusters above the
        minimum size threshold.
        """
        folders = await self._watcher.list_folders()
        leaf_paths = [f.path for f in folders]

        candidates = await self._filter.get_floating_candidates(leaf_paths)
        if len(candidates) < 2:
            logger.info("[CLUSTER-DISCOVERY] Fewer than 2 floating docs — skipping clustering")
            return []

        doc_ids = [doc.id for doc in candidates]
        file_paths_by_id = {doc.id: doc.file_path for doc in candidates}
        folder_samples = [os.path.basename(p) for p in leaf_paths if p]

        logger.info(
            "[CLUSTER-DISCOVERY] Running clustering on %d floating doc(s)", len(doc_ids)
        )

        vectors = await self._vectors.get_vectors(doc_ids)
        distance_matrix = await self._scorer.compute_distance_matrix(
            doc_ids, vectors, file_paths=file_paths_by_id
        )
        raw_clusters = self._engine.cluster(doc_ids, distance_matrix)

        logger.info(
            "[CLUSTER-DISCOVERY] %d raw cluster(s) produced", len(raw_clusters)
        )

        existing_pending = await self._proposals.list_pending()
        existing_sets: list[frozenset[str]] = [
            frozenset(p.document_ids) for p in existing_pending
        ]

        new_proposals: list[ClusterProposal] = []
        for cluster_doc_ids in raw_clusters:
            cluster_set = frozenset(cluster_doc_ids)
            if cluster_set in existing_sets:
                logger.debug(
                    "[CLUSTER-DISCOVERY] Skipping duplicate cluster %s", cluster_set
                )
                continue

            name = await self._naming.name_cluster(
                cluster_doc_ids,
                existing_folder_samples=folder_samples,
                file_paths=file_paths_by_id,
            )
            file_paths = [
                file_paths_by_id[doc_id]
                for doc_id in cluster_doc_ids
                if doc_id in file_paths_by_id
            ]
            proposal = await self._proposals.create(name, cluster_doc_ids, file_paths)
            new_proposals.append(proposal)
            existing_sets.append(cluster_set)  # prevent intra-run duplicates
            logger.info(
                "[CLUSTER-DISCOVERY] Created proposal %s: %r (%d file(s))",
                proposal.id, name, len(file_paths),
            )

        return new_proposals

    # ------------------------------------------------------------------
    # Proposal resolution
    # ------------------------------------------------------------------

    async def accept_proposal(
        self,
        proposal_id: str,
        accepted_folder: str,
    ) -> ClusterProposal:
        """Move all files in the proposal to *accepted_folder* and mark accepted.

        Files that no longer exist at their stored path are skipped silently —
        they may have been moved by an individual placement recommendation.
        Files that fail to move due to OS errors are logged and skipped so that
        one bad file does not block the rest.

        Returns the updated proposal record.

        Raises:
            ValueError: If the proposal does not exist or is not pending.
        """
        proposal = await self._proposals.get(proposal_id)
        if proposal is None:
            raise ValueError(f"Cluster proposal not found: {proposal_id}")
        if proposal.status != "pending":
            raise ValueError(f"Cluster proposal is already {proposal.status}")

        os.makedirs(accepted_folder, exist_ok=True)

        for file_path in proposal.file_paths:
            if not os.path.isfile(file_path):
                logger.info(
                    "[CLUSTER-ACCEPT] Skipping missing file: %s", file_path
                )
                continue
            try:
                await self._mover.move(file_path, accepted_folder, conflict_strategy="rename")
                await self._recs.set_accepted_by_source_path(file_path, accepted_folder)
            except OSError as exc:
                logger.error(
                    "[CLUSTER-ACCEPT] Failed to move %s → %s: %s",
                    file_path, accepted_folder, exc,
                )

        await self._proposals.set_accepted(proposal_id, accepted_folder)

        updated = await self._proposals.get(proposal_id)
        return updated  # type: ignore[return-value]

    async def dismiss_proposal(self, proposal_id: str) -> None:
        """Dismiss a proposal without moving any files.

        Raises:
            ValueError: If the proposal does not exist or is not pending.
        """
        proposal = await self._proposals.get(proposal_id)
        if proposal is None:
            raise ValueError(f"Cluster proposal not found: {proposal_id}")
        if proposal.status != "pending":
            raise ValueError(f"Cluster proposal is already {proposal.status}")

        await self._proposals.set_dismissed(proposal_id)
