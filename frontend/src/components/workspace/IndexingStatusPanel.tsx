import { useCallback, useRef, useState } from "react";
import {
  Loader2,
  Play,
  CheckCircle,
  AlertCircle,
  Activity,
  Square,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useWorkspace } from "@/hooks/useWorkspace";
import { IPCClient } from "@/services/ipc/IPCClient";
import type { IndexingStatus } from "@/services/ipc/IPCClient";

interface IndexingTaskState {
  taskId: string;
  workspacePath: string;
  status: IndexingStatus | null;
  polling: boolean;
}

export function IndexingStatusPanel() {
  const { folders } = useWorkspace();
  const [tasks, setTasks] = useState<IndexingTaskState[]>([]);
  const [customPath, setCustomPath] = useState("");

  // Interval handles stored in a ref so we can cancel them imperatively
  // without causing re-renders or stale closures.
  const intervalMapRef = useRef<Map<string, ReturnType<typeof setInterval>>>(new Map());

  const clearTaskInterval = useCallback((taskId: string) => {
    const handle = intervalMapRef.current.get(taskId);
    if (handle !== undefined) {
      clearInterval(handle);
      intervalMapRef.current.delete(taskId);
    }
  }, []);

  const pollTask = useCallback(
    (taskId: string) => {
      const handle = setInterval(async () => {
        try {
          const status = await IPCClient.getIndexingStatus(taskId);
          const isDone =
            status.status !== "running" &&
            status.status !== "queued" &&
            status.status !== "cancelled";
          const isCancelled = status.status === "cancelled";

          setTasks((prev) =>
            prev.map((t) =>
              t.taskId === taskId ? { ...t, status, polling: !isDone && !isCancelled } : t
            )
          );

          if (isDone || isCancelled) {
            clearTaskInterval(taskId);
          }
        } catch {
          clearTaskInterval(taskId);
          setTasks((prev) => prev.map((t) => (t.taskId === taskId ? { ...t, polling: false } : t)));
        }
      }, 2000);

      intervalMapRef.current.set(taskId, handle);
    },
    [clearTaskInterval]
  );

  const startIndex = async (workspacePath: string) => {
    try {
      const response = await IPCClient.indexWorkspace(workspacePath);
      const task: IndexingTaskState = {
        taskId: response.task_id,
        workspacePath,
        status: null,
        polling: true,
      };
      setTasks((prev) => [task, ...prev.slice(0, 9)]);
      pollTask(response.task_id);
    } catch (err) {
      console.error("Failed to start indexing:", err);
    }
  };

  const stopTask = async (taskId: string) => {
    try {
      await IPCClient.cancelIndexing(taskId);
    } catch {
      // Server-side cancel may still fail gracefully; stop polling regardless.
    }
    clearTaskInterval(taskId);
    setTasks((prev) =>
      prev.map((t) =>
        t.taskId === taskId
          ? { ...t, polling: false, status: t.status ? { ...t.status, status: "cancelled" } : null }
          : t
      )
    );
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-foreground">Indexing</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Manually trigger indexing on any folder.
        </p>
      </div>

      {/* Quick index watched folders */}
      {folders.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground">Watched folders</p>
          {folders.map((folder) => (
            <div
              key={folder.id}
              className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2"
            >
              <p className="min-w-0 flex-1 truncate text-xs text-foreground" title={folder.path}>
                {folder.path}
              </p>
              <button
                onClick={() => startIndex(folder.path)}
                className={cn(
                  "inline-flex flex-shrink-0 items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium",
                  "bg-muted text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                )}
              >
                <Play size={11} strokeWidth={1.5} />
                Index
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Custom path */}
      <div className="space-y-1.5">
        <p className="text-xs font-medium text-muted-foreground">Custom path</p>
        <div className="flex gap-2">
          <input
            type="text"
            value={customPath}
            onChange={(e) => setCustomPath(e.target.value)}
            placeholder="Enter folder path…"
            className={cn(
              "h-8 min-w-0 flex-1 rounded-md border border-border bg-background px-3 text-sm",
              "text-foreground placeholder:text-muted-foreground",
              "focus:outline-none focus:ring-1 focus:ring-ring"
            )}
          />
          <button
            onClick={() => {
              if (customPath.trim()) {
                void startIndex(customPath.trim());
                setCustomPath("");
              }
            }}
            disabled={!customPath.trim()}
            className={cn(
              "inline-flex h-8 flex-shrink-0 items-center gap-1.5 rounded-md px-3 text-xs font-medium",
              "bg-primary text-primary-foreground transition-colors hover:bg-primary/90",
              "disabled:pointer-events-none disabled:opacity-50"
            )}
          >
            <Play size={11} strokeWidth={1.5} />
            Run
          </button>
        </div>
      </div>

      {/* Task history */}
      {tasks.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground">Recent tasks</p>
          {tasks.map((task) => (
            <IndexingTaskCard key={task.taskId} task={task} onStop={stopTask} />
          ))}
        </div>
      )}

      {tasks.length === 0 && folders.length === 0 && (
        <div className="flex flex-col items-center gap-2 py-10 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-muted">
            <Activity size={20} className="text-muted-foreground" strokeWidth={1.5} />
          </div>
          <p className="text-sm text-muted-foreground">No indexing tasks yet.</p>
        </div>
      )}
    </div>
  );
}

interface IndexingTaskCardProps {
  task: IndexingTaskState;
  onStop: (taskId: string) => void;
}

function IndexingTaskCard({ task, onStop }: IndexingTaskCardProps) {
  const [errorsExpanded, setErrorsExpanded] = useState(false);

  const statusValue = task.status?.status ?? "queued";
  const isRunning = task.polling || statusValue === "running" || statusValue === "queued";
  const isCancelled = statusValue === "cancelled";
  const hasErrors = (task.status?.errors?.length ?? 0) > 0;
  const isComplete = statusValue === "completed" || statusValue === "completed_with_errors";

  const found = task.status?.files_found ?? 0;
  const indexed = task.status?.files_indexed ?? 0;
  const skipped = task.status?.files_skipped ?? 0;
  const errorCount = task.status?.errors?.length ?? 0;

  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2.5 space-y-1.5">
      <div className="flex items-center gap-2">
        {isRunning ? (
          <Loader2 size={13} className="flex-shrink-0 animate-spin text-primary" />
        ) : isComplete && !hasErrors ? (
          <CheckCircle size={13} className="flex-shrink-0 text-success" />
        ) : hasErrors || isCancelled ? (
          <AlertCircle
            size={13}
            className={cn("flex-shrink-0", isCancelled ? "text-muted-foreground" : "text-warning")}
          />
        ) : null}

        <p className="min-w-0 flex-1 truncate text-xs text-foreground" title={task.workspacePath}>
          {task.workspacePath}
        </p>

        {/* Stop button — only visible while running or queued */}
        {isRunning && (
          <button
            onClick={() => onStop(task.taskId)}
            title="Stop indexing"
            className={cn(
              "inline-flex flex-shrink-0 items-center gap-1 rounded-md px-2 py-0.5 text-2xs font-medium",
              "border border-destructive/30 bg-destructive/10 text-destructive",
              "transition-colors hover:bg-destructive/20"
            )}
          >
            <Square size={9} strokeWidth={1.5} />
            Stop
          </button>
        )}

        <span
          className={cn(
            "flex-shrink-0 rounded-full px-1.5 py-0.5 text-2xs font-medium capitalize",
            isRunning
              ? "bg-primary/10 text-primary"
              : isComplete && !hasErrors
                ? "bg-success/10 text-success"
                : hasErrors
                  ? "bg-warning/10 text-warning"
                  : isCancelled
                    ? "bg-muted text-muted-foreground"
                    : "bg-muted text-muted-foreground"
          )}
        >
          {statusValue}
        </span>
      </div>

      {task.status && (
        <div className="flex gap-3 text-2xs text-muted-foreground">
          <span>{found} found</span>
          <span>{indexed} indexed</span>
          <span>{skipped} skipped</span>
          {hasErrors && (
            <button
              onClick={() => setErrorsExpanded((v) => !v)}
              className="flex items-center gap-0.5 text-warning hover:underline"
            >
              {errorsExpanded ? <ChevronDown size={9} /> : <ChevronRight size={9} />}
              {errorCount} {errorCount === 1 ? "error" : "errors"}
            </button>
          )}
        </div>
      )}

      {found > 0 && (
        <div className="h-1 w-full overflow-hidden rounded-full bg-muted">
          <div
            className={cn(
              "h-full rounded-full transition-all",
              isCancelled ? "bg-muted-foreground" : isRunning ? "bg-primary" : "bg-success"
            )}
            style={{
              width: `${found > 0 ? Math.round(((indexed + skipped) / found) * 100) : 0}%`,
            }}
          />
        </div>
      )}

      {/* Inline error list — collapsible */}
      {errorsExpanded && task.status?.errors && task.status.errors.length > 0 && (
        <div className="mt-1.5 space-y-1 rounded-md border border-warning/20 bg-warning/5 p-2">
          {task.status.errors.slice(0, 20).map((err, i) => (
            <p key={i} className="break-all font-mono text-2xs text-warning leading-relaxed">
              {err}
            </p>
          ))}
          {task.status.errors.length > 20 && (
            <p className="text-2xs text-muted-foreground">
              …and {task.status.errors.length - 20} more (see Errors tab)
            </p>
          )}
        </div>
      )}
    </div>
  );
}
