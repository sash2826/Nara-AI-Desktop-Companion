import { FolderPlus, Loader2, X, Check, FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ClusterProposal } from "@/services/ipc/IPCClient";

interface ClusterProposalCardProps {
  proposal: ClusterProposal;
  isAccepting: boolean;
  isDismissing: boolean;
  error: string | undefined;
  onAccept: (proposal: ClusterProposal) => void;
  onChooseFolder: (proposal: ClusterProposal) => void;
  onDismiss: (proposalId: string) => void;
}

export function ClusterProposalCard({
  proposal,
  isAccepting,
  isDismissing,
  error,
  onAccept,
  onChooseFolder,
  onDismiss,
}: ClusterProposalCardProps) {
  const busy = isAccepting || isDismissing;

  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-card p-3 transition-opacity",
        busy && "opacity-70"
      )}
    >
      <div className="flex items-start gap-2.5">
        <span className="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
          <FolderPlus size={15} strokeWidth={1.5} />
        </span>

        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-foreground leading-tight">
            {proposal.proposed_folder_name}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {proposal.file_paths.length} file{proposal.file_paths.length !== 1 ? "s" : ""} could be
            grouped here
          </p>

          <ul className="mt-1.5 space-y-0.5">
            {proposal.file_paths.slice(0, 5).map((fp) => (
              <li key={fp} className="truncate text-2xs text-muted-foreground" title={fp}>
                {fp.split(/[\\/]/).pop()}
              </li>
            ))}
            {proposal.file_paths.length > 5 && (
              <li className="text-2xs text-muted-foreground">
                +{proposal.file_paths.length - 5} more
              </li>
            )}
          </ul>

          {error && <p className="mt-1.5 text-2xs text-destructive">{error}</p>}

          <div className="mt-2.5 flex items-center gap-2">
            <button
              onClick={() => onAccept(proposal)}
              disabled={busy}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-semibold transition-colors",
                busy
                  ? "bg-primary/20 text-primary cursor-not-allowed"
                  : "bg-primary text-primary-foreground hover:bg-primary/90"
              )}
            >
              {isAccepting ? (
                <Loader2 size={11} className="animate-spin" />
              ) : (
                <Check size={11} strokeWidth={2.5} />
              )}
              Create folder
            </button>

            <button
              onClick={() => onChooseFolder(proposal)}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-accent/50 hover:text-foreground disabled:opacity-50"
            >
              <FolderOpen size={11} strokeWidth={1.5} />
              Choose folder
            </button>

            <button
              onClick={() => onDismiss(proposal.id)}
              disabled={busy}
              title="Dismiss suggestion"
              aria-label="Dismiss"
              className="ml-auto inline-flex items-center justify-center rounded-md p-1 text-muted-foreground transition-colors hover:bg-accent/50 hover:text-foreground disabled:opacity-50"
            >
              {isDismissing ? (
                <Loader2 size={13} className="animate-spin" />
              ) : (
                <X size={13} strokeWidth={1.5} />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
