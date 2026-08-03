import { useEffect, useState } from "react";
import { StatusIndicator } from "@/components/common/StatusIndicator";
import { useTheme } from "@/hooks/useTheme";
import { cn } from "@/lib/utils";
import { STATUS_BAR_HEIGHT } from "@/layouts/constants";
import { IPCClient } from "@/services/ipc/IPCClient";

type StatusVariant = "online" | "offline" | "degraded" | "unknown";

const IS_TAURI = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

interface ServiceStatus {
  aiProvider: StatusVariant;
  database: StatusVariant;
  searchIndex: StatusVariant;
  sync: StatusVariant;
}

const DEFAULT_STATUS: ServiceStatus = {
  aiProvider: "unknown",
  database: "unknown",
  searchIndex: "unknown",
  sync: "unknown",
};

async function fetchServiceStatus(): Promise<Partial<ServiceStatus>> {
  const result: Partial<ServiceStatus> = {};

  const [health, watcher] = await Promise.allSettled([
    IPCClient.healthCheck(),
    IPCClient.getWatcherStatus(),
  ]);

  // Database + AI provider — inferred from sidecar health
  if (health.status === "fulfilled") {
    result.database = "online";
    result.aiProvider = "online";
  } else {
    result.database = "offline";
    result.aiProvider = "offline";
  }

  // Search index — watcher running means indexing infra is up
  if (watcher.status === "fulfilled") {
    result.searchIndex = watcher.value.running ? "online" : "degraded";
    result.sync = watcher.value.watched_count > 0 ? "online" : "degraded";
  } else {
    result.searchIndex = "unknown";
    result.sync = "unknown";
  }

  return result;
}

interface StatusBarProps {
  className?: string;
}

export function StatusBar({ className }: StatusBarProps) {
  const { resolvedTheme } = useTheme();
  const [status, setStatus] = useState<ServiceStatus>(DEFAULT_STATUS);

  useEffect(() => {
    if (!IS_TAURI) return;

    const poll = async () => {
      const fresh = await fetchServiceStatus();
      setStatus((prev) => ({ ...prev, ...fresh }));
    };

    void poll();
    const interval = setInterval(() => void poll(), 15_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <footer
      style={{ height: STATUS_BAR_HEIGHT }}
      className={cn(
        "z-sticky flex flex-shrink-0 items-center gap-4 border-t border-border bg-background px-4",
        className
      )}
      aria-label="Application status"
    >
      {/* Left section — service statuses */}
      <div className="flex items-center gap-4">
        <StatusIndicator label="AI Provider" status={status.aiProvider} />
        <StatusIndicator label="Database" status={status.database} />
        <StatusIndicator label="Search Index" status={status.searchIndex} />
      </div>

      {/* Right section — sync and theme */}
      <div className="ml-auto flex items-center gap-4">
        <StatusIndicator label="Sync" status={status.sync} />
        <span className="text-2xs text-muted-foreground capitalize">{resolvedTheme}</span>
      </div>
    </footer>
  );
}
