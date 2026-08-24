import { Folders, Activity, AlertTriangle, PackageSearch } from "lucide-react";
import { cn } from "@/lib/utils";
import { WorkspaceExplorer } from "@/components/workspace/WorkspaceExplorer";
import { OrganiseTab } from "@/components/workspace/OrganiseTab";
import { IndexingStatusPanel } from "@/components/workspace/IndexingStatusPanel";
import { IndexingErrorsTab } from "@/components/workspace/IndexingErrorsTab";
import { useWorkspace } from "@/hooks/useWorkspace";
import { useWorkspaceStore } from "@/store/workspaceStore";

// ── Page ──────────────────────────────────────────────────────────────────────

const STATIC_TABS = [
  { id: "explorer" as const, label: "Explorer", icon: Folders },
  { id: "indexing" as const, label: "Indexing", icon: Activity },
  { id: "organise" as const, label: "Organise", icon: PackageSearch },
];

export function WorkspacePage() {
  const { activeTab, setActiveTab } = useWorkspace();
  const errorCount = useWorkspaceStore((s) => s.errorCount);
  const setErrorCount = useWorkspaceStore((s) => s.setErrorCount);

  return (
    <div className="flex h-full flex-col">
      {/* Tab bar */}
      <div className="flex flex-shrink-0 items-center gap-1 border-b border-border px-4 pt-4">
        {STATIC_TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-t-md border-b-2 px-3 pb-2.5 pt-1 text-xs font-medium transition-colors",
              activeTab === id
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            <Icon size={13} strokeWidth={1.5} />
            {label}
          </button>
        ))}

        {/* Errors tab — rendered separately so we can attach the badge */}
        <button
          onClick={() => {
            setActiveTab("errors");
            setErrorCount(0);
          }}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-t-md border-b-2 px-3 pb-2.5 pt-1 text-xs font-medium transition-colors",
            activeTab === "errors"
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          <AlertTriangle size={13} strokeWidth={1.5} />
          Errors
          {errorCount > 0 && (
            <span
              className={cn(
                "ml-0.5 flex h-4 min-w-4 items-center justify-center rounded-full px-1",
                "bg-destructive text-2xs font-semibold text-destructive-foreground"
              )}
            >
              {errorCount > 99 ? "99+" : errorCount}
            </span>
          )}
        </button>
      </div>

      {/* Tab content */}
      <div
        className={cn(
          "min-h-0 flex-1",
          activeTab === "explorer" || activeTab === "organise"
            ? "overflow-hidden"
            : "overflow-y-auto px-4 py-4"
        )}
      >
        {activeTab === "explorer" && <WorkspaceExplorer />}
        {activeTab === "indexing" && <IndexingStatusPanel />}
        {activeTab === "organise" && <OrganiseTab />}
        {activeTab === "errors" && <IndexingErrorsTab />}
      </div>
    </div>
  );
}
