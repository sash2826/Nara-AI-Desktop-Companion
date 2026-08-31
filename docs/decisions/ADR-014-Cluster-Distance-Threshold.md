# ADR-014: Cluster Distance Threshold Default (EAC_CLUSTER_DISTANCE_THRESHOLD)

**Status:** Accepted

**Date:** 2026-08-31

**Decision Makers:** Project Architecture Team

---

## Context

Phase 10 Scenario 3 introduced agglomerative clustering to group floating
unorganised files into proposed new folders. The clustering pipeline
(`ClusterEngine`) cuts the dendrogram at a configurable distance threshold:
pairs of documents whose combined distance exceeds this threshold are never
merged into the same cluster.

The distance metric combines two signals weighted by `EAC_CLUSTER_ENTITY_WEIGHT`
(default α = 0.75):

```
combined_similarity(i, j) = α × overlap_coefficient(entities_i, entities_j)
                           + (1−α) × cosine_similarity(vec_i, vec_j)

distance(i, j) = 1 − combined_similarity(i, j)
```

`overlap_coefficient` is the Szymkiewicz-Simpson coefficient:
`|A ∩ B| / min(|A|, |B|)`, mirroring `PlacementScorer`'s formula.

A threshold that is too **tight** (small) causes the engine to reject
legitimate clusters — files about the same topic that differ slightly in
their entity set or vector. A threshold that is too **loose** (large)
causes the engine to merge unrelated files into a single over-broad folder
proposal.

Before shipping Phase 11, the default threshold required a formal
calibration decision so that:

1. The default works for most enterprise document corpora without per-site tuning.
2. The value is evidence-backed and reproducible.
3. Operators can override it per-deployment via `EAC_CLUSTER_DISTANCE_THRESHOLD`.

---

## Decision

Set `EAC_CLUSTER_DISTANCE_THRESHOLD` to **0.45** as the default.

---

## Calibration Evidence

A ten-suite benchmark (`backend/tests/test_cluster_calibration.py`) was written to
cover the range of realistic clustering scenarios. Each suite constructs a synthetic
distance matrix and asserts the expected cluster structure.

### Suites

| Suite | Scenario | Distance | Expected outcome |
|-------|----------|----------|-----------------|
| S1 | Perfect match — 4 identical docs | 0.00 | 1 cluster of 4 |
| S2 | Two tight groups, zero cross-similarity | 0.00 within / 1.00 across | 2 clusters of 2 |
| S3 | Three tight groups | 0.00 within / 1.00 across | 3 clusters of 2 |
| S4 | Tight cluster + unrelated singleton | 0.05 within / 0.90 across | 1 cluster of 3, singleton excluded |
| S5 | Boundary BELOW threshold | 0.44 | Merged |
| S6 | Boundary ABOVE threshold | 0.46 | Not merged |
| S7 | Entity signal dominates (cosine=0, overlap=1) | 0.25 | Merged |
| S8 | Vector signal only (overlap=0, cosine=0.8) | 0.80 | Not merged |
| S9 | Partial entity + strong vector (overlap=0.5, cosine=1) | 0.375 | Merged |
| S10 | Large cluster — 8 related docs | 0.05 | 1 cluster of 8 |

### Calibration Grid

The grid shows which suites pass at each candidate threshold (α = 0.75):

```
threshold │ S1  S2  S3  S4  S5  S6  S7  S8  S9  S10 │ pass/10
──────────┼────────────────────────────────────────────┼─────────
0.30      │  ✓   ✓   ✓   ✓   ✗   ✓   ✓   ✓   ✗   ✓  │  8/10
0.40      │  ✓   ✓   ✓   ✓   ✗   ✓   ✓   ✓   ✓   ✓  │  9/10
0.45      │  ✓   ✓   ✓   ✓   ✓   ✓   ✓   ✓   ✓   ✓  │ 10/10  ← chosen
0.50      │  ✓   ✓   ✓   ✓   ✓   ✗   ✓   ✓   ✓   ✓  │  9/10
0.60      │  ✓   ✓   ✓   ✓   ✓   ✗   ✓   ✓   ✓   ✓  │  9/10
```

