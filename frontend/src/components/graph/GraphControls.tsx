import { useState, type FormEvent } from "react";
import { Search, RefreshCw, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface GraphControlsProps {
  focalEntity: string | null;
  depth: number;
  isLoading: boolean;
  nodeCount: number;
  edgeCount: number;
  onEntitySearch: (name: string | null) => void;
  onDepthChange: (depth: number) => void;
  onRefresh: () => void;
}

export function GraphControls({
  focalEntity,
  depth,
  isLoading,
  nodeCount,
  edgeCount,
  onEntitySearch,
  onDepthChange,
  onRefresh,
}: GraphControlsProps) {
  const [inputValue, setInputValue] = useState(focalEntity ?? "");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onEntitySearch(inputValue.trim() || null);
  };

  const handleClear = () => {
    setInputValue("");
    onEntitySearch(null);
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Entity search */}
      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <div className="relative">
          <Search
            size={13}
            className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
          />
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Focus on entity…"
            className="h-8 w-52 rounded-lg border border-border bg-background pl-8 pr-8 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
          {inputValue && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label="Clear entity filter"
            >
              <X size={12} />
            </button>
          )}
        </div>
        <Button type="submit" size="sm" variant="secondary" className="h-8 px-3 text-xs">
          Go
        </Button>
      </form>

      {/* Depth slider */}
      <div className="flex items-center gap-2">
        <label className="text-xs text-muted-foreground" htmlFor="depth-slider">
          Depth
        </label>
        <input
          id="depth-slider"
          type="range"
          min={1}
          max={3}
          step={1}
          value={depth}
          onChange={(e) => onDepthChange(Number(e.target.value))}
          className="h-1 w-20 accent-primary"
        />
        <span className="w-3 text-center text-xs font-medium tabular-nums text-foreground">
          {depth}
        </span>
      </div>

      {/* Refresh */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onRefresh}
        disabled={isLoading}
        className="h-8 gap-1.5 px-2 text-xs text-muted-foreground"
        aria-label="Refresh graph"
      >
        <RefreshCw size={12} className={isLoading ? "animate-spin" : ""} />
        Refresh
      </Button>

      {/* Stats */}
      {!isLoading && (nodeCount > 0 || edgeCount > 0) && (
        <span className="ml-auto text-xs text-muted-foreground">
          {nodeCount} nodes · {edgeCount} edges
        </span>
      )}
    </div>
  );
}
