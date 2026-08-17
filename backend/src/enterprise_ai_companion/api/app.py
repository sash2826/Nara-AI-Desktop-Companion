"""FastAPI application for the Enterprise AI Companion backend."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request as StarletteRequest

from enterprise_ai_companion.api.routers import backup, conversations, documents, embeddings, graph, indexing, orb as orb_router_module, plugins as plugins_router_module, search, stats
from enterprise_ai_companion.api.routers import watcher as watcher_router_module
from enterprise_ai_companion.api.routers import organisation as organisation_router_module
from enterprise_ai_companion.capabilities.organisation.affinity_repository import AffinityRepository
from enterprise_ai_companion.capabilities.organisation.file_mover import FileMover
from enterprise_ai_companion.capabilities.organisation.placement_adapters import (
    HybridRerankAdapter,
    SqliteGraphScoreAdapter,
)
from enterprise_ai_companion.capabilities.organisation.placement_scorer import PlacementScorer
from enterprise_ai_companion.capabilities.organisation.recommendation_repository import RecommendationRepository
from enterprise_ai_companion.capabilities.organisation.audit_service import AuditService
from enterprise_ai_companion.capabilities.organisation.recommendation_service import RecommendationService
from enterprise_ai_companion.capabilities.graph.graph_state_repository import GraphStateRepository
from enterprise_ai_companion.capabilities.graph.neo4j_provider import Neo4jProvider
from enterprise_ai_companion.capabilities.graph.null_graph_provider import NullGraphProvider
from enterprise_ai_companion.capabilities.graph.sqlite_graph_provider import SQLiteGraphProvider
from enterprise_ai_companion.capabilities.indexing.abbreviation_repository import AbbreviationRepository
from enterprise_ai_companion.capabilities.indexing.chunk_repository import ChunkRepository
from enterprise_ai_companion.capabilities.indexing.document_repository import DocumentRepository
from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
from enterprise_ai_companion.capabilities.indexing.file_indexer import FileIndexer
from enterprise_ai_companion.capabilities.indexing.file_watcher import WatcherService
from enterprise_ai_companion.capabilities.indexing.indexing_error_repository import IndexingErrorRepository
from enterprise_ai_companion.capabilities.retrieval.abbreviation_extractor import AbbreviationExtractor
from enterprise_ai_companion.capabilities.retrieval.query_preprocessor import QueryPreprocessor, _EXPANSIONS
from enterprise_ai_companion.capabilities.plugins.plugin_manager import PluginManager
from enterprise_ai_companion.infrastructure.audit_logger import AuditLogger
from enterprise_ai_companion.infrastructure.config import get_config
from enterprise_ai_companion.infrastructure.database import close_db, open_db
from enterprise_ai_companion.infrastructure.qdrant_provider import QdrantProvider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _build_graph_provider(
    conn: "aiosqlite.Connection | None" = None,
) -> SQLiteGraphProvider | Neo4jProvider | NullGraphProvider:
    """Return the appropriate graph provider based on EAC_GRAPH_PROVIDER.

    Default (no env var): SQLiteGraphProvider — embedded, zero-config.
    EAC_GRAPH_PROVIDER=neo4j: Neo4jProvider — requires running Neo4j.
    EAC_GRAPH_PROVIDER=null: NullGraphProvider — graph features disabled.
    """
    mode = get_config().graph_provider.lower()
    if mode == "neo4j":
        return Neo4jProvider()
    if mode == "null":
        return NullGraphProvider()
    # Default: SQLite
    if conn is None:
        raise RuntimeError("SQLiteGraphProvider requires a database connection")
    return SQLiteGraphProvider(conn)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Open all stores on startup; close them on shutdown."""
    app.state.db = await open_db()
    app.state.audit_logger = AuditLogger(app.state.db)

    plugin_manager = PluginManager(app.state.db)
    counts = await plugin_manager.initialize()
    logger.info("Plugin manager ready: %d plugin(s) loaded", counts["loaded"])
    app.state.plugin_manager = plugin_manager

    qdrant = QdrantProvider()
    qdrant.initialize()
    app.state.qdrant = qdrant

    graph_provider = _build_graph_provider(conn=app.state.db)
    try:
        await graph_provider.initialize()
    except Exception as exc:
        logger.warning(
            "Graph provider failed to initialize (%s). Falling back to NullGraphProvider.", exc
        )
        graph_provider = NullGraphProvider()
        await graph_provider.initialize()
    app.state.graph = graph_provider

    # QueryPreprocessor singleton — placed on app.state so the indexing router
    # can call merge_expansions() after each job without a circular import.
    preprocessor = QueryPreprocessor()
    app.state.preprocessor = preprocessor

    # Shared FileIndexer — reused by both the manual indexing API and the watcher.
    doc_repo = DocumentRepository(app.state.db)
    chunk_repo = ChunkRepository(app.state.db, qdrant.get_client())
    embedding_service = EmbeddingService()
    error_repo = IndexingErrorRepository(app.state.db)
    app.state.indexing_error_repo = error_repo

    abbreviation_repo = AbbreviationRepository(app.state.db)
    app.state.abbreviation_repo = abbreviation_repo

    graph_state_repo = GraphStateRepository(app.state.db)
    app.state.graph_state_repo = graph_state_repo

    # Expose chunk_repo on app.state so ContextAssembler can use it for
    # graph-augmented retrieval without re-creating the instance.
    app.state.chunk_repo = chunk_repo

    abbreviation_extractor = AbbreviationExtractor(
        static_exclusions=frozenset(_EXPANSIONS.keys())
    )

    app.state.file_indexer = FileIndexer(
        doc_repo, chunk_repo, embedding_service,
        graph_provider=graph_provider,
        error_repo=error_repo,
        abbreviation_extractor=abbreviation_extractor,
        abbreviation_repo=abbreviation_repo,
        graph_state_repo=graph_state_repo,
        plugin_manager=plugin_manager,
    )

    # Prime the preprocessor with abbreviations discovered in previous sessions.
    try:
        initial_dynamic = await abbreviation_repo.load_all()
        preprocessor.merge_expansions(initial_dynamic)
        logger.info(
            "Loaded %d dynamic abbreviation expansion(s) from previous sessions",
            len(initial_dynamic),
        )
    except Exception as exc:
        logger.warning("Failed to load initial abbreviation expansions: %s", exc)

    # Background file watcher — monitors watched_folders table on startup.
    watcher = WatcherService(
        db=app.state.db,
        indexer=app.state.file_indexer,
        loop=asyncio.get_event_loop(),
    )
    await watcher._async_start()
    app.state.watcher = watcher

    # Organisation capability — placement recommendations for new Downloads files.
    recommendation_repo = RecommendationRepository(app.state.db)
    app.state.recommendation_repo = recommendation_repo

    app.state.file_mover = FileMover(app.state.db)

    affinity_repo = AffinityRepository(app.state.db)
    app.state.affinity_repo = affinity_repo

    placement_scorer = PlacementScorer(
        graph_score_port=SqliteGraphScoreAdapter(conn=app.state.db),
        rerank_port=HybridRerankAdapter(
            conn=app.state.db,
            embedding_service=embedding_service,
            qdrant_client=qdrant.get_client(),
        ),
    )

    recommendation_service = RecommendationService(
        recommendation_repo=recommendation_repo,
        placement_scorer=placement_scorer,
    )
    app.state.recommendation_service = recommendation_service

    # Wire the Downloads hook and auto-register the Downloads folder.
    watcher.recommendation_service = recommendation_service
    await watcher._ensure_downloads_registered()

    audit_service = AuditService(
        document_repo=doc_repo,
        placement_scorer=placement_scorer,
        recommendation_repo=recommendation_repo,
    )
    app.state.audit_service = audit_service

    # Purge index records for files deleted while the backend was offline.
    # Runs as a background task so it never blocks startup.
    asyncio.create_task(watcher.reconcile_stale_files())

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


