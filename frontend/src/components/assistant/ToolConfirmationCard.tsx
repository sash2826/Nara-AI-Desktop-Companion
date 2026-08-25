import { FolderPlus, FolderMinus } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { PendingToolAction } from "@/services/conversation/ConversationService";

interface ToolConfirmationCardProps {
  action: PendingToolAction;
  onConfirm: () => void;
  onCancel: () => void;
  className?: string;
}

export function ToolConfirmationCard({
  action,
  onConfirm,
  onCancel,
  className,
}: ToolConfirmationCardProps) {
  const isAdd = action.type === "add_folder";
  const Icon = isAdd ? FolderPlus : FolderMinus;
  const title = isAdd ? "Add folder to index?" : "Remove folder from index?";
  const actionLabel = isAdd ? "Add folder" : "Remove folder";
  const actionClass = isAdd
    ? "bg-primary text-primary-foreground hover:bg-primary/90"
    : "bg-destructive text-destructive-foreground hover:bg-destructive/90";

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 4 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={cn("mx-2 mb-3 rounded-xl border border-border bg-card p-4 shadow-sm", className)}
      role="dialog"
      aria-label={title}
    >
      {/* Header */}
      <div className="mb-3 flex items-center gap-2.5">
        <span className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-muted">
          <Icon size={14} strokeWidth={1.8} className="text-foreground" aria-hidden="true" />
        </span>
        <span className="text-sm font-medium text-foreground">{title}</span>
      </div>

      {/* Path */}
      <p className="mb-1.5 break-all rounded-md bg-muted px-3 py-2 font-mono text-xs text-foreground">
        {action.path}
      </p>

      {/* Reason */}
      {action.reason && <p className="mb-4 text-xs text-muted-foreground">{action.reason}</p>}

      {/* Actions */}
      <div className="flex items-center justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className={cn(
            "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
            "border border-border bg-transparent text-muted-foreground",
            "hover:bg-muted hover:text-foreground"
          )}
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={onConfirm}
          className={cn(
            "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
            actionClass
          )}
        >
          {actionLabel}
        </button>
      </div>
    </motion.div>
  );
}
