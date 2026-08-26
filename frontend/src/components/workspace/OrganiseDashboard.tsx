import { PackageSearch, ShieldQuestion, Sparkles } from "lucide-react";
import type { ReactNode } from "react";
import type { PendingRecommendation } from "@/services/ipc/IPCClient";
import { CONFIDENT_THRESHOLD, LOW_CONFIDENCE_THRESHOLD } from "@/windows/orb/recommendationGroups";

interface OrganiseDashboardProps {
  recommendations: PendingRecommendation[];
}

export function OrganiseDashboard({ recommendations }: OrganiseDashboardProps) {
  const total = recommendations.length;
  const topScores = recommendations.map((rec) => rec.candidates[0]?.score ?? 0);
  const confident = topScores.filter((s) => s >= CONFIDENT_THRESHOLD).length;
  const needsReview = topScores.filter((s) => s < LOW_CONFIDENCE_THRESHOLD).length;

  return (
    <div className="grid grid-cols-3 gap-3">
      <StatTile
        icon={<PackageSearch size={14} strokeWidth={1.5} />}
        value={total}
        label={`Suggestion${total !== 1 ? "s" : ""} pending`}
      />
      <StatTile
        icon={<Sparkles size={14} strokeWidth={1.5} />}
        value={confident}
        label="High confidence"
        tone="success"
      />
      <StatTile
        icon={<ShieldQuestion size={14} strokeWidth={1.5} />}
        value={needsReview}
        label="Needs review"
        tone="muted"
      />
    </div>
  );
}

interface StatTileProps {
  icon: ReactNode;
  value: number;
  label: string;
  tone?: "default" | "success" | "muted";
}

function StatTile({ icon, value, label, tone = "default" }: StatTileProps) {
  const valueColor =
    tone === "success"
      ? "text-success"
      : tone === "muted"
        ? "text-muted-foreground"
        : "text-foreground";

  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2.5">
      <div className="flex items-center gap-1.5 text-muted-foreground">
        {icon}
        <span className="text-2xs uppercase tracking-wide">{label}</span>
      </div>
      <p className={`mt-1 text-xl font-semibold tabular-nums ${valueColor}`}>{value}</p>
    </div>
  );
}
