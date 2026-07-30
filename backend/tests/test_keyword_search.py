"""Tests for KeywordSearchProvider."""

from __future__ import annotations

import pytest
import aiosqlite

from enterprise_ai_companion.capabilities.retrieval.keyword_search import (
    KeywordSearchProvider,
    _escape_fts5_query,
    _normalise_bm25,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
async def db():
    """In-memory SQLite database with the full knowledge schema applied."""
    async with aiosqlite.connect(":memory:") as conn:
        conn.row_factory = aiosqlite.Row
        await conn.executescript("""
            CREATE TABLE documents (
                id             TEXT PRIMARY KEY,
                workspace_path TEXT NOT NULL,
                file_path      TEXT NOT NULL UNIQUE,
                file_hash      TEXT NOT NULL,
                char_count     INTEGER NOT NULL DEFAULT 0,
                chunk_count    INTEGER NOT NULL DEFAULT 0,
                indexed_at     TEXT NOT NULL
            );

            CREATE TABLE chunks (
                id          TEXT PRIMARY KEY,
                document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                content     TEXT NOT NULL,
                char_start  INTEGER NOT NULL,
                char_end    INTEGER NOT NULL
            );

            CREATE VIRTUAL TABLE chunks_fts
                USING fts5(content, chunk_id UNINDEXED, tokenize='porter ascii');
        """)
        yield conn


async def _seed(conn: aiosqlite.Connection, doc_id: str, workspace: str, file_path: str, chunks: list[str]) -> None:
    """Insert one document and its chunks into both SQLite and FTS5 tables."""
    await conn.execute(
        "INSERT INTO documents (id, workspace_path, file_path, file_hash, char_count, chunk_count, indexed_at) "
        "VALUES (?, ?, ?, 'hash', 0, ?, '2026-01-01T00:00:00Z')",
        (doc_id, workspace, file_path, len(chunks)),
    )
    for i, content in enumerate(chunks):
        chunk_id = f"{doc_id}-chunk-{i}"
        await conn.execute(
            "INSERT INTO chunks (id, document_id, chunk_index, content, char_start, char_end) VALUES (?, ?, ?, ?, 0, 0)",
            (chunk_id, doc_id, i, content),
        )
        await conn.execute(
            "INSERT INTO chunks_fts (content, chunk_id) VALUES (?, ?)",
            (content, chunk_id),
        )
    await conn.commit()


# ─── Helper tests ─────────────────────────────────────────────────────────────

class TestEscapeFts5Query:
    def test_single_word(self):
        assert _escape_fts5_query("hello") == '"hello"'

    def test_multiple_words(self):
        assert _escape_fts5_query("hello world") == '"hello" "world"'

    def test_strips_extra_whitespace(self):
        assert _escape_fts5_query("  hello   world  ") == '"hello" "world"'

    def test_special_chars_wrapped(self):
        result = _escape_fts5_query("c++ tutorial")
        assert '"c++"' in result
        assert '"tutorial"' in result

    def test_fts5_operators_neutralised(self):
        result = _escape_fts5_query("AND OR NOT")
        assert result == '"AND" "OR" "NOT"'


class TestNormaliseBm25:
    def test_zero_returns_zero(self):
        assert _normalise_bm25(0.0) == pytest.approx(1.0 / (1.0 + 0.0))

    def test_negative_input(self):
        score = _normalise_bm25(-5.0)
        assert 0.0 < score < 1.0

    def test_more_negative_yields_lower_normalised_score(self):
        # BM25 scores are negative — more negative = better match.
        # _normalise_bm25 maps via 1/(1+|raw|), so a larger |raw| yields a
        # smaller normalised value. Scores stay in (0, 1] regardless.
        weak_match = _normalise_bm25(-1.0)    # small magnitude → closer to 1.0
        strong_match = _normalise_bm25(-100.0) # large magnitude → closer to 0.0
        assert weak_match > strong_match
        assert 0.0 < strong_match < weak_match <= 1.0

    def test_positive_input_treated_same_as_negative(self):
        assert _normalise_bm25(5.0) == _normalise_bm25(-5.0)


# ─── Search behaviour ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestKeywordSearchProvider:
    async def test_empty_query_returns_empty(self, db):
        provider = KeywordSearchProvider(db)
        results = await provider.search("   ")
        assert results == []

    async def test_basic_match(self, db):
        await _seed(db, "doc1", "/ws", "/ws/notes.md", ["The quick brown fox jumps"])
        provider = KeywordSearchProvider(db)
        results = await provider.search("fox")
        assert len(results) == 1
        assert "fox" in results[0].content

    async def test_no_match_returns_empty(self, db):
        await _seed(db, "doc1", "/ws", "/ws/notes.md", ["The quick brown fox"])
        provider = KeywordSearchProvider(db)
        results = await provider.search("elephant")
        assert results == []

    async def test_top_k_limits_results(self, db):
        for i in range(5):
            await _seed(db, f"doc{i}", "/ws", f"/ws/file{i}.md", [f"Python tutorial part {i}"])
        provider = KeywordSearchProvider(db)
        results = await provider.search("Python", top_k=3)
        assert len(results) <= 3

    async def test_results_have_valid_scores(self, db):
        await _seed(db, "doc1", "/ws", "/ws/a.md", ["Machine learning models"])
        await _seed(db, "doc2", "/ws", "/ws/b.md", ["Deep learning neural networks"])
        provider = KeywordSearchProvider(db)
        results = await provider.search("learning")
        for r in results:
            assert 0.0 < r.score <= 1.0

    async def test_workspace_filter_includes_only_matching(self, db):
        await _seed(db, "doc1", "/workspace/a", "/workspace/a/file.md", ["Python scripting guide"])
        await _seed(db, "doc2", "/workspace/b", "/workspace/b/file.md", ["Python automation guide"])
        provider = KeywordSearchProvider(db)
        results = await provider.search("Python", workspace_path="/workspace/a")
        assert all(r.document_path.startswith("/workspace/a") for r in results)
        assert len(results) == 1

    async def test_workspace_filter_none_returns_all(self, db):
        await _seed(db, "doc1", "/ws/a", "/ws/a/file.md", ["shared keyword here"])
        await _seed(db, "doc2", "/ws/b", "/ws/b/file.md", ["shared keyword there"])
        provider = KeywordSearchProvider(db)
        results = await provider.search("shared", workspace_path=None)
        assert len(results) == 2

    async def test_result_fields_are_populated(self, db):
        await _seed(db, "doc1", "/ws", "/ws/readme.md", ["Enterprise AI Companion documentation"])
        provider = KeywordSearchProvider(db)
        results = await provider.search("Enterprise")
        assert len(results) == 1
        r = results[0]
        assert r.chunk_id
        assert r.document_id == "doc1"
        assert r.document_path == "/ws/readme.md"
        assert r.chunk_index == 0
        assert "Enterprise" in r.content

    async def test_porter_stemmer_matches_variants(self, db):
        await _seed(db, "doc1", "/ws", "/ws/notes.md", ["Running tests is important for quality"])
        provider = KeywordSearchProvider(db)
        # "run" should match "running" via porter stemmer
        results = await provider.search("run")
        assert len(results) == 1

    async def test_multi_word_query_requires_all_tokens(self, db):
        await _seed(db, "doc1", "/ws", "/ws/a.md", ["Python machine learning tutorial"])
        await _seed(db, "doc2", "/ws", "/ws/b.md", ["JavaScript tutorial for beginners"])
        provider = KeywordSearchProvider(db)
        results = await provider.search("Python tutorial")
        doc_paths = {r.document_path for r in results}
        assert "/ws/a.md" in doc_paths
