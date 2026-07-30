"""Graph router — knowledge graph query endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/graph", tags=["graph"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class EntityResponse(BaseModel):
    id: str
    name: str
    entity_type: str
    source_document_id: str
    properties: dict


class RelationshipResponse(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str
    properties: dict


class GraphContextResponse(BaseModel):
    entity: EntityResponse
    related_entities: list[EntityResponse]
    relationships: list[RelationshipResponse]


class GraphHealthResponse(BaseModel):
    connected: bool
    provider: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/entity/{entity_name}", response_model=GraphContextResponse)
async def get_entity_context(
    entity_name: str,
    depth: int = 1,
    request: Request = ...,  # type: ignore[assignment]
) -> GraphContextResponse:
    """Return a named entity and its neighbourhood from the knowledge graph.

    Args:
        entity_name: Exact entity name to look up.
        depth: Neighbourhood traversal depth (1–3, default 1).
    """
    if not entity_name.strip():
        raise HTTPException(status_code=422, detail="entity_name must not be empty")
    if not 1 <= depth <= 3:
        raise HTTPException(status_code=422, detail="depth must be between 1 and 3")

    graph = request.app.state.graph
    context = await graph.get_context(entity_name.strip(), depth=depth)

    if context is None:
        raise HTTPException(
            status_code=404,
            detail=f"Entity '{entity_name}' not found in the knowledge graph.",
        )

    return GraphContextResponse(
        entity=_entity_to_response(context.entity),
        related_entities=[_entity_to_response(e) for e in context.related_entities],
        relationships=[_rel_to_response(r) for r in context.relationships],
    )


@router.get("/health", response_model=GraphHealthResponse)
async def graph_health(request: Request) -> GraphHealthResponse:
    """Return the health of the graph provider."""
    graph = request.app.state.graph
    connected = await graph.health()
    provider = type(graph).__name__
    return GraphHealthResponse(connected=connected, provider=provider)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity_to_response(entity: object) -> EntityResponse:
    return EntityResponse(
        id=entity.id,  # type: ignore[attr-defined]
        name=entity.name,  # type: ignore[attr-defined]
        entity_type=entity.entity_type.value,  # type: ignore[attr-defined]
        source_document_id=entity.source_document_id,  # type: ignore[attr-defined]
        properties=dict(entity.properties),  # type: ignore[attr-defined]
    )


def _rel_to_response(rel: object) -> RelationshipResponse:
    return RelationshipResponse(
        source_id=rel.source_id,  # type: ignore[attr-defined]
        target_id=rel.target_id,  # type: ignore[attr-defined]
        relationship_type=rel.relationship_type.value,  # type: ignore[attr-defined]
        properties=dict(rel.properties),  # type: ignore[attr-defined]
    )
