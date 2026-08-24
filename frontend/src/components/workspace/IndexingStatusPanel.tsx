import { useState } from "react";
import {
  Loader2,
  Play,
  CheckCircle,
  AlertCircle,
  Activity,
  Square,
  ChevronDown,
  ChevronRight,
  Circle,
  Network,
  Link,
  FileSearch,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useWorkspace } from "@/hooks/useWorkspace";
import type { IndexingStatus } from "@/services/ipc/IPCClient";
import { useIndexingStore } from "@/store/indexingStore";
import type { IndexingTaskState } from "@/store/indexingStore";

export function IndexingStatusPanel() {
  const { folders } = useWorkspace();
  const [customPath, setCustomPath] = useState("");
  const { tasks, startIndex, stopTask } = useIndexingStore();

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-foreground">Indexing</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Manually trigger indexing on any folder.
        </p>
      </div>

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

// ---------------------------------------------------------------------------
// Stage helpers
// ---------------------------------------------------------------------------

type StageId = "indexing" | "building_graph" | "linking_entities" | "completed";

function resolveStage(status: IndexingStatus | null, polling: boolean): StageId {
  if (!status) return "indexing";
  const s = status.stage as StageId | undefined;
  if (s === "building_graph" || s === "linking_entities") return s;
  if (
    status.status === "completed" ||
    status.status === "completed_with_errors" ||
    (!polling && status.status !== "running" && status.status !== "queued")
  )
    return "completed";
  return "indexing";
}

type PassState = "pending" | "active" | "done";

function passState(stageId: StageId, pass: 1 | 2 | 3): PassState {
  const order: StageId[] = ["indexing", "building_graph", "linking_entities", "completed"];
  const current = order.indexOf(stageId);
  const passTrigger: StageId[] = ["indexing", "building_graph", "linking_entities"];
  const passIndex = order.indexOf(passTrigger[pass - 1]);
  if (current < passIndex) return "pending";
  if (current === passIndex) return "active";
  return "done";
}

// ---------------------------------------------------------------------------
// Task card
// ---------------------------------------------------------------------------

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

  const currentStage = resolveStage(task.status, task.polling);
  const graphTotal = task.status?.graph_files_total ?? 0;
  const graphProcessed = task.status?.graph_files_processed ?? 0;

  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2.5 space-y-2">
      {/* Header row */}
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
                  : "bg-muted text-muted-foreground"
          )}
        >
          {statusValue}
        </span>
      </div>

      {/* Three-stage progress */}
      {(isRunning || isComplete || isCancelled) && (
        <div className="space-y-1.5">
          <PassRow
            pass={1}
            icon={FileSearch}
            label="Extracting & indexing files"
            state={isCancelled ? "done" : passState(currentStage, 1)}
            progress={found > 0 ? (indexed + skipped) / found : null}
            detail={
              task.status
                ? `${indexed} indexed · ${skipped} skipped${found ? ` / ${found} found` : ""}`
                : null
            }
          />
          <PassRow
            pass={2}
            icon={Network}
            label="Building knowledge graph"
            state={isCancelled ? "pending" : passState(currentStage, 2)}
            progress={
              graphTotal > 0
                ? graphProcessed / graphTotal
                : currentStage === "building_graph"
                  ? null // indeterminate
                  : 0
            }
            detail={
              graphTotal > 0
                ? `${graphProcessed} / ${graphTotal} documents`
                : currentStage === "building_graph"
                  ? "Processing…"
                  : null
            }
          />
          <PassRow
            pass={3}
            icon={Link}
            label="Linking entities"
            state={isCancelled ? "pending" : passState(currentStage, 3)}
            progress={null}
            detail={null}
          />
        </div>
      )}

      {/* Error list */}
      {task.status && hasErrors && (
        <button
          onClick={() => setErrorsExpanded((v) => !v)}
          className="flex items-center gap-0.5 text-2xs text-warning hover:underline"
        >
          {errorsExpanded ? <ChevronDown size={9} /> : <ChevronRight size={9} />}
          {errorCount} {errorCount === 1 ? "error" : "errors"}
        </button>
      )}

      {errorsExpanded && task.status?.errors && task.status.errors.length > 0 && (
        <div className="space-y-1 rounded-md border border-warning/20 bg-warning/5 p-2">
          {task.status.errors.slice(0, 20).map((err, i) => (
            <p key={i} className="break-all font-mono text-2xs text-warning leading-relaxed">
              {err}
            </p>
          ))}
          {task.status.errors.length > 20 && (
            <p className="text-2xs text-muted-foreground">
              …and {task.status.errors.length - 20} more
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Per-pass row
// ---------------------------------------------------------------------------

interface PassRowProps {
  pass: 1 | 2 | 3;
  icon: React.ElementType;
  label: string;
  state: PassState;
  progress: number | null; // 0–1, or null = indeterminate
  detail: string | null;
}

function PassRow({ icon: Icon, label, state, progress, detail }: PassRowProps) {
  const isActive = state === "active";
  const isDone = state === "done";
  const isPending = state === "pending";
  const isIndeterminate = isActive && progress === null;

  // Fill % for the determinate bar: 100 when done, actual progress when active, 0 when pending.
  const fillPct = isDone ? 100 : isActive && progress !== null ? Math.round(progress * 100) : 0;

  return (
    <div
      className={cn(
        "flex flex-col gap-1 rounded-md px-2 py-1.5 transition-colors",
        isActive && "bg-primary/5 border border-primary/15",
        isDone && "opacity-60",
        isPending && "opacity-30"
      )}
    >
      <div className="flex items-center gap-2">
        {isDone ? (
          <CheckCircle size={11} className="flex-shrink-0 text-success" strokeWidth={1.75} />
        ) : isActive ? (
          <Loader2 size={11} className="flex-shrink-0 animate-spin text-primary" />
        ) : (
          <Circle size={11} className="flex-shrink-0 text-muted-foreground/40" strokeWidth={1.5} />
        )}
        <Icon
          size={11}
          className={cn(
            "flex-shrink-0",
            isActive ? "text-primary" : isDone ? "text-success" : "text-muted-foreground/40"
          )}
          strokeWidth={1.5}
        />
        <span
          className={cn(
            "text-2xs font-medium",
            isActive
              ? "text-foreground"
              : isDone
                ? "text-muted-foreground"
                : "text-muted-foreground/40"
          )}
        >
          {label}
        </span>
        {detail && isActive && (
          <span className="ml-auto text-2xs text-muted-foreground/70 tabular-nums">{detail}</span>
        )}
      </div>

      {/* Progress track — always visible so each pass has its own distinct bar */}
      <div className="pl-[23px]">
        <div className="h-0.5 w-full overflow-hidden rounded-full bg-muted">
          {isIndeterminate ? (
            <div className="h-full w-1/3 rounded-full bg-primary animate-pulse" />
          ) : (
            <div
              className={cn(
                "h-full rounded-full transition-all duration-300",
                isDone ? "bg-success" : "bg-primary"
              )}
              style={{ width: `${fillPct}%` }}
            />
          )}
        </div>
      </div>
    </div>
  );
}
