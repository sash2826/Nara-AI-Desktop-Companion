import { Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface QuickActionsProps {
  onSelect: (prompt: string) => void;
  disabled?: boolean;
  suggestions?: string[];
  className?: string;
}

export function QuickActions({
  onSelect,
  disabled = false,
  suggestions,
  className,
}: QuickActionsProps) {
  if (!suggestions || suggestions.length === 0) return null;

  const topSuggestions = suggestions.slice(0, 3);

  return (
    <div className={cn("flex flex-col gap-2 px-4 py-2", className)}>
      {/* Heading */}
      <div className="flex items-center gap-1.5">
        <Sparkles size={12} className="text-muted-foreground" strokeWidth={1.75} />
        <span className="text-xs font-medium text-muted-foreground">Suggested searches</span>
      </div>

      {/* Suggestion chips */}
      <div role="group" aria-label="Suggested questions" className="flex flex-wrap gap-1.5">
        {topSuggestions.map((suggestion, i) => (
          <motion.button
            key={suggestion}
            type="button"
            onClick={(e) => {
              onSelect(suggestion);
              e.currentTarget.blur();
            }}
            disabled={disabled}
            aria-label={`Suggested: ${suggestion}`}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.15, delay: i * 0.04 }}
            whileHover={!disabled ? { scale: 1.02 } : {}}
            whileTap={!disabled ? { scale: 0.97 } : {}}
            className={cn(
              "rounded-full border border-border bg-[hsl(var(--color-neutral-0))] shadow-elevation-1 px-3 py-1.5 text-xs font-medium text-card-foreground",
              "transition-colors duration-fast dark:bg-card dark:shadow-none",
              disabled
                ? "cursor-not-allowed opacity-50"
                : "hover:border-primary/40 hover:bg-accent hover:text-accent-foreground"
            )}
          >
            {suggestion}
          </motion.button>
        ))}
      </div>
    </div>
  );
}