class TokenVerificationMiddleware(BaseHTTPMiddleware):
    """Reject requests that lack the per-session IPC shared secret.

    The token is generated at startup (server.py), injected via EAC_IPC_SECRET,
    and transmitted by the Tauri host as the X-EAC-Token header. When no secret
    is configured (e.g. in development without Tauri), all requests are allowed.
    """

    async def dispatch(
        self, request: StarletteRequest, call_next  # type: ignore[override]
    ):
        expected = get_config().ipc_secret
        if expected:
            provided = request.headers.get("X-EAC-Token")
            if provided != expected:
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return await call_next(request)


app = FastAPI(
    title="Enterprise AI Companion",
    version="0.1.0",
    description="Local backend service for the Enterprise AI Companion desktop app.",
    lifespan=lifespan,
)

app.add_middleware(TokenVerificationMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])


_MAX_REQUEST_BODY_BYTES = 10 * 1024 * 1024  # 10 MiB


@app.middleware("http")
async def limit_request_body(request: StarletteRequest, call_next):  # type: ignore[return]
    """Reject requests with a Content-Length header exceeding 10 MiB."""
    cl = request.headers.get("content-length")
    if cl and int(cl) > _MAX_REQUEST_BODY_BYTES:
        return JSONResponse({"detail": "Request body too large"}, status_code=413)
    return await call_next(request)


app.include_router(embeddings.router)
app.include_router(conversations.router)
app.include_router(indexing.router)
app.include_router(search.router)
app.include_router(graph.router)
app.include_router(backup.router)
app.include_router(documents.router)
app.include_router(plugins_router_module.router)
app.include_router(watcher_router_module.router, prefix="/watcher", tags=["watcher"])
app.include_router(stats.router)
app.include_router(orb_router_module.router)
app.include_router(organisation_router_module.router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe used by the Tauri IPC health_check command."""
    return {"status": "ok"}
