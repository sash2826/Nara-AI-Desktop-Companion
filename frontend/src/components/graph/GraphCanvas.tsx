/**
 * GraphCanvas — library-free SVG force-directed graph renderer.
 *
 * Layout: spring-charge simulation running in a useLayoutEffect.
 * Navigation: pan (drag background), zoom (scroll wheel / pinch).
 * No D3, no additional npm dependencies.
 *
 * Performance contract: up to ~150 nodes renders comfortably at 60 fps.
 * For larger graphs the force iterations are reduced automatically.
 */

import { useRef, useLayoutEffect, useState, useCallback, useEffect, type MouseEvent } from "react";
import type { GraphVisNode, GraphVisEdge } from "@/services/ipc/IPCClient";
import { cn } from "@/lib/utils";

// ─── Entity type colours ──────────────────────────────────────────────────────

const ENTITY_COLORS: Record<string, string> = {
  Person: "#6366f1",
  Organisation: "#0ea5e9",
  Project: "#10b981",
  Technology: "#f59e0b",
  Location: "#ec4899",
  Event: "#8b5cf6",
  Product: "#14b8a6",
  Concept: "#64748b",
  unknown: "#94a3b8",
};

function entityColor(type: string): string {
  return ENTITY_COLORS[type] ?? ENTITY_COLORS.unknown;
}

// ─── Force simulation types ───────────────────────────────────────────────────

interface SimNode extends GraphVisNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface SimEdge extends GraphVisEdge {
  sourceNode: SimNode;
  targetNode: SimNode;
}

// ─── Force simulation ─────────────────────────────────────────────────────────

const REPULSION = 3500;
const SPRING_K = 0.04;
const SPRING_LEN = 120;
const DAMPING = 0.85;
const ALPHA_MIN = 0.005;

function buildSimulation(
  nodes: GraphVisNode[],
  edges: GraphVisEdge[],
  width: number,
  height: number
): { simNodes: SimNode[]; simEdges: SimEdge[] } {
  const cx = width / 2;
  const cy = height / 2;
  const angle = (2 * Math.PI) / Math.max(nodes.length, 1);

  const simNodes: SimNode[] = nodes.map((n, i) => ({
    ...n,
    x: cx + Math.cos(angle * i) * Math.min(cx, cy) * 0.6,
    y: cy + Math.sin(angle * i) * Math.min(cx, cy) * 0.6,
    vx: 0,
    vy: 0,
  }));

  const idToNode = new Map<string, SimNode>(simNodes.map((n) => [n.id, n]));

  const simEdges: SimEdge[] = edges
    .map((e) => {
      const sourceNode = idToNode.get(e.source);
      const targetNode = idToNode.get(e.target);
      if (!sourceNode || !targetNode) return null;
      return { ...e, sourceNode, targetNode };
    })
    .filter((e): e is SimEdge => e !== null);

  return { simNodes, simEdges };
}

function tick(simNodes: SimNode[], simEdges: SimEdge[], alpha: number): void {
  const n = simNodes.length;

  // Repulsion between all pairs
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const a = simNodes[i];
      const b = simNodes[j];
      const dx = b.x - a.x || 0.01;
      const dy = b.y - a.y || 0.01;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = (alpha * REPULSION) / (dist * dist);
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      a.vx -= fx;
      a.vy -= fy;
      b.vx += fx;
      b.vy += fy;
    }
  }

  // Spring attraction along edges
  for (const e of simEdges) {
    const dx = e.targetNode.x - e.sourceNode.x;
    const dy = e.targetNode.y - e.sourceNode.y;
    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
    const stretch = dist - SPRING_LEN;
    const force = SPRING_K * stretch * alpha;
    const fx = (dx / dist) * force;
    const fy = (dy / dist) * force;
    e.sourceNode.vx += fx;
    e.sourceNode.vy += fy;
    e.targetNode.vx -= fx;
    e.targetNode.vy -= fy;
  }

  // Integrate velocities
  for (const node of simNodes) {
    node.vx *= DAMPING;
    node.vy *= DAMPING;
    node.x += node.vx;
    node.y += node.vy;
  }
}

// ─── Pan / zoom state ─────────────────────────────────────────────────────────

interface Transform {
  tx: number; // x translation
  ty: number; // y translation
  scale: number;
}

const ZOOM_MIN = 0.15;
const ZOOM_MAX = 4.0;
const ZOOM_STEP = 0.12;

