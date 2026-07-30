"""Integration tests for FileIndexer using a temporary directory and in-memory stores."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import aiosqlite
import pytest

from enterprise_ai_companion.capabilities.indexing.chunk_repository import ChunkRepository
from enterprise_ai_companion.capabilities.indexing.document_repository import DocumentRepository
from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
from enterprise_ai_companion.capabilities.indexing.file_indexer import FileIndexer
from enterprise_ai_companion.infrastructure.database import open_db


@pytest.fixture
async def db():
    os.environ["EAC_DB_PATH"] = ":memory:"
    conn = await open_db()
    yield conn
    await conn.close()
    del os.environ["EAC_DB_PATH"]


@pytest.fixture
def mock_qdrant():
    """Minimal Qdrant client mock — records upsert calls without real vector ops."""
    client = MagicMock()
    client.upsert = MagicMock()
    client.delete = MagicMock()
    client.search = MagicMock(return_value=[])
    return client


@pytest.fixture
def mock_embedding_service():
    """Returns deterministic 1024-dim vectors without loading the ONNX model."""
    svc = MagicMock(spec=EmbeddingService)
    svc.generate.return_value = [0.1] * 1024
    svc.generate_batch.return_value = [[0.1] * 1024]
    return svc


@pytest.fixture
async def indexer(db: aiosqlite.Connection, mock_qdrant, mock_embedding_service):
    doc_repo = DocumentRepository(db)
    chunk_repo = ChunkRepository(db, mock_qdrant)
    return FileIndexer(doc_repo, chunk_repo, mock_embedding_service)


class TestIndexWorkspace:
    async def test_returns_error_for_missing_directory(self, indexer: FileIndexer) -> None:
        result = await indexer.index_workspace("/does/not/exist")
        assert len(result.errors) == 1
        assert result.files_found == 0

    async def test_indexes_txt_and_md_files(
        self, indexer: FileIndexer, tmp_path: Path
    ) -> None:
        (tmp_path / "doc.md").write_text("# Hello\nThis is a test document.", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("Some plain text notes.", encoding="utf-8")
        (tmp_path / "ignore.pdf").write_bytes(b"%PDF")

        result = await indexer.index_workspace(str(tmp_path))
        assert result.files_found == 2
        assert result.files_indexed == 2
        assert result.files_skipped == 0
        assert result.errors == []

    async def test_skips_unchanged_files(
        self, indexer: FileIndexer, tmp_path: Path
    ) -> None:
        f = tmp_path / "doc.md"
        f.write_text("Content", encoding="utf-8")

        await indexer.index_workspace(str(tmp_path))
        result = await indexer.index_workspace(str(tmp_path))

        assert result.files_skipped == 1
        assert result.files_indexed == 0

    async def test_reindexes_changed_files(
        self, indexer: FileIndexer, tmp_path: Path
    ) -> None:
        f = tmp_path / "doc.md"
        f.write_text("Original content", encoding="utf-8")
        await indexer.index_workspace(str(tmp_path))

        f.write_text("Updated content", encoding="utf-8")
        result = await indexer.index_workspace(str(tmp_path))

        assert result.files_indexed == 1
        assert result.files_skipped == 0

    async def test_empty_directory_produces_no_errors(
        self, indexer: FileIndexer, tmp_path: Path
    ) -> None:
        result = await indexer.index_workspace(str(tmp_path))
        assert result.files_found == 0
        assert result.errors == []
        assert result.status == "completed"

    async def test_status_completed_with_errors_on_failure(
        self, indexer: FileIndexer, tmp_path: Path
    ) -> None:
        f = tmp_path / "bad.md"
        f.write_text("content", encoding="utf-8")

        # Force a read error
        with patch.object(Path, "read_text", side_effect=PermissionError("no access")):
            result = await indexer.index_workspace(str(tmp_path))

        assert result.status == "completed_with_errors"
        assert len(result.errors) == 1
