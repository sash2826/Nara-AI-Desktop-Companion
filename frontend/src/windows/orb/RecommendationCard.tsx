import type { CSSProperties } from "react";
import { motion } from "framer-motion";
import { FileTypeIcon } from "@/components/common/FileTypeIcon";
import type { Recommendation } from "./useRecommendations";
import { fileName, folderName } from "./recommendationGroups";

// eslint-disable-next-line react-refresh/only-export-components
export function labelColor(label: Recommendation["candidates"][0]["label"]): string {
  if (label === "Strong") return "hsl(var(--success))";
  if (label === "Good") return "hsl(var(--primary))";
  return "hsl(var(--muted-foreground))";
}

const baseButton: CSSProperties = {
  padding: "4px 10px",
  borderRadius: 7,
  fontSize: 12,
  cursor: "pointer",
};

const primaryButton: CSSProperties = {
  ...baseButton,
  padding: "4px 12px",
  border: "none",
  background: "hsl(var(--primary))",
  color: "hsl(var(--primary-foreground))",
  fontWeight: 600,
};

const secondaryButton: CSSProperties = {
  ...baseButton,
  border: "1px solid hsl(var(--border))",
  background: "hsl(var(--muted) / 0.6)",
  color: "hsl(var(--popover-foreground))",
};

const mutedButton: CSSProperties = {
  ...secondaryButton,
  color: "hsl(var(--muted-foreground))",
};

function disabledStyle(style: CSSProperties, disabled: boolean): CSSProperties {
  return disabled ? { ...style, opacity: 0.5, cursor: "default" } : style;
}

interface RecommendationCardProps {
  recommendation: Recommendation;
  error?: string;
  conflictFolder?: string;
  disabled: boolean;
  onAccept: (recId: string, folder: string) => void;
  onChooseFolder: (recId: string) => void;
  onSkip: (recId: string) => void;
  onConflictReplace: (recId: string) => void;
  onConflictKeepBoth: (recId: string) => void;
  onConflictCancel: (recId: string) => void;
}

export function RecommendationCard({
  recommendation: rec,
  error,
  conflictFolder,
  disabled,
  onAccept,
  onChooseFolder,
  onSkip,
  onConflictReplace,
  onConflictKeepBoth,
  onConflictCancel,
}: RecommendationCardProps) {
  const top = rec.candidates[0];
  const name = fileName(rec.source_path);

  return (
    <motion.div
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.18 }}
      style={{ padding: "10px 14px", borderBottom: "1px solid hsl(var(--border) / 0.4)" }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 4 }}>
        <FileTypeIcon path={rec.source_path} size={17} style={{ flexShrink: 0 }} />
        <div
          style={{
            minWidth: 0,
            fontWeight: 500,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
          title={rec.source_path}
        >
          {name}
        </div>
      </div>

      {conflictFolder ? (
        <>
          <div style={{ fontSize: 11, color: "hsl(var(--warning))", marginBottom: 8 }}>
            A file named <strong>{name}</strong> already exists in{" "}
            <strong>{folderName(conflictFolder)}</strong>.
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => onConflictReplace(rec.id)}
              disabled={disabled}
              style={disabledStyle(
                {
                  ...baseButton,
                  border: "1px solid hsl(var(--warning) / 0.4)",
                  background: "hsl(var(--warning) / 0.15)",
                  color: "hsl(var(--warning))",
                  fontWeight: 600,
                },
                disabled
              )}
            >
              Replace
            </button>
            <button
              onClick={() => onConflictKeepBoth(rec.id)}
              disabled={disabled}
              style={disabledStyle(primaryButton, disabled)}
            >
              Keep both
            </button>
            <button
              onClick={() => onConflictCancel(rec.id)}
              disabled={disabled}
              style={disabledStyle(mutedButton, disabled)}
            >
              Cancel
            </button>
          </div>
        </>
      ) : (
        <>
          {top && (
            <div style={{ fontSize: 12, color: "hsl(var(--muted-foreground))", marginBottom: 8 }}>
              <span style={{ color: labelColor(top.label), fontWeight: 600 }}>{top.label}</span>
              <span style={{ marginLeft: 4 }}>{Math.round(top.score * 100)}%</span>
              {" · "}
              <span title={top.folder}>{folderName(top.folder)}</span>
            </div>
          )}

          {error && (
            <div style={{ fontSize: 11, color: "hsl(var(--destructive))", marginBottom: 6 }}>
              {error}
            </div>
          )}

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {top && (
              <button
                onClick={() => onAccept(rec.id, top.folder)}
                disabled={disabled}
                style={disabledStyle(primaryButton, disabled)}
              >
                Move here
              </button>
            )}
            <button
              onClick={() => onChooseFolder(rec.id)}
              disabled={disabled}
              style={disabledStyle(secondaryButton, disabled)}
            >
              Choose folder…
            </button>
            <button
              onClick={() => onSkip(rec.id)}
              disabled={disabled}
              style={disabledStyle(mutedButton, disabled)}
            >
              Skip
            </button>
          </div>
        </>
      )}
    </motion.div>
  );
}
