"""Graph router — knowledge graph query endpoints."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from enterprise_ai_companion.capabilities.graph.graph_query_service import (
    EntitySearchResult,
    GraphQueryService,
)
from enterprise_ai_companion.capabilities.graph.traversal_engine import TraversalEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class EntityResponse(BaseModel):
    id: str
    name: str
    entity_type: str
    confidence: float = 1.0
    source_document_id: str
    properties: dict


class RelationshipResponse(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str
    confidence: float = 1.0
    properties: dict


class GraphNeighborhoodResponse(BaseModel):
    root: EntityResponse
    neighbours: list[EntityResponse]
    relationships: list[RelationshipResponse]


class EntitySearchResponse(BaseModel):
    results: list[EntitySearchResult]


class GraphPathResponse(BaseModel):
    source_name: str
    target_name: str
    node_names: list[str]
    length: int
    found: bool


class ConnectedDocumentsResponse(BaseModel):
    entity_name: str
    document_ids: list[str]


class GraphContextResponse(BaseModel):
    entity: EntityResponse
    related_entities: list[EntityResponse]
    relationships: list[RelationshipResponse]


class GraphHealthResponse(BaseModel):
    connected: bool
    provider: str


class GraphVisNode(BaseModel):
    id: str
    label: str
    entity_type: str
    confidence: float
    source_document_path: str | None = None


class GraphVisEdge(BaseModel):
    source: str        # entity UUID — used by the force layout
    source_name: str   # human-readable name for display
    target: str        # entity UUID
    target_name: str   # human-readable name for display
    relation_type: str
    confidence: float


class GraphVisualizationResponse(BaseModel):
    nodes: list[GraphVisNode]
    edges: list[GraphVisEdge]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/entity/{entity_name}", response_model=GraphContextResponse)
async def get_entity_context(
    entity_name: str,
    depth: int = 1,
    request: Request = ...,  # type: ignore[assignment]
) -> GraphContextResponse:
    """Return a named entity and its neighbourhood from the knowledge graph."""
    if not entity_name.strip():
        raise HTTPException(status_code=422, detail="entity_name must not be empty")
    if not 1 <= depth <= 3:
        raise HTTPException(status_code=422, detail="depth must be between 1 and 3")

    svc = GraphQueryService(request.app.state.graph)
    context = await svc.get_entity(entity_name.strip())

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


@router.get("/neighborhood/{entity_name}", response_model=GraphNeighborhoodResponse)
async def get_neighborhood(
    entity_name: str,
    depth: int = 2,
    request: Request = ...,  # type: ignore[assignment]
) -> GraphNeighborhoodResponse:
    """Return an entity and its N-hop neighbourhood (depth 1–3)."""
    if not entity_name.strip():
        raise HTTPException(status_code=422, detail="entity_name must not be empty")
    if not 1 <= depth <= 3:
        raise HTTPException(status_code=422, detail="depth must be between 1 and 3")

    svc = GraphQueryService(request.app.state.graph)
    hood = await svc.get_neighborhood(entity_name.strip(), depth=depth)

    if hood is None:
        raise HTTPException(
            status_code=404,
            detail=f"Entity '{entity_name}' not found in the knowledge graph.",
        )

    return GraphNeighborhoodResponse(
        root=_entity_to_response(hood.root),
        neighbours=[_entity_to_response(e) for e in hood.neighbours],
        relationships=[_rel_to_response(r) for r in hood.relationships],
    )


@router.get("/search", response_model=EntitySearchResponse)
async def search_entities(
    q: str,
    entity_type: Optional[str] = None,
    limit: int = 10,
    request: Request = ...,  # type: ignore[assignment]
) -> EntitySearchResponse:
    """Search entity names by substring (case-insensitive).

    Args:
        q: Search string.
        entity_type: Optional type filter (e.g. Person, Organization).
        limit: Maximum results (1–50).
    """
    if not q.strip():
        raise HTTPException(status_code=422, detail="q must not be empty")
    limit = max(1, min(limit, 50))

    svc = GraphQueryService(request.app.state.graph)
    results = await svc.search_entities(q.strip(), entity_type=entity_type, limit=limit)
    return EntitySearchResponse(results=results)


@router.get("/path", response_model=GraphPathResponse)
async def find_path(
    from_entity: str,
    to_entity: str,
    request: Request = ...,  # type: ignore[assignment]
) -> GraphPathResponse:
    """Find the shortest path between two named entities (max 6 hops).

    Args:
        from_entity: Start entity name.
        to_entity: Target entity name.
    """
    if not from_entity.strip() or not to_entity.strip():
        raise HTTPException(
            status_code=422, detail="from_entity and to_entity must not be empty"
        )

    engine = TraversalEngine(request.app.state.graph)
    path = await engine.find_path(from_entity.strip(), to_entity.strip())

    return GraphPathResponse(
        source_name=path.source_name,
        target_name=path.target_name,
        node_names=path.node_names,
        length=path.length,
        found=path.found,
    )


@router.get("/documents/{entity_name}", response_model=ConnectedDocumentsResponse)
async def get_connected_documents(
    entity_name: str,
    request: Request = ...,  # type: ignore[assignment]
) -> ConnectedDocumentsResponse:
    """Return document IDs connected to a named entity (up to 2 hops).

    Used by the context assembler to expand retrieval via graph neighbours.
    """
    if not entity_name.strip():
        raise HTTPException(status_code=422, detail="entity_name must not be empty")

    engine = TraversalEngine(request.app.state.graph)
    doc_ids = await engine.get_connected_documents(entity_name.strip())

    return ConnectedDocumentsResponse(
        entity_name=entity_name.strip(),
        document_ids=doc_ids,
    )


@router.get("/visualize", response_model=GraphVisualizationResponse)
async def get_graph_visualization(
    request: Request,
    entity: Optional[str] = None,
    depth: int = 2,
) -> GraphVisualizationResponse:
    """Return nodes and edges suitable for frontend graph rendering.

    When ``entity`` is provided the subgraph is centred on that entity.
    When omitted the provider returns a global overview (may be capped).
    Returns empty nodes/edges when the graph is empty or Neo4j is offline.

    Args:
        entity: Optional focal entity name.
        depth: Traversal depth (1–3, default 2).
    """
    if not 1 <= depth <= 3:
        raise HTTPException(status_code=422, detail="depth must be between 1 and 3")

    graph = request.app.state.graph

    try:
        if not await graph.health():
            logger.warning("Graph provider offline — returning empty visualization")
            return GraphVisualizationResponse(nodes=[], edges=[])

        raw = await graph.get_visualization(
            entity_name=entity.strip() if entity else None,
            depth=depth,
        )

        nodes = [
            GraphVisNode(
                id=n["id"],
                label=n["label"],
                entity_type=n.get("entity_type", "unknown"),
                confidence=float(n.get("confidence", 1.0)),
                source_document_path=n.get("source_document_path"),
            )
            for n in raw.get("nodes", [])
        ]
        edges = [
            GraphVisEdge(
                source=e["source"],
                source_name=e.get("source_name", e["source"]),
                target=e["target"],
                target_name=e.get("target_name", e["target"]),
                relation_type=e.get("relation_type", "RELATED_TO"),
                confidence=float(e.get("confidence", 1.0)),
            )
            for e in raw.get("edges", [])
        ]
        return GraphVisualizationResponse(nodes=nodes, edges=edges)

    except Exception:
        logger.exception("Failed to build graph visualization — returning empty response")
        return GraphVisualizationResponse(nodes=[], edges=[])


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
        confidence=getattr(entity, "confidence", 1.0),
        source_document_id=entity.source_document_id,  # type: ignore[attr-defined]
        properties=dict(entity.properties),  # type: ignore[attr-defined]
    )


def _rel_to_response(rel: object) -> RelationshipResponse:
    return RelationshipResponse(
        source_id=rel.source_id,  # type: ignore[attr-defined]
        target_id=rel.target_id,  # type: ignore[attr-defined]
        relationship_type=rel.relationship_type.value,  # type: ignore[attr-defined]
        confidence=getattr(rel, "confidence", 1.0),
        properties=dict(rel.properties),  # type: ignore[attr-defined]
    )
