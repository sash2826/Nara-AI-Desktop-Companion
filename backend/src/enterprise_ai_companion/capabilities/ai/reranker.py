"""Chunk reranker for the context assembly pipeline.

Reranking runs after the initial hybrid search fetch (top 20 candidates)
and before the token-budget step. It re-orders candidates to maximise
relevance to the specific query, so the 5 chunks that reach the LLM are
the most useful rather than just the highest-RRF.

Architecture:
    The public surface is the abstract ``ChunkReranker`` interface.
    ``HeuristicReranker`` provides a position-aware cosine similarity
    implementation that runs entirely in-process with no external models.
    When a cross-encoder model becomes available in the corporate environment
    it can be dropped in as a new implementation without changing callers.

Heuristic scoring formula:
    score = α × cos(q̂, ĉ) + β × rrf_position_bonus

    Where:
      - q̂  is the query character-level n-gram TF-IDF vector (approximated)
      - ĉ  is the chunk content vector (same space)
      - rrf_position_bonus decays with original rank so strong RRF signals
        are not completely discarded
      - α = 0.7, β = 0.3

This outperforms raw RRF ordering in multi-document scenarios because:
  1. RRF only knows rank position; it cannot compare query-to-chunk textual
     overlap directly.
  2. The cosine component re-surfaces chunks that share rare query terms
     that may rank lower in BM25 but are semantically central.
"""

from __future__ import annotations

import logging
import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Blend weights: cosine similarity vs RRF position bonus.
_COSINE_WEIGHT: float = 0.7
_POSITION_WEIGHT: float = 0.3

# RRF smoothing constant (must match hybrid_orchestrator.py).
_RRF_K: int = 60


@dataclass(frozen=True)
class RankedChunk:
    """A candidate chunk with its reranker score."""

    chunk_id: str
    document_id: str
    document_path: str
    chunk_index: int
    content: str
    rrf_score: float
    rerank_score: float
    semantic_rank: int | None
    keyword_rank: int | None


class ChunkReranker(ABC):
    """Abstract reranker interface.

    Implementations receive raw hybrid-search candidates and return them
    re-ordered by a relevance signal that is complementary to RRF rank.
    """

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: list,  # list[HybridSearchResult]
        top_n: int,
    ) -> list[RankedChunk]:
        """Return up to top_n candidates ordered by descending rerank_score.

        Args:
            query: The raw user query string.
            candidates: Hybrid search results (HybridSearchResult dataclasses).
            top_n: Maximum number of results to return.
        """


class HeuristicReranker(ChunkReranker):
    """Position-aware cosine similarity reranker.

    Scores each candidate as a weighted blend of:
      - character n-gram cosine similarity between query and chunk content
      - a position bonus derived from the original RRF score

    Requires no external models and runs synchronously in microseconds.
    The interface is compatible with a future cross-encoder replacement.
    """

    def rerank(
        self,
        query: str,
        candidates: list,
        top_n: int,
    ) -> list[RankedChunk]:
        if not candidates:
            return []

        query_vec = _ngram_tfidf(query)
        max_rrf = max(c.rrf_score for c in candidates) or 1.0

        ranked: list[RankedChunk] = []
        for c in candidates:
            content_vec = _ngram_tfidf(c.content)
            cos = _cosine(query_vec, content_vec)
            # Normalise RRF score to [0, 1] for the position bonus.
            pos_bonus = c.rrf_score / max_rrf
            rerank_score = _COSINE_WEIGHT * cos + _POSITION_WEIGHT * pos_bonus

            ranked.append(
                RankedChunk(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    document_path=c.document_path,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    rrf_score=c.rrf_score,
                    rerank_score=rerank_score,
                    semantic_rank=c.semantic_rank,
                    keyword_rank=c.keyword_rank,
                )
            )

        ranked.sort(key=lambda r: r.rerank_score, reverse=True)
        return ranked[:top_n]


# ---------------------------------------------------------------------------
# Text vectorisation helpers
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"\w+")


def _tokenise(text: str) -> list[str]:
    """Lowercase word tokenisation."""
    return _TOKEN_RE.findall(text.lower())


def _ngram_tfidf(text: str, n: int = 2) -> dict[str, float]:
    """Compute a simple n-gram TF vector (no IDF — single-document context).

    Returns a dict mapping each n-gram string to its normalised term frequency.
    Using character bigrams of words captures morphological similarity better
    than whole-word matching for short queries.
    """
    tokens = _tokenise(text)
    if not tokens:
        return {}

    ngrams: list[str] = []
    for token in tokens:
        if len(token) >= n:
            ngrams.extend(token[i : i + n] for i in range(len(token) - n + 1))
        else:
            ngrams.append(token)

    counts = Counter(ngrams)
    total = sum(counts.values()) or 1
    return {k: v / total for k, v in counts.items()}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity between two sparse TF vectors."""
    if not a or not b:
        return 0.0

    dot = sum(a.get(k, 0.0) * v for k, v in b.items())
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    denom = norm_a * norm_b
    return dot / denom if denom > 0 else 0.0
