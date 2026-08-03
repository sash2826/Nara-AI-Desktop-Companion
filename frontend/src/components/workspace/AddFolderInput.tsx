import { useState, useRef } from "react";
import { FolderPlus, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface AddFolderInputProps {
  onAdd: (path: string) => Promise<unknown>;
  className?: string;
}

export function AddFolderInput({ onAdd, className }: AddFolderInputProps) {
  const [path, setPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = path.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    try {
      await onAdd(trimmed);
      setPath("");
      inputRef.current?.focus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add folder");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={cn("space-y-1.5", className)}>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          ref={inputRef}
          type="text"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="Paste or type a folder path…"
          className={cn(
            "h-8 min-w-0 flex-1 rounded-md border border-border bg-background px-3 text-sm",
            "text-foreground placeholder:text-muted-foreground",
            "focus:outline-none focus:ring-1 focus:ring-ring",
            error && "border-destructive"
          )}
          disabled={loading}
          aria-label="Folder path"
        />
        <button
          type="submit"
          disabled={loading || !path.trim()}
          className={cn(
            "inline-flex h-8 flex-shrink-0 items-center gap-1.5 rounded-md px-3 text-xs font-medium",
            "bg-primary text-primary-foreground transition-colors hover:bg-primary/90",
            "disabled:pointer-events-none disabled:opacity-50"
          )}
        >
          {loading ? (
            <Loader2 size={13} className="animate-spin" />
          ) : (
            <FolderPlus size={13} strokeWidth={1.5} />
          )}
          Add
        </button>
      </form>
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
