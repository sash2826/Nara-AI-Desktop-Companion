import { describe, it, expect } from "vitest";
import {
  NEEDS_REVIEW_KEY,
  folderName,
  groupRecommendations,
} from "@/windows/orb/recommendationGroups";
import type { Recommendation } from "@/windows/orb/useRecommendations";

function rec(
  id: string,
  candidates: Array<[string, number, Recommendation["candidates"][0]["label"]]>
): Recommendation {
  return {
    id,
    source_path: `C:/Downloads/${id}.pdf`,
    candidates: candidates.map(([folder, score, label]) => ({ folder, score, label })),
  };
}

describe("folderName", () => {
  it("takes the last segment of a Windows path", () => {
    expect(folderName("C:\\Work\\Horizon-Logistics")).toBe("Horizon-Logistics");
  });

  it("ignores a trailing separator", () => {
    expect(folderName("/home/user/Polaris/")).toBe("Polaris");
  });
});

describe("groupRecommendations", () => {
  it("buckets recommendations by their top candidate folder", () => {
    const groups = groupRecommendations([
      rec("a", [["/w/Horizon", 0.8, "Most Likely"]]),
      rec("b", [["/w/Horizon", 0.7, "Most Likely"]]),
      rec("c", [["/w/Polaris", 0.6, "Likely"]]),
    ]);

    expect(groups).toHaveLength(2);
    expect(groups[0].label).toBe("Horizon");
    expect(groups[0].recommendations.map((r) => r.id)).toEqual(["a", "b"]);
    expect(groups[1].recommendations.map((r) => r.id)).toEqual(["c"]);
  });

  it("orders groups by mean confidence so easy wins come first", () => {
    const groups = groupRecommendations([
      rec("low", [["/w/Weak", 0.45, "Likely"]]),
      rec("high", [["/w/Strong", 0.95, "Most Likely"]]),
    ]);

    expect(groups.map((g) => g.label)).toEqual(["Strong", "Weak"]);
  });

  it("routes weak matches to Needs review instead of a folder heading", () => {
    const groups = groupRecommendations([
      rec("strong", [["/w/Horizon", 0.9, "Most Likely"]]),
      rec("weak", [["/w/Horizon", 0.2, "Possible"]]),
    ]);

    const needsReview = groups.find((g) => g.key === NEEDS_REVIEW_KEY);
    expect(needsReview?.recommendations.map((r) => r.id)).toEqual(["weak"]);
    expect(needsReview?.folder).toBeNull();
  });

  it("keeps Needs review last even when it is the largest group", () => {
    const groups = groupRecommendations([
      rec("w1", [["/w/A", 0.1, "Possible"]]),
      rec("w2", [["/w/B", 0.1, "Possible"]]),
      rec("ok", [["/w/Horizon", 0.9, "Most Likely"]]),
    ]);

    expect(groups[groups.length - 1].key).toBe(NEEDS_REVIEW_KEY);
  });

  it("treats a recommendation with no candidates as needing review", () => {
    const groups = groupRecommendations([rec("empty", [])]);

    expect(groups).toHaveLength(1);
    expect(groups[0].key).toBe(NEEDS_REVIEW_KEY);
  });

  it("counts only confident matches in the group summary", () => {
    const groups = groupRecommendations([
      rec("a", [["/w/Horizon", 0.9, "Most Likely"]]),
      rec("b", [["/w/Horizon", 0.45, "Likely"]]),
    ]);

    expect(groups[0].recommendations).toHaveLength(2);
    expect(groups[0].confidentCount).toBe(1);
  });

  it("returns no groups for an empty list", () => {
    expect(groupRecommendations([])).toEqual([]);
  });
});
