import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { IPCClient, type GraphVisualization, type GraphVisNode } from "@/services/ipc/IPCClient";

interface GraphState {
  data: GraphVisualization;
  isLoading: boolean;
  error: string | null;
  focalEntity: string | null;
  depth: number;
  selectedNode: GraphVisNode | null;
}

const EMPTY_GRAPH: GraphVisualization = { nodes: [], edges: [] };

export function useGraph() {
  const [state, setState] = useState<GraphState>({
    data: EMPTY_GRAPH,
    isLoading: true,
    error: null,
    focalEntity: null,
    depth: 1,
    selectedNode: null,
  });

  // Serial request counter — only the response matching the latest request is applied.
  const requestSeqRef = useRef(0);
  const depthDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async (entityName: string | null, depth: number) => {
    const seq = ++requestSeqRef.current;
    setState((s) => ({ ...s, isLoading: true, error: null }));
    try {
      const data = await IPCClient.getGraphVisualization(entityName ?? undefined, depth);
      // Discard stale responses that arrived after a newer request was fired.
      if (seq !== requestSeqRef.current) return;
      setState((s) => ({ ...s, data, isLoading: false }));
    } catch (err) {
      if (seq !== requestSeqRef.current) return;
      setState((s) => ({
        ...s,
        data: EMPTY_GRAPH,
        isLoading: false,
        error: err instanceof Error ? err.message : "Failed to load graph.",
      }));
    }
  }, []);

  // Initial load on mount
  useEffect(() => {
    load(null, 1);
  }, [load]);

  const setFocalEntity = useCallback(
    (name: string | null) => {
      setState((s) => ({ ...s, focalEntity: name, selectedNode: null }));
      load(name, state.depth);
    },
    [load, state.depth]
  );

  const setDepth = useCallback(
    (depth: number) => {
      setState((s) => ({ ...s, depth }));
      // Debounce: cancel pending depth-change request and wait 300 ms
      // before firing, so rapid slider moves don't stack concurrent requests.
      if (depthDebounceRef.current !== null) {
        clearTimeout(depthDebounceRef.current);
      }
      depthDebounceRef.current = setTimeout(() => {
        depthDebounceRef.current = null;
        load(state.focalEntity, depth);
      }, 300);
    },
    [load, state.focalEntity]
  );

  const setSelectedNode = useCallback((node: GraphVisNode | null) => {
    setState((s) => ({ ...s, selectedNode: node }));
  }, []);

  const refresh = useCallback(() => {
    load(state.focalEntity, state.depth);
  }, [load, state.focalEntity, state.depth]);

  // Stable references — only change when load() delivers new data, not on every
  // selectedNode / isLoading state update.  This prevents GraphCanvas from
  // restarting the force simulation on every click or loading-flag toggle.
  const nodes = useMemo(() => state.data.nodes, [state.data]);
  const edges = useMemo(() => state.data.edges, [state.data]);

  return {
    nodes,
    edges,
    isLoading: state.isLoading,
    error: state.error,
    focalEntity: state.focalEntity,
    depth: state.depth,
    selectedNode: state.selectedNode,
    setFocalEntity,
    setDepth,
    setSelectedNode,
    refresh,
  };
}
