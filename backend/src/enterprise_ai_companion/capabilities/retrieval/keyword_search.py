"""Keyword search provider backed by SQLite FTS5."""

from __future__ import annotations

import logging
import re

import aiosqlite

from enterprise_ai_companion.capabilities.retrieval.search_models import SearchResult

logger = logging.getLogger(__name__)

# Maximum number of results the FTS5 query will fetch before workspace filtering.
_FTS_FETCH_MULTIPLIER = 3


class KeywordSearchProvider:
    """Full-text keyword search over indexed document chunks using SQLite FTS5.

    The FTS5 virtual table ``chunks_fts`` is kept in sync with the ``chunks``
    table by ``ChunkRepository.save_batch`` and ``delete_by_document``.  This
    provider queries it using the FTS5 MATCH syntax and hydrates results with
    metadata from the ``chunks`` and ``documents`` tables.

    Porter-stemmer tokenisation (configured on the FTS5 table) means that
    queries like "running" will also match "run" and "runs".
    """

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def search(
        self,
        query: str,
        top_k: int = 10,
        workspace_path: str | None = None,
    ) -> list[SearchResult]:
        """Return up to *top_k* chunks matching *query* via full-text search.

        Args:
            query: Raw user query string.  Special FTS5 characters are escaped
                so that plain user input cannot inject FTS5 operators.
            top_k: Maximum results to return after workspace filtering.
            workspace_path: When supplied, only chunks whose parent document
                belongs to this workspace path are returned.

        Returns:
            Results ordered by FTS5 BM25 relevance (best first).
        """
        stripped = query.strip()
        if not stripped:
            return []

        fts_query = _escape_fts5_query(stripped)
        fetch_limit = top_k * _FTS_FETCH_MULTIPLIER if workspace_path else top_k

        sql = """
            SELECT
                cf.chunk_id,
                c.document_id,
                d.file_path,
                c.chunk_index,
                c.content,
                d.workspace_path,
                bm25(chunks_fts) AS bm25_score
            FROM chunks_fts cf
            JOIN chunks   c ON c.id  = cf.chunk_id
            JOIN documents d ON d.id = c.document_id
            WHERE chunks_fts MATCH ?
            ORDER BY bm25_score
            LIMIT ?
        """

        try:
            async with self._conn.execute(sql, (fts_query, fetch_limit)) as cur:
                rows = await cur.fetchall()
        except Exception:
            logger.exception("FTS5 query failed for query=%r", stripped)
            return []

        results: list[SearchResult] = []
        for row in rows:
            chunk_id, document_id, file_path, chunk_index, content, ws_path, bm25_score = row

            if workspace_path and ws_path != workspace_path:
                continue

            # BM25 scores from SQLite are negative (lower = better match).
            # Invert and normalise to [0, 1] range for a consistent score field.
            normalised_score = _normalise_bm25(float(bm25_score))

            results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    document_path=file_path,
                    chunk_index=chunk_index,
                    content=content,
                    score=normalised_score,
                )
            )
            if len(results) >= top_k:
                break

        logger.debug(
            "Keyword search: query=%r returned %d results (top_k=%d)",
            stripped,
            len(results),
            top_k,
        )
        return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _escape_fts5_query(query: str) -> str:
    """Escape a raw user query for safe use in an FTS5 MATCH expression.

    Wraps each whitespace-delimited token in double quotes so that special FTS5
    characters (AND, OR, NOT, *, ^, etc.) are treated as literals.  This keeps
    the behaviour predictable for end-users who are not familiar with FTS5 syntax.

    Example:
        "hello world"  →  '"hello" "world"'
        "c++ tutorial" →  '"c++" "tutorial"'
    """
    tokens = re.split(r"\s+", query.strip())
    return " ".join(f'"{t}"' for t in tokens if t)


def _normalise_bm25(raw: float) -> float:
    """Convert a raw SQLite BM25 score (negative, unbounded) to (0, 1].

    SQLite's bm25() returns negative values — more negative means better match.
    We map the raw score using  score = 1 / (1 + |raw|)  so that:
      - A perfect match (raw → -∞) approaches 1.0.
      - A weak match (raw → 0)    approaches 0.0.
    """
    return 1.0 / (1.0 + abs(raw))
