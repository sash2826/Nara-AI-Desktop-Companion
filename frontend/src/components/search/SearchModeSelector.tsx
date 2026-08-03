import { Brain, Type } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SearchMode } from "@/store/searchStore";

interface SearchModeSelectorProps {
  mode: SearchMode;
  onChange: (mode: SearchMode) => void;
  className?: string;
}

const MODES: { id: SearchMode; label: string; icon: typeof Brain; description: string }[] = [
  {
    id: "semantic",
    label: "Semantic",
    icon: Brain,
    description: "Find conceptually related content",
  },
  {
    id: "keyword",
    label: "Keyword",
    icon: Type,
    description: "Match exact words and phrases",
  },
];

export function SearchModeSelector({ mode, onChange, className }: SearchModeSelectorProps) {
  return (
    <div
      className={cn("flex items-center gap-1 rounded-lg bg-muted p-1", className)}
      role="tablist"
      aria-label="Search mode"
    >
      {MODES.map(({ id, label, icon: Icon, description }) => (
        <button
          key={id}
          type="button"
          role="tab"
          aria-selected={mode === id}
          aria-label={`${label}: ${description}`}
          onClick={() => onChange(id)}
          className={cn(
            "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
            mode === id
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Icon size={13} strokeWidth={1.75} />
          {label}
        </button>
      ))}
    </div>
  );
}
