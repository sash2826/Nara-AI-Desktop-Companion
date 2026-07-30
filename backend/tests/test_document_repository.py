"""Unit tests for DocumentRepository using an in-memory SQLite database."""

import os

import aiosqlite
import pytest

from enterprise_ai_companion.capabilities.indexing.document_repository import (
    DocumentRepository,
    IndexedDocument,
)
from enterprise_ai_companion.infrastructure.database import open_db


@pytest.fixture
async def db():
    os.environ["EAC_DB_PATH"] = ":memory:"
    conn = await open_db()
    yield conn
    await conn.close()
    del os.environ["EAC_DB_PATH"]


@pytest.fixture
async def repo(db: aiosqlite.Connection) -> DocumentRepository:
    return DocumentRepository(db)


def _make_doc(**kwargs) -> IndexedDocument:
    defaults = dict(
        id="doc-1",
        workspace_path="/workspace",
        file_path="/workspace/file.md",
        file_hash="abc123",
        char_count=100,
        chunk_count=2,
        indexed_at="2026-07-30T00:00:00Z",
    )
    defaults.update(kwargs)
    return IndexedDocument(**defaults)


class TestUpsert:
    async def test_inserts_new_document(self, repo: DocumentRepository) -> None:
        doc = _make_doc()
        await repo.upsert(doc)
        result = await repo.get_by_path("/workspace/file.md")
        assert result is not None
        assert result.id == "doc-1"

    async def test_updates_existing_document_on_conflict(self, repo: DocumentRepository) -> None:
        await repo.upsert(_make_doc(file_hash="old"))
        await repo.upsert(_make_doc(id="doc-2", file_hash="new"))
        result = await repo.get_by_path("/workspace/file.md")
        assert result is not None
        assert result.file_hash == "new"

    async def test_updates_chunk_count(self, repo: DocumentRepository) -> None:
        await repo.upsert(_make_doc(chunk_count=2))
        await repo.upsert(_make_doc(chunk_count=5))
        result = await repo.get_by_path("/workspace/file.md")
        assert result is not None
        assert result.chunk_count == 5


class TestGetByPath:
    async def test_returns_none_for_unknown_path(self, repo: DocumentRepository) -> None:
        result = await repo.get_by_path("/no/such/file.md")
        assert result is None

    async def test_returns_correct_document(self, repo: DocumentRepository) -> None:
        await repo.upsert(_make_doc())
        result = await repo.get_by_path("/workspace/file.md")
        assert result is not None
        assert result.workspace_path == "/workspace"


class TestListByWorkspace:
    async def test_returns_empty_for_unknown_workspace(self, repo: DocumentRepository) -> None:
        results = await repo.list_by_workspace("/unknown")
        assert results == []

    async def test_returns_all_documents_in_workspace(self, repo: DocumentRepository) -> None:
        await repo.upsert(_make_doc(id="d1", file_path="/ws/a.md"))
        await repo.upsert(_make_doc(id="d2", file_path="/ws/b.md"))
        await repo.upsert(_make_doc(id="d3", file_path="/other/c.md", workspace_path="/other"))
        results = await repo.list_by_workspace("/workspace")
        assert len(results) == 2

    async def test_results_ordered_by_file_path(self, repo: DocumentRepository) -> None:
        await repo.upsert(_make_doc(id="d1", file_path="/ws/z.md"))
        await repo.upsert(_make_doc(id="d2", file_path="/ws/a.md"))
        results = await repo.list_by_workspace("/workspace")
        assert results[0].file_path == "/ws/a.md"
        assert results[1].file_path == "/ws/z.md"


class TestDeleteByPath:
    async def test_removes_document(self, repo: DocumentRepository) -> None:
        await repo.upsert(_make_doc())
        await repo.delete_by_path("/workspace/file.md")
        result = await repo.get_by_path("/workspace/file.md")
        assert result is None

    async def test_no_error_on_unknown_path(self, repo: DocumentRepository) -> None:
        await repo.delete_by_path("/no/such/file.md")  # should not raise
