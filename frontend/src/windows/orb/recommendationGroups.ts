import type { Recommendation } from "./useRecommendations";

/** Below this the top match is too weak to present under a confident folder heading. */
export const LOW_CONFIDENCE_THRESHOLD = 0.4;
/** At or above this a match counts as "confident" in a group summary. */
export const CONFIDENT_THRESHOLD = 0.6;
/** Total pending count at or below which the first group opens automatically. */
export const AUTO_EXPAND_MAX_TOTAL = 5;

export const NEEDS_REVIEW_KEY = "__needs_review__";

export interface RecommendationGroup {
  key: string;
  /** Destination folder, or null for the "Needs review" bucket. */
  folder: string | null;
  label: string;
  recommendations: Recommendation[];
  confidentCount: number;
  meanScore: number;
}

export function topCandidate(rec: Recommendation): Recommendation["candidates"][0] | null {
  return rec.candidates[0] ?? null;
}

export function folderName(path: string): string {
  return path.split(/[\\/]/).filter(Boolean).pop() ?? path;
}

export function fileName(path: string): string {
  return path.split(/[\\/]/).pop() ?? path;
}

/**
 * Buckets recommendations by their top candidate folder.
 *
 * Weak matches are pulled into a separate "Needs review" group rather than
 * listed under a folder heading they don't actually justify.
 */
export function groupRecommendations(recs: Recommendation[]): RecommendationGroup[] {
  const byFolder = new Map<string, Recommendation[]>();
  const needsReview: Recommendation[] = [];

  for (const rec of recs) {
    const top = topCandidate(rec);
    if (!top || top.score < LOW_CONFIDENCE_THRESHOLD) {
      needsReview.push(rec);
      continue;
    }
    const bucket = byFolder.get(top.folder);
    if (bucket) bucket.push(rec);
    else byFolder.set(top.folder, [rec]);
  }

  const groups: RecommendationGroup[] = [...byFolder.entries()].map(([folder, items]) => {
    const scores = items.map((r) => topCandidate(r)?.score ?? 0);
    return {
      key: folder,
      folder,
      label: folderName(folder),
      recommendations: items,
      confidentCount: scores.filter((s) => s >= CONFIDENT_THRESHOLD).length,
      meanScore: scores.reduce((sum, s) => sum + s, 0) / (scores.length || 1),
    };
  });

  // Most decidable first, so the queue clears fastest.
  groups.sort((a, b) => b.meanScore - a.meanScore);

  if (needsReview.length > 0) {
    groups.push({
      key: NEEDS_REVIEW_KEY,
      folder: null,
      label: "Needs review",
      recommendations: needsReview,
      confidentCount: 0,
      meanScore: 0,
    });
  }

  return groups;
}
