import { useState } from "react";
import { Monitor, Brain, FolderSearch, HardDrive, Save, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useSettings } from "@/hooks/useSettings";
import { GeneralSettings } from "@/components/settings/GeneralSettings";
import { AIProviderSettings } from "@/components/settings/AIProviderSettings";
import { IndexingSettings } from "@/components/settings/IndexingSettings";
import { BackupSettings } from "@/components/settings/BackupSettings";

type SettingsTab = "general" | "ai" | "indexing" | "backup";

const TABS: { id: SettingsTab; label: string; icon: typeof Monitor }[] = [
  { id: "general", label: "General", icon: Monitor },
  { id: "ai", label: "AI Provider", icon: Brain },
  { id: "indexing", label: "Indexing", icon: FolderSearch },
  { id: "backup", label: "Backup", icon: HardDrive },
];

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>("general");
  const { settings, isDirty, updateTheme, updateAIProvider, updateIndexing, save, reset } =
    useSettings();

  return (
    <div className="flex h-full gap-6">
      {/* Sidebar navigation */}
      <nav className="flex w-44 flex-shrink-0 flex-col gap-0.5" aria-label="Settings sections">
        <p className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Settings
        </p>
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => setActiveTab(id)}
            aria-current={activeTab === id ? "page" : undefined}
            className={cn(
              "flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm transition-colors",
              activeTab === id
                ? "bg-accent text-accent-foreground font-medium"
                : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
            )}
          >
            <Icon size={15} strokeWidth={1.75} />
            {label}
          </button>
        ))}

        {/* Save / reset — anchored at bottom of sidebar */}
        <div className="mt-auto space-y-2 pt-4">
          <Button size="sm" className="w-full gap-1.5" onClick={save} disabled={!isDirty}>
            <Save size={13} />
            Save
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="w-full gap-1.5 text-muted-foreground"
            onClick={reset}
          >
            <RotateCcw size={13} />
            Reset
          </Button>
        </div>
      </nav>

      {/* Divider */}
      <div className="w-px flex-shrink-0 bg-border" />

      {/* Panel content */}
      <main className="min-w-0 flex-1 overflow-y-auto">
        {activeTab === "general" && (
          <GeneralSettings theme={settings.theme} onThemeChange={updateTheme} />
        )}
        {activeTab === "ai" && (
          <AIProviderSettings settings={settings.aiProvider} onChange={updateAIProvider} />
        )}
        {activeTab === "indexing" && (
          <IndexingSettings settings={settings.indexing} onChange={updateIndexing} />
        )}
        {activeTab === "backup" && <BackupSettings />}
      </main>
    </div>
  );
}
