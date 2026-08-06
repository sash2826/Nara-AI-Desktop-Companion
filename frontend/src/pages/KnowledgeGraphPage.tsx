import { AlertTriangle } from "lucide-react";
import { useGraph } from "@/hooks/useGraph";
import { GraphCanvas } from "@/components/graph/GraphCanvas";
import { GraphControls } from "@/components/graph/GraphControls";
import { EntityCard } from "@/components/graph/EntityCard";
import type { GraphVisNode } from "@/services/ipc/IPCClient";

export function KnowledgeGraphPage() {
  const {
    nodes,
    edges,
    isLoading,
    error,
    focalEntity,
    depth,
    selectedNode,
    setFocalEntity,
    setDepth,
    setSelectedNode,
    refresh,
  } = useGraph();

  const handleNodeClick = (node: GraphVisNode) => {
    setSelectedNode(selectedNode?.id === node.id ? null : node);
  };

  const handleFocusFromCard = (name: string) => {
    setFocalEntity(name);
    setSelectedNode(null);
  };

  return (
    <div className="flex h-full flex-col gap-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-lg font-semibold text-foreground">Knowledge Graph</h1>
          <p className="text-sm text-muted-foreground">
            Entity relationships discovered across your indexed documents.
          </p>
        </div>
      </div>

      {/* Controls */}
      <GraphControls
        focalEntity={focalEntity}
        depth={depth}
        isLoading={isLoading}
        nodeCount={nodes.length}
        edgeCount={edges.length}
        onEntitySearch={setFocalEntity}
        onDepthChange={setDepth}
        onRefresh={refresh}
      />

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">
          <AlertTriangle size={14} className="flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Main canvas + side panel */}
      <div className="relative flex min-h-0 flex-1 gap-4">
        {/* Loading overlay on canvas */}
        <div className="relative flex-1">
          <GraphCanvas
            nodes={nodes}
            edges={edges}
            selectedNodeId={selectedNode?.id ?? null}
            onNodeClick={handleNodeClick}
            className="h-full"
          />
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-background/60">
              <div className="flex flex-col items-center gap-2">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                <p className="text-xs text-muted-foreground">Building graph…</p>
              </div>
            </div>
          )}
        </div>

        {/* Entity detail panel */}
        {selectedNode && (
          <EntityCard
            node={selectedNode}
            edges={edges}
            onClose={() => setSelectedNode(null)}
            onFocus={handleFocusFromCard}
            className="w-64 flex-shrink-0"
          />
        )}
      </div>
    </div>
  );
}
