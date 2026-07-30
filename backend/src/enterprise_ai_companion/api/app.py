"""FastAPI application for the Enterprise AI Companion backend."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from enterprise_ai_companion.api.routers import conversations, embeddings, indexing, search
from enterprise_ai_companion.infrastructure.database import close_db, open_db
from enterprise_ai_companion.infrastructure.qdrant_provider import QdrantProvider


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Open the database and Qdrant store on startup; close both on shutdown."""
    app.state.db = await open_db()

    qdrant = QdrantProvider()
    qdrant.initialize()
    app.state.qdrant = qdrant

    app.state.indexing_tasks: dict = {}

    try:
        yield
    finally:
        await close_db(app.state.db)
        app.state.db = None

        app.state.qdrant.close()
        app.state.qdrant = None


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


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe used by the Tauri IPC health_check command."""
    return {"status": "ok"}
