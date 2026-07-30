"""Indexes local workspace files into SQLite, Qdrant, and the knowledge graph."""

from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from enterprise_ai_companion.capabilities.graph.graph_provider import GraphProvider
from enterprise_ai_companion.capabilities.graph.knowledge_graph_service import KnowledgeGraphService
from enterprise_ai_companion.capabilities.graph.null_graph_provider import NullGraphProvider
from enterprise_ai_companion.capabilities.indexing.chunk_repository import (
    Chunk,
    ChunkRepository,
)
from enterprise_ai_companion.capabilities.indexing.document_repository import (
    DocumentRepository,
    IndexedDocument,
)
from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
from enterprise_ai_companion.capabilities.indexing.text_chunker import TextChunker

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".txt", ".md"}


@dataclass
class IndexingResult:
    files_found: int = 0
    files_indexed: int = 0
    files_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "completed" if not self.errors else "completed_with_errors"


class FileIndexer:
    """Recursively indexes text files in a workspace directory.

    For each file that is new or has changed (detected by SHA-256 hash), the
    indexer chunks the content, generates embeddings, persists both to SQLite
    (via DocumentRepository / ChunkRepository) and Qdrant, then builds graph
    entities via KnowledgeGraphService (best-effort — graph failures never abort
    indexing).
    """

    def __init__(
        self,
        doc_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        embedding_service: EmbeddingService,
        chunker: TextChunker | None = None,
        graph_provider: GraphProvider | None = None,
    ) -> None:
        self._doc_repo = doc_repo
        self._chunk_repo = chunk_repo
        self._embedding_service = embedding_service
        self._chunker = chunker or TextChunker()
        self._graph_service = KnowledgeGraphService(graph_provider or NullGraphProvider())

    async def index_workspace(self, workspace_path: str) -> IndexingResult:
        """Index all supported files under workspace_path. Returns a summary."""
        root = Path(workspace_path).resolve()
        result = IndexingResult()

        if not root.exists() or not root.is_dir():
            result.errors.append(f"Workspace path does not exist or is not a directory: {root}")
            return result

        files = [
            p for p in root.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        result.files_found = len(files)

        for file_path in files:
            try:
                indexed = await self._index_file(file_path, workspace_path)
                if indexed:
                    result.files_indexed += 1
                else:
                    result.files_skipped += 1
            except Exception as exc:
                logger.warning("Failed to index %s: %s", file_path, exc)
                result.errors.append(f"{file_path}: {exc}")

        logger.info(
            "Indexing complete: %d found, %d indexed, %d skipped, %d errors",
            result.files_found,
            result.files_indexed,
            result.files_skipped,
            len(result.errors),
        )
        return result

    async def _index_file(self, file_path: Path, workspace_path: str) -> bool:
        """Index a single file. Returns True if indexed, False if unchanged."""
        text = file_path.read_text(encoding="utf-8", errors="replace")
        file_hash = hashlib.sha256(text.encode()).hexdigest()

        existing = await self._doc_repo.get_by_path(str(file_path))
        if existing and existing.file_hash == file_hash:
            return False  # unchanged

        # Remove stale chunks and graph nodes before re-indexing.
        if existing:
            await self._chunk_repo.delete_by_document(existing.id)
            await self._graph_service.delete_document(existing.id)

        raw_chunks = self._chunker.chunk(text)
        if not raw_chunks:
            return False

        doc_id = str(uuid.uuid4())
        chunks = [
            Chunk(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                chunk_index=i,
                content=content,
                char_start=char_start,
                char_end=char_end,
            )
            for i, (content, char_start, char_end) in enumerate(raw_chunks)
        ]

        embeddings = self._embedding_service.generate_batch([c.content for c in chunks])

        # Document row must exist before chunks are inserted (FK constraint).
        doc = IndexedDocument(
            id=doc_id,
            workspace_path=workspace_path,
            file_path=str(file_path),
            file_hash=file_hash,
            char_count=len(text),
            chunk_count=len(chunks),
            indexed_at=datetime.now(UTC).isoformat(),
        )
        await self._doc_repo.upsert(doc)

        await self._chunk_repo.save_batch(chunks, embeddings)

        # Graph building is best-effort — failure here must not abort indexing.
        try:
            await self._graph_service.build_from_chunks(
                doc_id,
                [c.content for c in chunks],
            )
        except Exception as exc:
            logger.warning("Graph build failed for %s: %s", file_path.name, exc)

        logger.debug("Indexed %s (%d chunks)", file_path.name, len(chunks))
        return True
