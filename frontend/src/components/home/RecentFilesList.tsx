import { FileText, FolderOpen, Loader2 } from "lucide-react";
import { useState } from "react";
import { IPCClient } from "@/services/ipc/IPCClient";
import type { RecentFile } from "@/services/ipc/IPCClient";
import { cn } from "@/lib/utils";
import { FileTypeIcon } from "@/components/common/FileTypeIcon";

interface RecentFilesListProps {
  files: RecentFile[];
}

function fileName(path: string): string {
  return path.split(/[\\/]/).pop() ?? path;
}

function formatDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, { dateStyle: "short", timeStyle: "short" }).format(
      new Date(iso)
    );
  } catch {
    return iso;
  }
}

function OpenButton({ path }: { path: string }) {
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);

  const handleOpen = async () => {
    if (loading) return;
    setLoading(true);
    setFailed(false);
    try {
      await IPCClient.openFile(path);
    } catch {
      setFailed(true);
      setTimeout(() => setFailed(false), 2000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={() => void handleOpen()}
      title={path}
      aria-label={`Open ${fileName(path)}`}
      className={cn(
        "flex-shrink-0 rounded p-1 transition-colors",
        failed
          ? "text-destructive"
          : "text-muted-foreground opacity-0 group-hover:opacity-100 hover:text-foreground"
      )}
    >
      {loading ? <Loader2 size={13} className="animate-spin" /> : <FolderOpen size={13} />}
    </button>
  );
}

export function RecentFilesList({ files }: RecentFilesListProps) {
  if (!files.length) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-border py-8 text-center">
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <FileText size={18} strokeWidth={1.5} aria-hidden="true" />
        </span>
        <p className="text-xs text-muted-foreground">No files indexed yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {files.map((file) => (
        <div
          key={file.id}
          className="group flex items-center gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-accent/50"
        >
          <span className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-muted">
            <FileTypeIcon path={file.file_path} size={21} />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm text-foreground" title={file.file_path}>
              {fileName(file.file_path)}
            </p>
            <p className="text-xs text-muted-foreground">
              {file.chunk_count} chunks · {formatDate(file.indexed_at)}
            </p>
          </div>
          <OpenButton path={file.file_path} />
        </div>
      ))}
    </div>
  );
}
