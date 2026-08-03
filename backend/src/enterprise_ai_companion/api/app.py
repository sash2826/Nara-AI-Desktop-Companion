"""FastAPI application for the Enterprise AI Companion backend."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from enterprise_ai_companion.api.routers import backup, conversations, documents, embeddings, graph, indexing, search
from enterprise_ai_companion.api.routers import watcher as watcher_router_module
from enterprise_ai_companion.capabilities.graph.neo4j_provider import Neo4jProvider
from enterprise_ai_companion.capabilities.graph.null_graph_provider import NullGraphProvider
from enterprise_ai_companion.capabilities.indexing.chunk_repository import ChunkRepository
from enterprise_ai_companion.capabilities.indexing.document_repository import DocumentRepository
from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
from enterprise_ai_companion.capabilities.indexing.file_indexer import FileIndexer
from enterprise_ai_companion.capabilities.indexing.file_watcher import WatcherService
from enterprise_ai_companion.infrastructure.database import close_db, open_db
from enterprise_ai_companion.infrastructure.qdrant_provider import QdrantProvider

logger = logging.getLogger(__name__)


def _build_graph_provider() -> NullGraphProvider | Neo4jProvider:
    """Return Neo4jProvider when EAC_GRAPH_PROVIDER=neo4j, else NullGraphProvider."""
    if os.environ.get("EAC_GRAPH_PROVIDER", "null").lower() == "neo4j":
        return Neo4jProvider()
    return NullGraphProvider()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Open all stores on startup; close them on shutdown."""
    app.state.db = await open_db()

    qdrant = QdrantProvider()
    qdrant.initialize()
    app.state.qdrant = qdrant

    graph_provider = _build_graph_provider()
    try:
        await graph_provider.initialize()
    except Exception as exc:
        logger.warning(
            "Graph provider failed to initialize (%s). Falling back to NullGraphProvider.", exc
        )
        graph_provider = NullGraphProvider()
        await graph_provider.initialize()
    app.state.graph = graph_provider

    # Shared FileIndexer — reused by both the manual indexing API and the watcher.
    doc_repo = DocumentRepository(app.state.db)
    chunk_repo = ChunkRepository(app.state.db, qdrant.get_client())
    embedding_service = EmbeddingService()
    app.state.file_indexer = FileIndexer(
        doc_repo, chunk_repo, embedding_service, graph_provider=graph_provider
    )

    # Background file watcher — monitors watched_folders table on startup.
    watcher = WatcherService(
        db=app.state.db,
        indexer=app.state.file_indexer,
        loop=asyncio.get_event_loop(),
    )
    await watcher._async_start()
    app.state.watcher = watcher

    app.state.indexing_tasks: dict = {}

    try:
        yield
    finally:
        app.state.watcher.stop()
        app.state.watcher = None

        await close_db(app.state.db)
        app.state.db = None

        app.state.qdrant.close()
        app.state.qdrant = None

        await app.state.graph.close()
        app.state.graph = None


app = FastAPI(
    title="Enterprise AI Companion",
    version="0.1.0",
    description="Local backend service for the Enterprise AI Companion desktop app.",
    lifespan=lifespan,
)

app.include_router(embeddings.router)
app.include_router(conversations.router)
app.include_router(indexing.router)
app.include_router(search.router)
app.include_router(graph.router)
app.include_router(backup.router)
app.include_router(documents.router)
app.include_router(watcher_router_module.router, prefix="/watcher", tags=["watcher"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe used by the Tauri IPC health_check command."""
    return {"status": "ok"}
