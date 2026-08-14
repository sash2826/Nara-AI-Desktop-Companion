# Deferred Features

## Passive Background Suggester (Phase 10 deferral)

**Decision date:** 2026-08-14  
**Deferred from:** Phase 10 — File Organisation: Existing Files

### What was deferred

The passive background suggester would, after each file is indexed, sample a small random cluster of peer documents and score them against candidate folders. Any file scoring above the threshold would have a placement recommendation created automatically — without the user explicitly running an audit.

### Why it was deferred

The on-demand "Organise" audit covers the primary use case without introducing background churn. The passive suggester adds complexity (sampling strategy, rate-limiting, interaction with the existing Downloads watcher) that is better addressed once the on-demand flow has been validated in real use.

### Preferred future implementation

When revisited, the passive suggester should:

1. Trigger from `FileIndexer.index_file()` post-hook (similar to the Downloads recommendation hook).
2. Sample a configurable number of peer documents from the same workspace folder.
3. Score only the sampled peers — not a full corpus scan — to keep latency low.
4. Reuse `PlacementScorer.score_all()` and `RecommendationRepository.create()` unchanged.
5. Gate on a user setting (opt-in) to avoid unwanted background activity.