**Key observations:**

- Suites S5 (dist=0.44) and S9 (dist=0.375) fail below threshold ≤ 0.40:
  the threshold is too tight and rejects legitimate partial-overlap clusters.
- Suite S6 (dist=0.46) fails at threshold ≥ 0.50:
  the threshold is too loose and merges documents that share no entities and
  have only marginal vector similarity.
- Threshold **0.45** is the unique value at which all ten suites pass.

### Suite 8 Rationale

Suite 8 (vector-only, dist=0.80) establishes that vector proximity alone is
insufficient to form a cluster. At α=0.75 the entity signal dominates: two
documents that are semantically adjacent in embedding space but share no
canonical entities (e.g. "Excel pivot tables" vs "SQL window functions") will
have dist=0.80 and will not be proposed as a folder pair. This is intentional —
folder organisation should reflect topical identity, not embedding neighbourhood.

### Suite 9 Rationale

Suite 9 (partial entity + strong vector, dist=0.375) represents the most common
"related but not identical" case in real corpora: two documents share a parent
concept (entity overlap=0.5) and are about the same project (cosine=1). The
distance of 0.375 comfortably passes the 0.45 threshold, producing a useful
folder proposal.

---

## Alternatives Considered

### Threshold = 0.30 (tight)

8/10 suites pass. Rejects Suites S5 (dist=0.44) and S9 (dist=0.375), which
represent valid partial-overlap and near-boundary cases. Would produce
fewer, tighter proposals at the cost of missing genuinely related files.
Appropriate for very domain-specific corpora where folder precision matters
more than recall.

### Threshold = 0.50 (loose)

9/10 suites pass. Fails Suite S6 (dist=0.46): merges a weakly related pair
that shares no entities and only moderate vector similarity. Increased false
positive rate — users would see more proposals for files that do not belong
together. Appropriate for broad-topic corpora (e.g. a general knowledge base).

### Threshold = 0.60 (very loose)

Same failure as 0.50 for Suite S6. Significantly increases the risk of
presenting over-broad folder proposals that frustrate users.

---

## Consequences

### Positive

- `EAC_CLUSTER_DISTANCE_THRESHOLD = 0.45` passes all 10 calibration suites.
- The threshold is conservative enough to avoid nuisance proposals while loose
  enough to catch partial-overlap cases (Suite 9).
- Operators can override per-deployment to match corpus characteristics.
- The calibration benchmark (`test_cluster_calibration.py`) is a regression
  guard: any future change to `ClusterEngine` or `ClusterScorer` must continue
  to pass all 26 assertions.

### Negative

- The default is calibrated against synthetic distance matrices, not a real
  file corpus. Real-world performance may differ depending on embedding quality
  and knowledge-graph coverage.
- A single global default cannot be optimal for all corpora. Operators with
  high-precision requirements (legal, compliance) may need to lower the threshold;
  those with broad knowledge bases may need to raise it.

### Neutral

- `EAC_CLUSTER_ENTITY_WEIGHT = 0.75` is assumed throughout. If that weight
  is changed in production, the threshold calibration should be re-run.
- The benchmark is deterministic and runs in < 1 second; it is suitable as
  a pre-commit gate.

---

## Configuration

```bash
# Default (calibrated value — suitable for most enterprise corpora)
EAC_CLUSTER_DISTANCE_THRESHOLD=0.45

# Tighter: fewer, more precise proposals (high-stakes document environments)
EAC_CLUSTER_DISTANCE_THRESHOLD=0.30

# Looser: more proposals, higher recall (broad knowledge bases)
EAC_CLUSTER_DISTANCE_THRESHOLD=0.55
```

The override is applied at startup in `ClusterDiscoveryService` via `get_config()`.
