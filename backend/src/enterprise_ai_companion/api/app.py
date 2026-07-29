"""FastAPI application for the Enterprise AI Companion backend."""

from fastapi import FastAPI

from enterprise_ai_companion.api.routers import embeddings

app = FastAPI(
    title="Enterprise AI Companion",
    version="0.1.0",
    description="Local backend service for the Enterprise AI Companion desktop app.",
)

app.include_router(embeddings.router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe used by the Tauri IPC health_check command."""
    return {"status": "ok"}
