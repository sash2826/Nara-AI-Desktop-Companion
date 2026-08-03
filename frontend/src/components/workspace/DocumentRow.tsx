import { FileText, FileType, File } from "lucide-react";
import { cn } from "@/lib/utils";
import type { IndexedDocument } from "@/types/workspace";

const EXT_ICONS: Record<string, React.ElementType> = {
  ".pdf": FileType,
  ".docx": FileText,
  ".md": FileText,
  ".txt": File,
};

function getExtension(filePath: string): string {
  const dot = filePath.lastIndexOf(".");
  return dot >= 0 ? filePath.slice(dot).toLowerCase() : "";
}

function getFileName(filePath: string): string {
  return filePath.replace(/\\/g, "/").split("/").pop() ?? filePath;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatSize(chars: number): string {
  if (chars >= 1_000_000) return `${(chars / 1_000_000).toFixed(1)}M chars`;
  if (chars >= 1_000) return `${(chars / 1_000).toFixed(0)}k chars`;
  return `${chars} chars`;
}

interface DocumentRowProps {
  document: IndexedDocument;
  className?: string;
}

export function DocumentRow({ document, className }: DocumentRowProps) {
  const ext = getExtension(document.file_path);
  const Icon = EXT_ICONS[ext] ?? File;
  const fileName = getFileName(document.file_path);

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg border border-border bg-card px-3 py-2.5",
        "transition-colors hover:bg-accent/50",
        className
      )}
    >
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-muted">
        <Icon size={15} className="text-muted-foreground" strokeWidth={1.5} />
      </div>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-foreground" title={document.file_path}>
          {fileName}
        </p>
        <p className="truncate text-xs text-muted-foreground" title={document.file_path}>
          {document.file_path}
        </p>
      </div>

      <div className="flex flex-shrink-0 flex-col items-end gap-0.5">
        <span className="text-xs text-muted-foreground">
          {document.chunk_count} chunk{document.chunk_count !== 1 ? "s" : ""}
        </span>
        <span className="text-2xs text-muted-foreground">
          {formatSize(document.char_count)} · {formatDate(document.indexed_at)}
        </span>
      </div>
    </div>
  );
}
