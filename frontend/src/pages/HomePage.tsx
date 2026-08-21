import {
  FileText,
  Layers,
  AlignLeft,
  MessageSquare,
  FolderOpen,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDashboard } from "@/hooks/useDashboard";
import { useGreeting } from "@/hooks/useGreeting";
import { StatTile } from "@/components/home/StatTile";
import { RecentFilesList } from "@/components/home/RecentFilesList";

function StatsSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="h-24 animate-pulse rounded-xl border border-border bg-muted/40" />
      ))}
    </div>
  );
}

export function HomePage() {
  const { stats, isLoadingStats, statsError, refresh } = useDashboard();
  const greeting = useGreeting();

  return (
    <div className="flex flex-col gap-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-lg font-semibold text-foreground">{greeting}</h1>
          <p className="text-sm text-muted-foreground">Overview of your indexed knowledge base.</p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => void refresh()}
          className="gap-1.5 text-muted-foreground"
        >
          <RefreshCw size={13} />
          Refresh
        </Button>
      </div>

      {/* Stats tiles */}
      {statsError ? (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">
          <AlertTriangle size={14} className="flex-shrink-0" />
          {statsError}
        </div>
      ) : isLoadingStats ? (
        <StatsSkeleton />
      ) : stats ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <StatTile label="Documents" value={stats.document_count} icon={FileText} />
          <StatTile label="Chunks" value={stats.chunk_count} icon={Layers} />
          <StatTile label="Characters" value={stats.total_chars} icon={AlignLeft} />
          <StatTile label="Conversations" value={stats.conversation_count} icon={MessageSquare} />
          <StatTile label="Watched Folders" value={stats.watched_folder_count} icon={FolderOpen} />
          <StatTile
            label="Errors"
            value={stats.indexing_error_count}
            icon={AlertTriangle}
            accent={stats.indexing_error_count > 0 ? "warning" : "default"}
          />
        </div>
      ) : null}

      {/* Recently indexed files */}
      <section>
        <h2 className="mb-3 text-sm font-semibold text-foreground">Recently Indexed</h2>
        {isLoadingStats ? (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-10 animate-pulse rounded-lg bg-muted/40" />
            ))}
          </div>
        ) : (
          <RecentFilesList files={stats?.recent_files ?? []} />
        )}
      </section>
    </div>
  );
}
