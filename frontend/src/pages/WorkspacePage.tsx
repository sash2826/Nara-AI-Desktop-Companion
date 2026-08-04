import { Folders, Files, Activity, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { FolderList } from "@/components/workspace/FolderList";
import { DocumentBrowser } from "@/components/workspace/DocumentBrowser";
import { IndexingStatusPanel } from "@/components/workspace/IndexingStatusPanel";
import { IndexingErrorsTab } from "@/components/workspace/IndexingErrorsTab";
import { useWorkspace } from "@/hooks/useWorkspace";
import { useWorkspaceStore } from "@/store/workspaceStore";

const STATIC_TABS = [
  { id: "folders" as const, label: "Folders", icon: Folders },
  { id: "documents" as const, label: "Documents", icon: Files },
  { id: "indexing" as const, label: "Indexing", icon: Activity },
];

export function WorkspacePage() {
  const { activeTab, setActiveTab } = useWorkspace();
  const errorCount = useWorkspaceStore((s) => s.errorCount);

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
          onClick={() => setActiveTab("errors")}
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
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
        {activeTab === "folders" && <FolderList />}
        {activeTab === "documents" && <DocumentBrowser />}
        {activeTab === "indexing" && <IndexingStatusPanel />}
        {activeTab === "errors" && <IndexingErrorsTab />}
      </div>
    </div>
  );
}
