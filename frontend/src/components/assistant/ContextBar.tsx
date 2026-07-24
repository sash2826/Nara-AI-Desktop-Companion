import { FileText, Brain, LayoutDashboard, Hash } from "lucide-react";
import { cn } from "@/lib/utils";

interface ContextBarProps {
  className?: string;
}

interface ContextItem {
  id: string;
  icon: typeof FileText;
  label: string;
  value: string;
}

const CONTEXT_ITEMS: ContextItem[] = [
  { id: "context", icon: FileText, label: "Context", value: "None" },
  { id: "memory", icon: Brain, label: "Memory", value: "Off" },
  { id: "workspace", icon: LayoutDashboard, label: "Workspace", value: "None" },
  { id: "tokens", icon: Hash, label: "Tokens", value: "0 / 128k" },
];

export function ContextBar({ className }: ContextBarProps) {
  return (
    <div
      className={cn("flex items-center gap-4 border-t border-border px-4 py-2", className)}
      aria-label="Conversation context"
    >
      {CONTEXT_ITEMS.map(({ id, icon: Icon, label, value }) => (
        <button
          key={id}
          aria-label={`${label}: ${value}`}
          title={`${label}: ${value}`}
          className={cn(
            "flex items-center gap-1 rounded-md px-1.5 py-0.5",
            "text-2xs text-muted-foreground/60 transition-colors duration-fast",
            "hover:bg-muted hover:text-muted-foreground"
          )}
        >
          <Icon size={11} strokeWidth={1.8} aria-hidden="true" />
          <span>{value}</span>
        </button>
      ))}
    </div>
  );
}
