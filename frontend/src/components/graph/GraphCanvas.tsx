/**
 * GraphCanvas — Canvas-based force-directed graph renderer.
 *
 * Rendering: HTML5 Canvas (single drawFrame call per tick — zero DOM nodes
 * for graph content, React manages only the overlay buttons).
 * Physics: d3-force with Barnes-Hut O(n log n) repulsion via forceMany Body.
 * Navigation: pan (drag background), zoom (scroll wheel / buttons).
 *
 * Performance contract: crash-proof at any node count the backend cap allows.
 * Pan/zoom is instantaneous — no DOM reconciliation, just ctx.setTransform.
 */

import { useRef, useEffect, useLayoutEffect, useCallback, useState } from "react";
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
  type Simulation,
  type SimulationNodeDatum,
  type SimulationLinkDatum,
} from "d3-force";
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

// ─── Simulation node/link types ───────────────────────────────────────────────

interface SimNode extends SimulationNodeDatum, GraphVisNode {
  x: number;
  y: number;
}

interface SimLink extends SimulationLinkDatum<SimNode> {
  relation_type: string;
  confidence: number;
  // source/target are resolved to SimNode objects by d3 after simulation init
}

// ─── Constants ────────────────────────────────────────────────────────────────

const NODE_R = 20;
const ZOOM_MIN = 0.1;
const ZOOM_MAX = 5.0;
const ZOOM_STEP = 0.12;

// ─── Canvas drawing ───────────────────────────────────────────────────────────

function drawArrow(
  ctx: CanvasRenderingContext2D,
  x1: number,
  y1: number,
  x2: number,
  y2: number
): void {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const dist = Math.sqrt(dx * dx + dy * dy) || 1;
  const ux = dx / dist;
  const uy = dy / dist;
  // Trim line to node edge + arrowhead clearance
  const sx = x1 + ux * NODE_R;
  const sy = y1 + uy * NODE_R;
  const ex = x2 - ux * (NODE_R + 8);
  const ey = y2 - uy * (NODE_R + 8);

  ctx.beginPath();
  ctx.moveTo(sx, sy);
  ctx.lineTo(ex, ey);
  ctx.stroke();

  // Arrowhead
  const angle = Math.atan2(ey - sy, ex - sx);
  ctx.beginPath();
  ctx.moveTo(ex, ey);
  ctx.lineTo(ex - 8 * Math.cos(angle - 0.4), ey - 8 * Math.sin(angle - 0.4));
  ctx.lineTo(ex - 8 * Math.cos(angle + 0.4), ey - 8 * Math.sin(angle + 0.4));
  ctx.closePath();
  ctx.fill();
}

