"""Port interfaces for PlacementScorer data access.

Separates the scoring algorithm from storage details so PlacementScorer
can be tested without a database or Qdrant connection.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path


# ---------------------------------------------------------------------------
# Shared vocabulary helpers (used by both the scorer and the adapters)
# ---------------------------------------------------------------------------

_FILENAME_STOPWORDS: frozenset[str] = frozenset({
    "pdf", "doc", "docx", "txt", "md",
    "the", "a", "an", "of", "in", "on", "at", "for", "and", "or",
    "to", "by", "from", "with",
})


def filename_keywords(file_path: str) -> set[str]:
    """Tokenise a file/folder stem into lowercase keyword terms.

    Works on both file paths (uses stem) and directory paths (uses final
    directory name). Four-digit year tokens are excluded as non-discriminative.
    """
    p = Path(file_path)
    name = p.name if p.is_dir() or not p.suffix else p.stem
    words = re.sub(r"[_\-\.\s]+", " ", name).lower().split()
    return {
        w for w in words
        if len(w) > 2
        and w not in _FILENAME_STOPWORDS
        and not re.fullmatch(r"\d{4}", w)
    }


def expand_for_matching(canonicals: set[str]) -> set[str]:
    """Expand multi-word canonical entity strings into individual word tokens.

    LLM extraction often produces multi-word entities like
    'japan 2026 photography itinerary'. Exact-string matching misses the
    connection to single-word terms like 'japan' stored in other documents.
    Original strings are kept alongside expansions so the set is a superset.
    """
    expanded = set(canonicals)
    for entity in canonicals:
        if " " in entity or "-" in entity:
            tokens = re.sub(r"[-\s]+", " ", entity).lower().split()
            expanded |= {
                t for t in tokens
                if len(t) > 2
                and t not in _FILENAME_STOPWORDS
                and not re.fullmatch(r"\d{4}", t)
            }
    return expanded


# ---------------------------------------------------------------------------
# Port interfaces
# ---------------------------------------------------------------------------

class GraphScorePort(ABC):
    """Data access interface for graph-based entity overlap scoring."""

    @abstractmethod
    async def get_canonicals_for_document(
        self,
        document_id: str,
        file_path: str,
    ) -> set[str]:
        """Return canonical entity names for *document_id*, expanded 1 hop.

        *file_path* is provided so adapters can apply sparse-entity fallback
        (tokenising the filename) without a second round-trip to ask for it.
        """

    @abstractmethod
    async def get_canonicals_for_folder(self, folder_path: str) -> set[str]:
        """Return canonical entity names for all documents under *folder_path*, expanded 1 hop.

        Includes folder-name keyword terms so semantically-named empty folders
        still participate in scoring.
        """

    @abstractmethod
    async def get_known_folder_paths(
        self,
        exclude_paths: set[str] | None = None,
        max_candidates: int = 150,
    ) -> list[str]:
        """Return unique parent directories inferred from indexed file paths.

        Folders are ranked by document count (most-populated first) then
        ancestor directories are pruned so only leaf directories are returned.
        """


class RerankPort(ABC):
    """Data access interface for hybrid-search rerank scoring."""

    @abstractmethod
    async def rerank(
        self,
        document_id: str,
        folder_path: str,
        top_k: int = 30,
    ) -> float:
        """Return the mean RRF score of the top-5 folder-filtered search results.

        Uses the first chunk of *document_id* as the query text. Returns 0.0
        on failure or when the folder has no matching indexed content.
        """
