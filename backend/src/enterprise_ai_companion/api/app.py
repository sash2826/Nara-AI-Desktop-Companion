"""FastAPI application for the Enterprise AI Companion backend."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from enterprise_ai_companion.api.routers import conversations, embeddings
from enterprise_ai_companion.infrastructure.database import close_db, open_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Open the database on startup and close it on shutdown."""
    app.state.db = await open_db()
    try:
        yield
    finally:
        await close_db(app.state.db)
        app.state.db = None


app = FastAPI(
    title="Enterprise AI Companion",
    version="0.1.0",
    description="Local backend service for the Enterprise AI Companion desktop app.",
    lifespan=lifespan,
)

app.include_router(embeddings.router)
app.include_router(conversations.router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe used by the Tauri IPC health_check command."""
    return {"status": "ok"}