function drawFrame(
  ctx: CanvasRenderingContext2D,
  nodes: SimNode[],
  links: SimLink[],
  transform: { tx: number; ty: number; scale: number },
  selectedNodeId: string | null,
  hoveredNodeId: string | null,
  hoveredLinkKey: string | null,
  isDark: boolean
): void {
  const { width, height } = ctx.canvas;
  ctx.clearRect(0, 0, width, height);

  ctx.save();
  ctx.translate(transform.tx, transform.ty);
  ctx.scale(transform.scale, transform.scale);

  const edgeColor = isDark ? "rgba(148,163,184,0.25)" : "rgba(100,116,139,0.25)";
  const edgeHoverColor = isDark ? "rgba(248,250,252,0.6)" : "rgba(15,23,42,0.6)";
  const labelColor = isDark ? "#94a3b8" : "#64748b";

  // ── Draw edges ──────────────────────────────────────────────────────────────
  for (const link of links) {
    const s = link.source as SimNode;
    const t = link.target as SimNode;
    if (!s?.x || !t?.x) continue;

    const key = `${(link.source as SimNode).id}-${(link.target as SimNode).id}-${link.relation_type}`;
    const isHovered = hoveredLinkKey === key;

    ctx.strokeStyle = isHovered ? edgeHoverColor : edgeColor;
    ctx.fillStyle = isHovered ? edgeHoverColor : edgeColor;
    ctx.lineWidth = isHovered ? 1.5 : 1;
    drawArrow(ctx, s.x, s.y, t.x, t.y);

    if (isHovered) {
      const mx = (s.x + t.x) / 2;
      const my = (s.y + t.y) / 2 - 8;
      ctx.fillStyle = labelColor;
      ctx.font = "600 9px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(link.relation_type, mx, my);
    }
  }

  // ── Draw nodes ──────────────────────────────────────────────────────────────
  for (const node of nodes) {
    if (node.x == null || node.y == null) continue;
    const color = entityColor(node.entity_type);
    const isSelected = node.id === selectedNodeId;
    const isHovered = node.id === hoveredNodeId;

    // Selection ring
    if (isSelected) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, NODE_R + 5, 0, 2 * Math.PI);
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.globalAlpha = 0.45;
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    // Hover ring
    if (isHovered && !isSelected) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, NODE_R + 3, 0, 2 * Math.PI);
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = 0.35;
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    // Node fill
    ctx.beginPath();
    ctx.arc(node.x, node.y, NODE_R, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.globalAlpha = 0.85;
    ctx.fill();
    ctx.globalAlpha = 1;

    // Confidence arc (white dashed arc showing confidence level)
    const arcLen = node.confidence * 2 * Math.PI;
    ctx.beginPath();
    ctx.arc(node.x, node.y, NODE_R, -Math.PI / 2, -Math.PI / 2 + arcLen);
    ctx.strokeStyle = "rgba(255,255,255,0.3)";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Label inside node
    ctx.fillStyle = "white";
    ctx.font = "600 9px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const label = node.label.length > 10 ? node.label.slice(0, 9) + "…" : node.label;
    // Text shadow via offsetting in dark color first
    ctx.fillStyle = "rgba(0,0,0,0.35)";
    ctx.fillText(label, node.x + 0.5, node.y + 0.5);
    ctx.fillStyle = "white";
    ctx.fillText(label, node.x, node.y);

    // Entity type label below node
    ctx.fillStyle = labelColor;
    ctx.font = "8px system-ui, sans-serif";
    ctx.textBaseline = "top";
    ctx.fillText(node.entity_type, node.x, node.y + NODE_R + 4);
  }

  ctx.restore();
}

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
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // d3 simulation ref — persists across renders without causing re-renders
  const simRef = useRef<Simulation<SimNode, SimLink> | null>(null);
  const simNodesRef = useRef<SimNode[]>([]);
  const simLinksRef = useRef<SimLink[]>([]);

  // Pan/zoom — stored in a ref so drawFrame doesn't require React state
  const transformRef = useRef({ tx: 0, ty: 0, scale: 1 });
  const [transform, setTransform] = useState({ tx: 0, ty: 0, scale: 1 });

  // Interaction refs
  const panRef = useRef<{
    startX: number;
    startY: number;
    startTx: number;
    startTy: number;
  } | null>(null);
  const dragNodeRef = useRef<SimNode | null>(null);
  const mouseDownClientRef = useRef<{ x: number; y: number } | null>(null);

  // Hover state — kept in refs to avoid React re-renders on every mousemove
  const hoveredNodeRef = useRef<string | null>(null);
  const hoveredLinkRef = useRef<string | null>(null);

  // Derived directly from props — no state needed
  const hasNodes = nodes.length > 0;
  const [scaleDisplay, setScaleDisplay] = useState(1);

  // Detect dark mode once (canvas needs to know for colour choices)
  const isDark = window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;

  // ── Rendering loop ─────────────────────────────────────────────────────────
  // Single RAF-based render loop driven by the d3 simulation ticks.
  // When the simulation cools, d3 stops calling tick and RAF is not re-queued.
  const rafRef = useRef<number | null>(null);

  const scheduleFrame = useCallback(() => {
    if (rafRef.current !== null) return; // already queued
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = null;
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      drawFrame(
        ctx,
        simNodesRef.current,
        simLinksRef.current,
        transformRef.current,
        selectedNodeRef.current,
        hoveredNodeRef.current,
        hoveredLinkRef.current,
        isDark
      );
    });
  }, [isDark]);

  // selectedNodeId comes from props — keep a ref so drawFrame (inside RAF)
  // always reads the latest value without capturing a stale closure.
  const selectedNodeRef = useRef<string | null>(null);
  useLayoutEffect(() => {
    // eslint-disable-next-line react-hooks/immutability -- tracking latest prop in RAF callback; cannot use useEvent (experimental)
    selectedNodeRef.current = selectedNodeId;
  }, [selectedNodeId]);

  // ── Build/restart simulation when nodes or edges change ────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Stop any running simulation
    simRef.current?.stop();

    if (nodes.length === 0) {
      simNodesRef.current = [];
      simLinksRef.current = [];
      scheduleFrame();
      return;
    }

    const { width, height } = canvas.getBoundingClientRect();
    const w = width || 800;
    const h = height || 600;

    // Reset view on new data — update the ref synchronously for drawFrame,
    // defer the React state update to avoid setState-in-effect lint error.
    const newT = { tx: 0, ty: 0, scale: 1 };
    transformRef.current = newT;
    setTimeout(() => setTransform(newT), 0);

    // Build node objects, preserving positions if same node was in previous sim
    const prevById = new Map(simNodesRef.current.map((n) => [n.id, n]));
    const cx = w / 2;
    const cy = h / 2;
    const angle = (2 * Math.PI) / Math.max(nodes.length, 1);

    const simNodes: SimNode[] = nodes.map((n, i) => {
      const prev = prevById.get(n.id);
      return {
        ...n,
        x: prev?.x ?? cx + Math.cos(angle * i) * Math.min(cx, cy) * 0.6,
        y: prev?.y ?? cy + Math.sin(angle * i) * Math.min(cx, cy) * 0.6,
      } as SimNode;
    });

    const idToNode = new Map(simNodes.map((n) => [n.id, n]));
    const simLinks: SimLink[] = edges
      .map((e): SimLink | null => {
        const s = idToNode.get(e.source);
        const t = idToNode.get(e.target);
        if (!s || !t) return null;
        return {
          source: s,
          target: t,
          relation_type: e.relation_type,
          confidence: e.confidence,
        } as SimLink;
      })
      .filter((l): l is SimLink => l !== null);

    simNodesRef.current = simNodes;
    simLinksRef.current = simLinks;

    const sim = forceSimulation<SimNode>(simNodes)
      .force("link", forceLink<SimNode, SimLink>(simLinks).distance(130).strength(0.4))
      .force("charge", forceManyBody<SimNode>().strength(-400))
      .force("center", forceCenter(cx, cy).strength(0.05))
      .force("collide", forceCollide<SimNode>(NODE_R + 6))
      .alphaDecay(0.03)
      .on("tick", scheduleFrame)
      .on("end", scheduleFrame);

    simRef.current = sim;

    return () => {
      sim.stop();
    };
  }, [nodes, edges, scheduleFrame]);

  // ── Canvas resize observer ─────────────────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        canvas.width = width * devicePixelRatio;
        canvas.height = height * devicePixelRatio;
        const ctx = canvas.getContext("2d");
        if (ctx) ctx.scale(devicePixelRatio, devicePixelRatio);
        scheduleFrame();
      }
    });
    ro.observe(canvas);
    return () => ro.disconnect();
  }, [scheduleFrame]);

  // ── Coordinate conversion ─────────────────────────────────────────────────
  const toGraphCoords = useCallback((clientX: number, clientY: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const { tx, ty, scale } = transformRef.current;
    return {
      x: (clientX - rect.left - tx) / scale,
      y: (clientY - rect.top - ty) / scale,
    };
  }, []);

  const hitTest = useCallback((gx: number, gy: number): SimNode | null => {
    for (const node of simNodesRef.current) {
      const dx = gx - node.x;
      const dy = gy - node.y;
      if (dx * dx + dy * dy <= (NODE_R + 4) * (NODE_R + 4)) return node;
    }
    return null;
  }, []);

  const linkHitTest = useCallback((gx: number, gy: number): string | null => {
    for (const link of simLinksRef.current) {
      const s = link.source as SimNode;
      const t = link.target as SimNode;
      if (!s?.x || !t?.x) continue;
      // Point-to-segment distance
      const dx = t.x - s.x;
      const dy = t.y - s.y;
      const lenSq = dx * dx + dy * dy;
      if (lenSq === 0) continue;
      const u = Math.max(0, Math.min(1, ((gx - s.x) * dx + (gy - s.y) * dy) / lenSq));
      const px = s.x + u * dx - gx;
      const py = s.y + u * dy - gy;
      if (px * px + py * py < 36) {
        return `${s.id}-${t.id}-${link.relation_type}`;
      }
    }
    return null;
  }, []);

  // ── Mouse events ───────────────────────────────────────────────────────────
  const handleMouseDown = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      mouseDownClientRef.current = { x: e.clientX, y: e.clientY };
      const { x, y } = toGraphCoords(e.clientX, e.clientY);
      const hit = hitTest(x, y);
      if (hit) {
        dragNodeRef.current = hit;
        // Fix node during drag so d3 doesn't move it
        hit.fx = hit.x;
        hit.fy = hit.y;
      } else {
        const { tx, ty } = transformRef.current;
        panRef.current = { startX: e.clientX, startY: e.clientY, startTx: tx, startTy: ty };
      }
    },
    [toGraphCoords, hitTest]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (dragNodeRef.current) {
        const { x, y } = toGraphCoords(e.clientX, e.clientY);
        dragNodeRef.current.fx = x;
        dragNodeRef.current.fy = y;
        dragNodeRef.current.x = x;
        dragNodeRef.current.y = y;
        // Reheat slightly so linked nodes respond
        simRef.current?.alphaTarget(0.1).restart();
        scheduleFrame();
        return;
      }

      if (panRef.current) {
        const dx = e.clientX - panRef.current.startX;
        const dy = e.clientY - panRef.current.startY;
        const newT = {
          ...transformRef.current,
          tx: panRef.current.startTx + dx,
          ty: panRef.current.startTy + dy,
        };
        transformRef.current = newT;
        setTransform(newT);
        scheduleFrame();
        return;
      }

      // Hover detection
      const { x, y } = toGraphCoords(e.clientX, e.clientY);
      const hitNode = hitTest(x, y);
      const newNodeHover = hitNode?.id ?? null;
      const newLinkHover = hitNode ? null : linkHitTest(x, y);

      if (newNodeHover !== hoveredNodeRef.current || newLinkHover !== hoveredLinkRef.current) {
        hoveredNodeRef.current = newNodeHover;
        hoveredLinkRef.current = newLinkHover;
        canvasRef.current!.style.cursor = hitNode ? "pointer" : "grab";
        scheduleFrame();
      }
    },
    [toGraphCoords, hitTest, linkHitTest, scheduleFrame]
  );

  const handleMouseUp = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const dragged = dragNodeRef.current;
      const downPos = mouseDownClientRef.current;
      mouseDownClientRef.current = null;

      if (dragged) {
        // Distinguish click from drag: if mouse barely moved, treat as click
        const moved = downPos ? Math.hypot(e.clientX - downPos.x, e.clientY - downPos.y) > 4 : true;

        dragged.fx = undefined;
        dragged.fy = undefined;
        simRef.current?.alphaTarget(0).restart();
        dragNodeRef.current = null;

        if (!moved) onNodeClick(dragged);
      } else if (panRef.current) {
        panRef.current = null;
      }
    },
    [onNodeClick]
  );

  const handleMouseLeave = useCallback(() => {
    dragNodeRef.current = null;
    panRef.current = null;
    hoveredNodeRef.current = null;
    hoveredLinkRef.current = null;
    if (canvasRef.current) canvasRef.current.style.cursor = "grab";
    scheduleFrame();
  }, [scheduleFrame]);

  // ── Scroll zoom ───────────────────────────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const handler = (e: WheelEvent) => {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const cursorX = e.clientX - rect.left;
      const cursorY = e.clientY - rect.top;
      const t = transformRef.current;
      const delta = e.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP;
      const newScale = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, t.scale + delta * t.scale));
      const ratio = newScale / t.scale;
      const newT = {
        scale: newScale,
        tx: cursorX - ratio * (cursorX - t.tx),
        ty: cursorY - ratio * (cursorY - t.ty),
      };
      transformRef.current = newT;
      setTransform(newT);
      setScaleDisplay(newScale);
      scheduleFrame();
    };
    canvas.addEventListener("wheel", handler, { passive: false });
    return () => canvas.removeEventListener("wheel", handler);
  }, [scheduleFrame]);

  // ── Zoom buttons ──────────────────────────────────────────────────────────
  const applyZoom = useCallback(
    (factor: number) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const { width, height } = canvas.getBoundingClientRect();
      const cx = width / 2;
      const cy = height / 2;
      const t = transformRef.current;
      const newScale = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, t.scale * factor));
      const ratio = newScale / t.scale;
      const newT = {
        scale: newScale,
        tx: cx - ratio * (cx - t.tx),
        ty: cy - ratio * (cy - t.ty),
      };
      transformRef.current = newT;
      setTransform(newT);
      setScaleDisplay(newScale);
      scheduleFrame();
    },
    [scheduleFrame]
  );

  const resetView = useCallback(() => {
    const newT = { tx: 0, ty: 0, scale: 1 };
    transformRef.current = newT;
    setTransform(newT);
    setScaleDisplay(1);
    scheduleFrame();
  }, [scheduleFrame]);

  return (
    <div className={cn("relative rounded-xl", className)}>
      <canvas
        ref={canvasRef}
        className="h-full w-full cursor-grab select-none rounded-xl border border-border bg-card"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
      />

      {/* Empty state */}
      {nodes.length === 0 && (
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-3 text-center">
          <div className="text-3xl opacity-30">◎</div>
          <p className="text-sm text-muted-foreground">No entities in the knowledge graph yet.</p>
          <p className="text-xs text-muted-foreground">
            Index some documents to populate the graph.
          </p>
        </div>
      )}

      {/* Zoom controls */}
      {hasNodes && (
        <div className="absolute bottom-3 right-3 flex flex-col gap-1">
          <button
            onClick={() => applyZoom(1 + ZOOM_STEP)}
            title="Zoom in"
            className="flex h-7 w-7 items-center justify-center rounded-md border border-border bg-card text-sm font-semibold text-muted-foreground shadow-sm transition-colors hover:bg-accent hover:text-foreground"
          >
            +
          </button>
          <button
            onClick={() => applyZoom(1 - ZOOM_STEP)}
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
      {hasNodes && transform.scale !== 1 && (
        <div className="absolute bottom-3 left-3 rounded-md border border-border bg-card/80 px-2 py-0.5 text-xs text-muted-foreground">
          {Math.round(scaleDisplay * 100)}%
        </div>
      )}
    </div>
  );
}
