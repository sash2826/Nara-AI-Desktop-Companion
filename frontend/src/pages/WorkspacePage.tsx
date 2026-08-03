import { Folders, Files, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { FolderList } from "@/components/workspace/FolderList";
import { DocumentBrowser } from "@/components/workspace/DocumentBrowser";
import { IndexingStatusPanel } from "@/components/workspace/IndexingStatusPanel";
import { useWorkspace } from "@/hooks/useWorkspace";

const TABS = [
  { id: "folders" as const, label: "Folders", icon: Folders },
  { id: "documents" as const, label: "Documents", icon: Files },
  { id: "indexing" as const, label: "Indexing", icon: Activity },
];

export function WorkspacePage() {
  const { activeTab, setActiveTab } = useWorkspace();

  return (
    <div className="flex h-full flex-col">
      {/* Tab bar */}
      <div className="flex flex-shrink-0 items-center gap-1 border-b border-border px-4 pt-4">
        {TABS.map(({ id, label, icon: Icon }) => (
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
      </div>

      {/* Tab content */}
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
        {activeTab === "folders" && <FolderList />}
        {activeTab === "documents" && <DocumentBrowser />}
        {activeTab === "indexing" && <IndexingStatusPanel />}
      </div>
    </div>
  );
}
