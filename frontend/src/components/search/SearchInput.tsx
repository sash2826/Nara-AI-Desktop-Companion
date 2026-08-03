import { useRef, type KeyboardEvent } from "react";
import { Search, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SearchInputProps {
  value: string;
  isSearching: boolean;
  onChange: (value: string) => void;
  onSearch: () => void;
  onClear: () => void;
  className?: string;
}

export function SearchInput({
  value,
  isSearching,
  onChange,
  onSearch,
  onClear,
  className,
}: SearchInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !isSearching) onSearch();
    if (e.key === "Escape") {
      onClear();
      inputRef.current?.blur();
    }
  };

  return (
    <div
      className={cn(
        "relative flex items-center rounded-lg border border-input bg-background shadow-sm transition-colors focus-within:border-ring focus-within:ring-1 focus-within:ring-ring",
        className
      )}
    >
      <span className="pointer-events-none pl-3 pr-2">
        {isSearching ? (
          <Loader2 size={16} className="animate-spin text-muted-foreground" />
        ) : (
          <Search size={16} className="text-muted-foreground" />
        )}
      </span>

      <input
        ref={inputRef}
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Search your documents…"
        aria-label="Search query"
        className="flex-1 bg-transparent py-2.5 pr-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
      />

      {value && (
        <button
          type="button"
          onClick={onClear}
          aria-label="Clear search"
          className="pr-3 text-muted-foreground transition-colors hover:text-foreground"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}
