import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useRecommendations, type BulkProgress } from "./useRecommendations";
import {
  AUTO_EXPAND_MAX_TOTAL,
  NEEDS_REVIEW_KEY,
  groupRecommendations,
  type RecommendationGroup,
} from "./recommendationGroups";
import { RecommendationCard } from "./RecommendationCard";

const SKIP_ALL_KEY = "__all__";
/** Lets the exit animation finish before a completed group collapses. */
const GROUP_COLLAPSE_DELAY_MS = 250;

/**
 * Overlay showing pending file placement recommendations, grouped by
 * destination folder so the user decides per-folder instead of per-file.
 *
 * All data fetching, polling, and action logic lives in useRecommendations.
 */
export function OrbNotificationOverlay() {
  const {
    recommendations,
    loading,
    errors,
    conflicts,
    bulk,
    handleAccept,
    handleChooseFolder,
    handleConflictReplace,
    handleConflictKeepBoth,
    handleConflictCancel,
    handleSkip,
    handleAcceptMany,
    handleSkipMany,
    handleDismiss,
  } = useRecommendations();

  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const [confirmSkipAll, setConfirmSkipAll] = useState(false);
  const didAutoExpand = useRef(false);

  const groups = useMemo(() => groupRecommendations(recommendations), [recommendations]);
  const total = recommendations.length;
  const isBusy = bulk !== null;

  // Only on first load — auto-expanding after a group completes would slide a
  // new button under the cursor mid-click.
  useEffect(() => {
    if (didAutoExpand.current || groups.length === 0) return;
    didAutoExpand.current = true;
    if (groups.length === 1 || total <= AUTO_EXPAND_MAX_TOTAL) {
      // setTimeout defers the setState out of the effect body, satisfying the
      // react-hooks/set-state-in-effect rule without changing behaviour.
      const t = setTimeout(() => setExpandedKey(groups[0].key), 0);
      return () => clearTimeout(t);
    }
  }, [groups, total]);

  // A group leaves `groups` only once every file in it is resolved; anything
  // that conflicted or errored keeps it open.
  useEffect(() => {
    if (!expandedKey || groups.some((g) => g.key === expandedKey)) return;
    const timer = setTimeout(() => setExpandedKey(null), GROUP_COLLAPSE_DELAY_MS);
    return () => clearTimeout(timer);
  }, [groups, expandedKey]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      if (confirmSkipAll) setConfirmSkipAll(false);
      else if (expandedKey) setExpandedKey(null);
      else handleDismiss();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [confirmSkipAll, expandedKey, handleDismiss]);

  return (
    <motion.div
      data-orb-surface
      initial={{ opacity: 0, y: 8, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 8, scale: 0.95 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
      style={{
        position: "absolute",
        bottom: "calc(100% + 10px)",
        right: 0,
        width: 360,
        zIndex: 100,
        background: "hsl(var(--popover) / 0.94)",
        backdropFilter: "blur(20px) saturate(180%)",
        WebkitBackdropFilter: "blur(20px) saturate(180%)",
        border: "1px solid hsl(var(--border) / 0.7)",
        borderRadius: 16,
        boxShadow: ["0 8px 32px hsl(0 0% 0% / 0.28)", "inset 0 1px 0 hsl(0 0% 100% / 0.08)"].join(
          ", "
        ),
        color: "hsl(var(--popover-foreground))",
        fontFamily: "var(--font-sans), system-ui, sans-serif",
        fontSize: 13,
        maxHeight: 520,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "12px 14px 8px",
          borderBottom: "1px solid hsl(var(--border) / 0.6)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 8,
          flexShrink: 0,
        }}
      >
        <span style={{ fontWeight: 600, fontSize: 12, color: "hsl(var(--warning))" }}>
          File Placement Suggestions
          {total > 0 && (
            <span style={{ color: "hsl(var(--muted-foreground))", marginLeft: 6 }}>{total}</span>
          )}
        </span>
        <button
          onClick={handleDismiss}
          style={{
            background: "none",
            border: "none",
            color: "hsl(var(--muted-foreground))",
            cursor: "pointer",
            fontSize: 16,
            lineHeight: 1,
            padding: "0 2px",
          }}
          aria-label="Close suggestions"
        >
          ×
        </button>
      </div>

      {/* List */}
      <div style={{ overflowY: "auto", flex: 1, minHeight: 0, overscrollBehavior: "contain" }}>
        {loading && (
          <div style={{ padding: "16px 14px", color: "hsl(var(--muted-foreground))" }}>
            Loading…
          </div>
        )}

        {!loading && total === 0 && (
          <div style={{ padding: "16px 14px", color: "hsl(var(--muted-foreground))" }}>
            No pending suggestions.
          </div>
        )}

        <AnimatePresence initial={false}>
          {groups.map((group) => (
            <GroupSection
              key={group.key}
              group={group}
              expanded={expandedKey === group.key}
              bulk={bulk}
              isBusy={isBusy}
              errors={errors}
              conflicts={conflicts}
              onToggle={() => setExpandedKey(expandedKey === group.key ? null : group.key)}
              onAcceptGroup={handleAcceptMany}
              onSkipGroup={handleSkipMany}
              onAccept={handleAccept}
              onChooseFolder={(id) => void handleChooseFolder(id)}
              onSkip={(id) => void handleSkip(id)}
              onConflictReplace={handleConflictReplace}
              onConflictKeepBoth={handleConflictKeepBoth}
              onConflictCancel={handleConflictCancel}
            />
          ))}
        </AnimatePresence>
      </div>

      {total > 1 && (
        <div
          style={{
            padding: "8px 14px",
            borderTop: "1px solid hsl(var(--border) / 0.6)",
            flexShrink: 0,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          {confirmSkipAll ? (
            <>
              <span style={{ fontSize: 12, flex: 1 }}>Skip all {total}?</span>
              <button
                onClick={() => {
                  setConfirmSkipAll(false);
                  void handleSkipMany(
                    SKIP_ALL_KEY,
                    recommendations.map((r) => r.id)
                  );
                }}
                disabled={isBusy}
                style={{
                  padding: "3px 10px",
                  borderRadius: 7,
                  border: "1px solid hsl(var(--destructive) / 0.5)",
                  background: "hsl(var(--destructive) / 0.15)",
                  color: "hsl(var(--destructive))",
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: isBusy ? "default" : "pointer",
                }}
              >
                Skip all
              </button>
              <button
                onClick={() => setConfirmSkipAll(false)}
                style={{
                  padding: "3px 10px",
                  borderRadius: 7,
                  border: "1px solid hsl(var(--border))",
                  background: "hsl(var(--muted) / 0.6)",
                  color: "hsl(var(--muted-foreground))",
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              onClick={() => setConfirmSkipAll(true)}
              disabled={isBusy}
              style={{
                background: "none",
                border: "none",
                color: "hsl(var(--muted-foreground))",
                fontSize: 12,
                cursor: isBusy ? "default" : "pointer",
                padding: 0,
                opacity: isBusy ? 0.5 : 1,
              }}
            >
              {bulk?.key === SKIP_ALL_KEY
                ? `Skipping ${bulk.done}/${bulk.total}…`
                : `Skip all ${total}`}
            </button>
          )}
        </div>
      )}
    </motion.div>
  );
}

interface GroupSectionProps {
  group: RecommendationGroup;
  expanded: boolean;
  bulk: BulkProgress | null;
  isBusy: boolean;
  errors: Map<string, string>;
  conflicts: Map<string, string>;
  onToggle: () => void;
  onAcceptGroup: (key: string, recIds: string[], folder: string) => Promise<void>;
  onSkipGroup: (key: string, recIds: string[]) => Promise<void>;
  onAccept: (recId: string, folder: string) => void;
  onChooseFolder: (recId: string) => void;
  onSkip: (recId: string) => void;
  onConflictReplace: (recId: string) => void;
  onConflictKeepBoth: (recId: string) => void;
  onConflictCancel: (recId: string) => void;
}

function GroupSection({
  group,
  expanded,
  bulk,
  isBusy,
  errors,
  conflicts,
  onToggle,
  onAcceptGroup,
  onSkipGroup,
  ...cardHandlers
}: GroupSectionProps) {
  const count = group.recommendations.length;
  const isNeedsReview = group.key === NEEDS_REVIEW_KEY;
  const groupBusy = bulk?.key === group.key;
  const ids = group.recommendations.map((r) => r.id);
  const targetFolder = group.folder;

  return (
    <motion.div
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.18 }}
      style={{ borderBottom: "1px solid hsl(var(--border) / 0.4)", overflow: "hidden" }}
    >
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={expanded}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "10px 14px",
          background: "none",
          border: "none",
          color: "inherit",
          font: "inherit",
          textAlign: "left",
          cursor: "pointer",
        }}
      >
        {expanded ? (
          <ChevronDown size={14} style={{ flexShrink: 0 }} />
        ) : (
          <ChevronRight size={14} style={{ flexShrink: 0 }} />
        )}
        <span
          style={{
            flex: 1,
            minWidth: 0,
            fontWeight: 500,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            color: isNeedsReview ? "hsl(var(--muted-foreground))" : "inherit",
          }}
          title={targetFolder ?? group.label}
        >
          {group.label}
        </span>
        {!isNeedsReview && group.confidentCount > 0 && (
          <span style={{ fontSize: 11, color: "hsl(var(--success))", flexShrink: 0 }}>
            {group.confidentCount} confident
          </span>
        )}
        <span
          style={{
            flexShrink: 0,
            minWidth: 18,
            textAlign: "center",
            borderRadius: 999,
            padding: "1px 6px",
            fontSize: 11,
            fontWeight: 600,
            background: "hsl(var(--muted))",
            color: "hsl(var(--muted-foreground))",
          }}
        >
          {count}
        </span>
      </button>

      {expanded && (
        <>
          {targetFolder && (
            <div style={{ display: "flex", gap: 8, alignItems: "center", padding: "0 14px 10px" }}>
              <button
                onClick={() => void onAcceptGroup(group.key, ids, targetFolder)}
                disabled={isBusy}
                style={{
                  padding: "4px 12px",
                  borderRadius: 7,
                  border: "none",
                  background: "hsl(var(--primary))",
                  color: "hsl(var(--primary-foreground))",
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: isBusy ? "default" : "pointer",
                  opacity: isBusy ? 0.5 : 1,
                }}
              >
                {groupBusy && bulk
                  ? `Moving ${bulk.done}/${bulk.total}…`
                  : `Move all ${count} here`}
              </button>
              <button
                onClick={() => void onSkipGroup(group.key, ids)}
                disabled={isBusy}
                style={{
                  padding: "4px 10px",
                  borderRadius: 7,
                  border: "1px solid hsl(var(--border))",
                  background: "hsl(var(--muted) / 0.6)",
                  color: "hsl(var(--muted-foreground))",
                  fontSize: 12,
                  cursor: isBusy ? "default" : "pointer",
                  opacity: isBusy ? 0.5 : 1,
                }}
              >
                Skip folder
              </button>
            </div>
          )}

          <AnimatePresence initial={false}>
            {group.recommendations.map((rec) => (
              <RecommendationCard
                key={rec.id}
                recommendation={rec}
                error={errors.get(rec.id)}
                conflictFolder={conflicts.get(rec.id)}
                disabled={isBusy}
                {...cardHandlers}
              />
            ))}
          </AnimatePresence>
        </>
      )}
    </motion.div>
  );
}
