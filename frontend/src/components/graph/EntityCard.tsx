import { X } from "lucide-react";
import type { GraphVisNode, GraphVisEdge } from "@/services/ipc/IPCClient";
import { IPCClient } from "@/services/ipc/IPCClient";
import { Button } from "@/components/ui/button";
import { FileTypeIcon } from "@/components/common/FileTypeIcon";
import { cn } from "@/lib/utils";

interface EntityCardProps {
  node: GraphVisNode;
  edges: GraphVisEdge[];
  onClose: () => void;
  onFocus: (name: string) => void;
  className?: string;
}

function confidenceLabel(c: number): string {
  if (c >= 0.8) return "High";
  if (c >= 0.5) return "Medium";
  return "Low";
}

function confidenceColor(c: number): string {
  if (c >= 0.8) return "text-emerald-500";
  if (c >= 0.5) return "text-amber-500";
  return "text-muted-foreground";
}

export function EntityCard({ node, edges, onClose, onFocus, className }: EntityCardProps) {
  const outgoing = edges.filter((e) => e.source === node.id);
  const incoming = edges.filter((e) => e.target === node.id);

  const handleOpenDocument = async (filePath: string) => {
    try {
      await IPCClient.openFile(filePath);
    } catch {
      // No-op — file open is best-effort
    }
  };

  return (
    <div
      className={cn(
        "flex flex-col gap-4 rounded-xl border border-border bg-card p-4 shadow-lg",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-foreground">{node.label}</p>
          <p className="text-xs text-muted-foreground">{node.entity_type}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="flex-shrink-0 rounded p-0.5 text-muted-foreground hover:text-foreground"
          aria-label="Close entity panel"
        >
          <X size={14} />
        </button>
      </div>

      {/* Confidence */}
      <div className="flex items-center justify-between rounded-lg bg-muted/40 px-3 py-2">
        <span className="text-xs text-muted-foreground">Confidence</span>
        <span className={cn("text-xs font-medium", confidenceColor(node.confidence))}>
          {confidenceLabel(node.confidence)} ({Math.round(node.confidence * 100)}%)
        </span>
      </div>

      {/* Relationships */}
      {(outgoing.length > 0 || incoming.length > 0) && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Relationships
          </p>
          <div className="space-y-1">
            {outgoing.map((e) => (
              <div
                key={`out-${e.target}-${e.relation_type}`}
                className="flex items-center gap-1.5 text-xs"
              >
                <span className="text-muted-foreground">→</span>
                <span className="rounded bg-muted px-1 py-0.5 font-mono text-[10px] text-muted-foreground">
                  {e.relation_type}
                </span>
                <button
                  type="button"
                  onClick={() => onFocus(e.target_name)}
                  className="truncate text-foreground hover:underline"
                >
                  {e.target_name}
                </button>
              </div>
            ))}
            {incoming.map((e) => (
              <div
                key={`in-${e.source}-${e.relation_type}`}
                className="flex items-center gap-1.5 text-xs"
              >
                <span className="text-muted-foreground">←</span>
                <span className="rounded bg-muted px-1 py-0.5 font-mono text-[10px] text-muted-foreground">
                  {e.relation_type}
                </span>
                <button
                  type="button"
                  onClick={() => onFocus(e.source_name)}
                  className="truncate text-foreground hover:underline"
                >
                  {e.source_name}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-col gap-1.5">
        {node.source_document_path && (
          <Button
            variant="secondary"
            size="sm"
            className="h-7 justify-start gap-1.5 text-xs"
            onClick={() => void handleOpenDocument(node.source_document_path!)}
          >
            <FileTypeIcon path={node.source_document_path} size={14} />
            Open source document
          </Button>
        )}
        <Button
          variant="ghost"
          size="sm"
          className="h-7 justify-start gap-1.5 text-xs text-muted-foreground"
          onClick={() => onFocus(node.label)}
        >
          Focus graph on this entity
        </Button>
      </div>
    </div>
  );
}