// ─── Component ────────────────────────────────────────────────────────────────

interface GraphCanvasProps {
  nodes: GraphVisNode[];
  edges: GraphVisEdge[];
  selectedNodeId: string | null;
  onNodeClick: (node: GraphVisNode) => void;
  className?: string;
}

export function GraphCanvas({
  nodes,
  edges,
  selectedNodeId,
  onNodeClick,
  className,
}: GraphCanvasProps) {
  const containerRef = useRef<SVGSVGElement>(null);
  const [simState, setSimState] = useState<{
    nodes: SimNode[];
    edges: SimEdge[];
  }>({ nodes: [], edges: [] });
  const [hoveredEdge, setHoveredEdge] = useState<string | null>(null);

  // Pan/zoom transform
  const [transform, setTransform] = useState<Transform>({ tx: 0, ty: 0, scale: 1 });

  // Interaction mode refs — use refs so event handlers don't close over stale state
  const dragNodeRef = useRef<{ node: SimNode; offsetX: number; offsetY: number } | null>(null);
  const panRef = useRef<{
    startX: number;
    startY: number;
    startTx: number;
    startTy: number;
  } | null>(null);
  const transformRef = useRef<Transform>(transform);

  useEffect(() => {
    transformRef.current = transform;
  }, [transform]);

  // ── Force simulation ──────────────────────────────────────────────────────

  useLayoutEffect(() => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const width = rect.width || containerRef.current.clientWidth || 800;
    const height = rect.height || containerRef.current.clientHeight || 600;
    const { simNodes, simEdges } = buildSimulation(nodes, edges, width, height);

    if (simNodes.length === 0) {
      setSimState({ nodes: [], edges: [] });
      return;
    }

    // Reset transform when graph data changes so nodes start centred
    setTransform({ tx: 0, ty: 0, scale: 1 });

    // Run the entire simulation synchronously — no RAF loop, no incremental
    // setSimState calls.  An animated loop calls setSimState ~60×/s while
    // also executing O(n²) physics on the main thread; with 150 nodes that
    // blocks long enough to crash the WebView.  A single synchronous pass
    // completes in <10 ms even at 150 nodes and triggers exactly one render.
    const maxIter = simNodes.length > 80 ? 80 : 150;
    let alpha = 1.0;
    let iter = 0;
    while (alpha >= ALPHA_MIN && iter < maxIter) {
      tick(simNodes, simEdges, alpha);
      alpha *= 0.97;
      iter++;
    }
    setSimState({ nodes: [...simNodes], edges: [...simEdges] });
  }, [nodes, edges]);

  // ── Coordinate helpers ────────────────────────────────────────────────────

  // Convert a mouse event position (in SVG viewport coords) to graph-space coords
  const toGraphCoords = useCallback((e: MouseEvent): { x: number; y: number } => {
    const svg = containerRef.current;
    if (!svg) return { x: 0, y: 0 };
    const rect = svg.getBoundingClientRect();
    const { tx, ty, scale } = transformRef.current;
    const svgX = e.clientX - rect.left;
    const svgY = e.clientY - rect.top;
    return {
      x: (svgX - tx) / scale,
      y: (svgY - ty) / scale,
    };
  }, []);

  // ── Node drag ─────────────────────────────────────────────────────────────

  const handleNodeMouseDown = useCallback(
    (e: MouseEvent, node: SimNode) => {
      e.stopPropagation();
      const pt = toGraphCoords(e);
      dragNodeRef.current = { node, offsetX: pt.x - node.x, offsetY: pt.y - node.y };
    },
    [toGraphCoords]
  );

  // ── Background pan ────────────────────────────────────────────────────────

  const handleSvgMouseDown = useCallback((e: MouseEvent) => {
    // Only start pan when clicking on the SVG background (not a node)
    if (e.target !== containerRef.current && (e.target as Element).closest("g[data-node]") !== null)
      return;
    const { tx, ty } = transformRef.current;
    panRef.current = { startX: e.clientX, startY: e.clientY, startTx: tx, startTy: ty };
  }, []);

  const handleSvgMouseMove = useCallback(
    (e: MouseEvent) => {
      // Node drag takes priority
      if (dragNodeRef.current) {
        const pt = toGraphCoords(e);
        dragNodeRef.current.node.x = pt.x - dragNodeRef.current.offsetX;
        dragNodeRef.current.node.y = pt.y - dragNodeRef.current.offsetY;
        dragNodeRef.current.node.vx = 0;
        dragNodeRef.current.node.vy = 0;
        setSimState((s) => ({ ...s }));
        return;
      }

      // Pan
      if (panRef.current) {
        const dx = e.clientX - panRef.current.startX;
        const dy = e.clientY - panRef.current.startY;
        setTransform((t) => ({
          ...t,
          tx: panRef.current!.startTx + dx,
          ty: panRef.current!.startTy + dy,
        }));
      }
    },
    [toGraphCoords]
  );

  const handleSvgMouseUp = useCallback(() => {
    dragNodeRef.current = null;
    panRef.current = null;
  }, []);

  // ── Scroll zoom — attached as non-passive so preventDefault works ─────────
  useEffect(() => {
    const svg = containerRef.current;
    if (!svg) return;
    const handler = (e: globalThis.WheelEvent) => {
      e.preventDefault();
      const rect = svg.getBoundingClientRect();
      const cursorX = e.clientX - rect.left;
      const cursorY = e.clientY - rect.top;
      setTransform((t) => {
        const delta = e.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP;
        const newScale = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, t.scale + delta * t.scale));
        const ratio = newScale / t.scale;
        return {
          scale: newScale,
          tx: cursorX - ratio * (cursorX - t.tx),
          ty: cursorY - ratio * (cursorY - t.ty),
        };
      });
    };
    svg.addEventListener("wheel", handler, { passive: false });
    return () => svg.removeEventListener("wheel", handler);
  }, []);

  // ── Zoom controls ─────────────────────────────────────────────────────────

  const zoomIn = useCallback(() => {
    const svg = containerRef.current;
    if (!svg) return;
    const { width, height } = svg.getBoundingClientRect();
    const cx = width / 2;
    const cy = height / 2;
    setTransform((t) => {
      const newScale = Math.min(ZOOM_MAX, t.scale * (1 + ZOOM_STEP));
      const ratio = newScale / t.scale;
      return { scale: newScale, tx: cx - ratio * (cx - t.tx), ty: cy - ratio * (cy - t.ty) };
    });
  }, []);

  const zoomOut = useCallback(() => {
    const svg = containerRef.current;
    if (!svg) return;
    const { width, height } = svg.getBoundingClientRect();
    const cx = width / 2;
    const cy = height / 2;
    setTransform((t) => {
      const newScale = Math.max(ZOOM_MIN, t.scale * (1 - ZOOM_STEP));
      const ratio = newScale / t.scale;
      return { scale: newScale, tx: cx - ratio * (cx - t.tx), ty: cy - ratio * (cy - t.ty) };
    });
  }, []);

  const resetView = useCallback(() => {
    setTransform({ tx: 0, ty: 0, scale: 1 });
  }, []);

  const NODE_R = 20;

  return (
    <div className={cn("relative rounded-xl", className)}>
      <svg
        ref={containerRef}
        className="h-full w-full cursor-grab select-none rounded-xl border border-border bg-card active:cursor-grabbing"
        onMouseDown={handleSvgMouseDown}
        onMouseMove={handleSvgMouseMove}
        onMouseUp={handleSvgMouseUp}
        onMouseLeave={handleSvgMouseUp}
      >
        {/* Empty state overlay */}
        {nodes.length === 0 && (
          <foreignObject x="0" y="0" width="100%" height="100%">
            <div className="flex h-full w-full flex-col items-center justify-center gap-3 text-center">
              <div className="text-3xl opacity-30">◎</div>
              <p className="text-sm text-muted-foreground">
                No entities in the knowledge graph yet.
              </p>
              <p className="text-xs text-muted-foreground">
                Index some documents to populate the graph.
              </p>
            </div>
          </foreignObject>
        )}

        <defs>
          <marker id="arrowhead" markerWidth="8" markerHeight="8" refX="8" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="currentColor" className="text-muted-foreground/50" />
          </marker>
        </defs>

        {/* Pan/zoom transform group */}
        <g transform={`translate(${transform.tx},${transform.ty}) scale(${transform.scale})`}>
          {/* Edges */}
          <g>
            {simState.edges.map((e) => {
              const key = `${e.source}-${e.target}-${e.relation_type}`;
              const isHovered = hoveredEdge === key;
              const midX = (e.sourceNode.x + e.targetNode.x) / 2;
              const midY = (e.sourceNode.y + e.targetNode.y) / 2;

              const dx = e.targetNode.x - e.sourceNode.x;
              const dy = e.targetNode.y - e.sourceNode.y;
              const dist = Math.sqrt(dx * dx + dy * dy) || 1;
              const ux = dx / dist;
              const uy = dy / dist;
              const x1 = e.sourceNode.x + ux * NODE_R;
              const y1 = e.sourceNode.y + uy * NODE_R;
              const x2 = e.targetNode.x - ux * (NODE_R + 8);
              const y2 = e.targetNode.y - uy * (NODE_R + 8);

              return (
                <g key={key}>
                  <line
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    className={cn(
                      "transition-all",
                      isHovered ? "stroke-foreground/60" : "stroke-muted-foreground/30"
                    )}
                    strokeWidth={isHovered ? 1.5 : 1}
                    markerEnd="url(#arrowhead)"
                    onMouseEnter={() => setHoveredEdge(key)}
                    onMouseLeave={() => setHoveredEdge(null)}
                  />
                  {isHovered && (
                    <text
                      x={midX}
                      y={midY - 6}
                      textAnchor="middle"
                      className="fill-foreground text-[9px] font-medium"
                      fontSize={9}
                    >
                      {e.relation_type}
                    </text>
                  )}
                </g>
              );
            })}
          </g>

          {/* Nodes */}
          <g>
            {simState.nodes.map((node) => {
              const isSelected = node.id === selectedNodeId;
              const color = entityColor(node.entity_type);
              return (
                <g
                  key={node.id}
                  data-node="1"
                  transform={`translate(${node.x},${node.y})`}
                  className="cursor-pointer"
                  onClick={() => onNodeClick(node)}
                  onMouseDown={(e) => handleNodeMouseDown(e, node)}
                >
                  {isSelected && (
                    <circle
                      r={NODE_R + 4}
                      fill="none"
                      stroke={color}
                      strokeWidth={2}
                      opacity={0.5}
                    />
                  )}
                  <circle
                    r={NODE_R}
                    fill={color}
                    fillOpacity={0.85}
                    stroke={isSelected ? color : "transparent"}
                    strokeWidth={2}
                    className="transition-all"
                  />
                  <circle
                    r={NODE_R}
                    fill="none"
                    stroke="white"
                    strokeWidth={1.5}
                    strokeDasharray={`${node.confidence * 2 * Math.PI * NODE_R} 999`}
                    strokeOpacity={0.3}
                    transform="rotate(-90)"
                  />
                  <text
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize={9}
                    fontWeight={600}
                    fill="white"
                    className="pointer-events-none"
                    style={{ textShadow: "0 1px 2px rgba(0,0,0,0.4)" }}
                  >
                    {node.label.length > 10 ? node.label.slice(0, 9) + "…" : node.label}
                  </text>
                  <text
                    y={NODE_R + 12}
                    textAnchor="middle"
                    fontSize={8}
                    className="pointer-events-none fill-muted-foreground"
                  >
                    {node.entity_type}
                  </text>
                </g>
              );
            })}
          </g>
        </g>
      </svg>

      {/* Zoom controls — overlaid bottom-right of the canvas */}
      {simState.nodes.length > 0 && (
        <div className="absolute bottom-3 right-3 flex flex-col gap-1">
          <button
            onClick={zoomIn}
            title="Zoom in"
            className="flex h-7 w-7 items-center justify-center rounded-md border border-border bg-card text-sm font-semibold text-muted-foreground shadow-sm transition-colors hover:bg-accent hover:text-foreground"
          >
            +
          </button>
          <button
            onClick={zoomOut}
            title="Zoom out"
            className="flex h-7 w-7 items-center justify-center rounded-md border border-border bg-card text-sm font-semibold text-muted-foreground shadow-sm transition-colors hover:bg-accent hover:text-foreground"
          >
            −
          </button>
          <button
            onClick={resetView}
            title="Reset view"
            className="flex h-7 w-7 items-center justify-center rounded-md border border-border bg-card text-xs text-muted-foreground shadow-sm transition-colors hover:bg-accent hover:text-foreground"
          >
            ⊙
          </button>
        </div>
      )}

      {/* Zoom level indicator */}
      {simState.nodes.length > 0 && transform.scale !== 1 && (
        <div className="absolute bottom-3 left-3 rounded-md border border-border bg-card/80 px-2 py-0.5 text-xs text-muted-foreground">
          {Math.round(transform.scale * 100)}%
        </div>
      )}
    </div>
  );
}
