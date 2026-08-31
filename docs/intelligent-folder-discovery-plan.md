# Intelligent Folder Discovery — Revised Implementation Plan
## Post-Review Edition

> This document supersedes the original plan after a codebase-grounded review
> of all 12 areas specified. Every claim below is traceable to an actual source
> file read during the review session.

---

## Review Corrections Summary

| Area | Original plan | Corrected finding |
|---|---|---|
| Migration | Needed Qdrant payload update + graph source_path update | `FileMover` comment: "Qdrant payload does NOT store document_path directly." Only SQLite `documents` needs updating. `FileMover` already handles this correctly. |
| Migration | Custom rollback implementation | `FileMover` already exists with conflict strategies. Reuse it. |
| Clustering | Agglomerative Ward + cosine | Ward assumes Euclidean geometry. Correct: average linkage + cosine (metric-agnostic). Ward is only defensible for L2-normalized embeddings (BGE-M3 is, but average is more principled). |
| Graph integration | Post-clustering validation only | Entity overlap can be a clustering INPUT via combined similarity matrix. Architecturally natural given existing `SqliteGraphScoreAdapter`. |
| Module placement | New sibling capability `cluster_discovery/` | Belongs inside existing `organisation/` module. `FileMover`, `PlacementScorer`, floating-file heuristics are already there. |
| Guard threshold | Arbitrary 0.55 | Use existing calibrated `_SCORE_STRONG_THRESHOLD = 0.60` from `placement_scorer.py`. |
| Folder naming | LLM for every cluster | Deterministic naming from entity signals first. LLM only as fallback when deterministic output fails validation. |
| Floating file definition | Shallow copy of AuditService | Must be more precise. Extract into a shared `FloatingFileFilter` so AuditService and ClusterDiscoveryService share the same rules. |
| Rule 8 — floating zone logic | "Parent IS an ancestor of a known leaf subfolder" | **Broken for flat workspaces** (zero subfolders). When `Documents/` has no subfolders, `get_known_folder_paths()` returns `["Documents/"]` as the only leaf — making the ancestor condition impossible to satisfy and producing zero candidates. Replaced with a three-tier rule (see Part 5). |
| Proposal gate | Not defined — any cluster ≥ size 2 became a proposal | **Missing**. Threshold-crossing is not sufficient evidence. Added five-criterion gate: tightness floor, size-2 tightness floor, entity overlap floor, entity token count, ambiguity cap. LOW confidence suppressed entirely (no card). See Part 3.4 and step 6 of data flow. |
| Cloud AI | Assumed entity names are safe to send | Must confirm with data governance before LLM naming path is enabled. Entity names are lower-risk than content but require explicit sign-off. |

---

## Part 1 — Revised Architecture

### 1.1 Module Placement

The feature belongs **inside the existing `organisation/` module**, not as a sibling capability.

Rationale:
- `FileMover` is already correct for the migration step. Reuse it unchanged.
- `PlacementScorer` provides the existing-folder guard. Reuse it unchanged.
- `AuditService` has floating-file heuristics that must become shared. Extract them rather than duplicate.
- All three scenarios share the same conceptual domain: "where does this file go?"

```
backend/src/enterprise_ai_companion/
└── capabilities/
    └── organisation/                ← extend this module
        ├── placement_scorer.py      ← unchanged
        ├── placement_ports.py       ← unchanged
        ├── placement_adapters.py    ← unchanged
        ├── audit_service.py         ← refactored to use FloatingFileFilter
        ├── file_mover.py            ← unchanged, REUSED for migration
        ├── recommendation_repository.py  ← unchanged
        ├── recommendation_service.py     ← unchanged
        ├── affinity_repository.py        ← unchanged
        │
        ├── floating_file_filter.py      ← NEW: extracted from audit_service
        ├── document_vector_service.py   ← NEW
        ├── cluster_scorer.py            ← NEW: pairwise similarity matrix
        ├── cluster_engine.py            ← NEW: agglomerative clustering
        ├── cluster_proposal_repository.py  ← NEW
        └── cluster_discovery_service.py    ← NEW: pipeline orchestrator

backend/src/enterprise_ai_companion/api/routers/
└── organisation.py              ← extend with 6 new endpoints

database/migrations/
└── 0XX_cluster_proposals.sql   ← NEW
```

Frontend: `ClusterProposalCard.tsx`, `ClusterReviewDrawer.tsx` (new), extend `OrganiseDashboard.tsx` and `IPCClient.ts`.

---

### 1.2 Revised Data Flow

```
POST /organisation/discover-clusters
        ↓
ClusterDiscoveryService.run()
        │
        ├─ 1. IDENTIFY FLOATING CANDIDATES
        │      DocumentRepository.list_all()
        │      FloatingFileFilter.filter(docs)  ← shared with AuditService
        │        Rules applied in order:
        │        a. Exclude Downloads folder
        │        b. Exclude personal filename tokens (_PERSONAL_FILENAME_TOKENS)
        │        c. Exclude temp/lock file prefixes (_IGNORED_PREFIXES)
        │        d. Exclude EXCLUDED_DIRS and _BLOCKED_ROOTS
        │        e. Exclude EAC_SYSTEM_INDEX_PATHS
        │        f. Exclude files with active pending recommendation
        │        g. FLOATING = file whose parent satisfies at least ONE of:
        │             (a) WORKSPACE ROOT TIER: parent is a watched workspace
        │                 root registered with WatcherService. Workspace roots
        │                 are always floating zones regardless of whether
        │                 subfolders exist. Handles flat workspaces (Case A).
        │             (b) ANCESTOR TIER: parent is NOT in get_known_folder_paths()
        │                 (was pruned as an ancestor of real leaf subfolders).
        │                 File sits in a root/dump zone within an hierarchy.
        │             (c) DUMP FOLDER TIER: parent IS in get_known_folder_paths()
        │                 but its name matches DUMP_FOLDER_NAMES.
        │           Files in a non-dump leaf folder are NOT floating candidates
        │           — they belong to AuditService / Scenario 2.
        │
        ├─ 2. EXISTING FOLDER GUARD
        │      For each floating candidate:
        │        PlacementScorer.score_all() — single call, all known leaf
        │        folders, normalised scale within the call.
        │        Files scoring ≥ _SCORE_STRONG_THRESHOLD (0.60) against any
        │        existing folder → emit Scenario 2 recommendation instead.
        │        Only files with no strong existing match proceed.
        │
        ├─ 3. DOCUMENT VECTOR AGGREGATION
        │      DocumentVectorService.get_document_vectors(doc_ids)
        │      Qdrant payload: chunk_id, document_id, chunk_index (no file_path)
        │      SQLite chunks → batch fetch vectors via QdrantClient
        │      Mean-pool per document → 1024-dim float32 vector
        │
        ├─ 4. COMBINED SIMILARITY MATRIX
        │      ClusterScorer.build_matrix(doc_vectors, entity_sets)
        │      combined_sim(i,j) = α × cosine_sim(i,j)
        │                        + (1-α) × entity_overlap(i,j)
        │      α = configurable (EAC_CLUSTER_ENTITY_WEIGHT, default 0.75)
        │      entity_overlap = Szymkiewicz-Simpson on canonical names
        │        minus _GENERIC_TERMS (reused from placement_scorer.py)
        │      Sparse docs: entity_overlap → 0 → combined → cosine naturally
        │      Batch-fetch all entity sets once before matrix build (not O(n²) queries)
        │
        ├─ 5. AGGLOMERATIVE CLUSTERING
        │      ClusterEngine.cluster(distance_matrix, distance_threshold, min_cluster_size)
        │      distance = 1 − combined_sim
        │      Linkage: AVERAGE (metric-agnostic; correct for cosine distances)
        │      distance_threshold: configurable (EAC_CLUSTER_DISTANCE_THRESHOLD)
        │        MUST be calibrated via benchmark — no default shipped without calibration
        │      min_cluster_size=2: single doc cannot justify a new folder
        │      Outliers: docs not merging at threshold → silently left in place
        │      Ambiguous: within EAC_CLUSTER_AMBIGUITY_MARGIN of two centroids → flagged
        │
        ├─ 6. PROPOSAL GATE + CONFIDENCE ASSIGNMENT
        │      For each raw cluster from step 5, compute:
        │
        │        tightness           = mean combined_sim across all member pairs
        │        mean_entity_overlap = mean Szymkiewicz-Simpson across all pairs
        │                              (using graph entity sets, minus _GENERIC_TERMS)
        │        specific_entity_count = count of distinct non-generic entity tokens
        │                                appearing in ≥ 2 cluster members
        │        ambiguous_fraction  = (ambiguous-flagged members) / cluster_size
        │
        │      SUPPRESS (no proposal) if ANY of:
        │        a. tightness < _PROPOSAL_TIGHTNESS_MIN (0.45)
        │        b. size == 2 AND tightness < _PROPOSAL_TIGHTNESS_MIN_PAIR (0.55)
        │        c. mean_entity_overlap < _PROPOSAL_ENTITY_OVERLAP_MIN (0.08)
        │        d. specific_entity_count < _PROPOSAL_ENTITY_TOKENS_MIN (2)
        │        e. ambiguous_fraction > _PROPOSAL_AMBIGUITY_MAX (0.50)
        │
        │      Suppressed clusters: members silently left in place (same as outliers).
        │      Count tracked and returned for the UI summary line.
        │
        │      Confidence level (passed clusters only):
        │        HIGH   if ALL: size ≥ 4
        │                   AND mean_entity_overlap ≥ 0.15
        │                   AND tightness ≥ 0.55
        │                   AND ambiguous_fraction ≤ 0.20
        │        MEDIUM if passed gate but any HIGH criterion not met
        │        LOW    → does not exist as a proposal level (see gate above)
        │
        ├─ 7. FOLDER NAME GENERATION
        │      FolderNamingService.name_cluster(cluster, existing_folder_names)
        │      → Deterministic first; LLM only on deterministic validation failure
        │      (see Part 6)
        │
        └─ 8. PERSIST + RETURN
               ClusterProposalRepository.create_proposals(clusters)
               Return: List[ClusterProposalResponse]

POST /organisation/cluster-proposals/{id}/accept
        ↓
        ├─ Validate all member files still exist on disk
        ├─ os.makedirs(target_folder, exist_ok=False)
        ├─ For each member: FileMover.move(source, target, conflict_strategy="error")
        │    FileMover handles: shutil.move + SQLite UPDATE (file_path + workspace_path)
        │    NO Qdrant update needed (payload has no file_path)
        │    NO graph_entities update needed (FK is source_document_id UUID, not path)
        │    Track moved files for manual rollback on partial failure
        ├─ ClusterProposalRepository.accept(proposal_id)
        └─ Emit "files-moved" IPC event
```

---

## Part 2 — Revised Component List

### Backend — New files

| File | Purpose |
|---|---|
| `organisation/floating_file_filter.py` | Single source of truth for floating file inclusion/exclusion. Extracted from `AuditService._run()`. |
| `organisation/document_vector_service.py` | Fetch Qdrant chunk embeddings per document; mean-pool to doc vector. |
| `organisation/cluster_scorer.py` | Build pairwise combined similarity matrix (embedding + entity overlap). |
| `organisation/cluster_engine.py` | scipy agglomerative clustering; outlier and ambiguity detection. |
| `organisation/cluster_proposal_repository.py` | CRUD for `cluster_proposals` + `cluster_proposal_members`. |
| `organisation/cluster_discovery_service.py` | Pipeline orchestrator. |
| `database/migrations/0XX_cluster_proposals.sql` | Schema. |

### Backend — Modified files

| File | Change |
|---|---|
| `organisation/audit_service.py` | Replace inline floating-file filter with `FloatingFileFilter.filter()` |
| `api/routers/organisation.py` | 6 new endpoints |
| `api/app.py` | Inject `ClusterDiscoveryService` |

### Frontend — New files

`ClusterProposalCard.tsx`, `ClusterReviewDrawer.tsx`

### Frontend — Modified files

`OrganiseDashboard.tsx` (add Discover Folders section), `IPCClient.ts` (6 new wrappers), state management (cluster proposals store).

---

## Part 3 — Revised Clustering Strategy

### 3.1 Algorithm Comparison

| Algorithm | No K | Natural outliers | Cosine correct | 10–500 docs | New deps | Verdict |
|---|---|---|---|---|---|---|
| Agglomerative + **average linkage** | ✓ | ✓ | ✓ metric-agnostic | ✓ | scipy | **Recommended** |
| Agglomerative + Ward | ✓ | ✓ | ⚠️ Euclidean only (OK if L2-norm) | ✓ | scipy | Acceptable but less principled |
| Agglomerative + complete | ✓ | ✓ | ✓ | ✓ | scipy | Tends to elongated clusters |
| HDBSCAN | ✓ | ✓ | ✓ | ✓ | hdbscan | Good; adds one dependency |
| Similarity graph + community | ✓ | ✓ | ✓ | ⚠️ <300 | networkx | Future upgrade path |
| K-means / DBSCAN | — | — | — | — | — | Ruled out |

**Decision: Agglomerative with average linkage.**

Average linkage is metric-agnostic and mathematically correct for cosine distance. Ward minimizes within-cluster Euclidean variance; although BGE-M3 vectors ARE L2-normalized (making Ward on them equivalent to Ward on angular distance), average linkage is more principled and equally capable with scipy. HDBSCAN is the recommended upgrade path if the corpus regularly exceeds 500 documents.

### 3.2 Combined Similarity Matrix

```
combined_sim(doc_i, doc_j) = α × cosine_sim(emb_i, emb_j)
                            + (1-α) × entity_overlap(entities_i, entities_j)
```

- `α` = `EAC_CLUSTER_ENTITY_WEIGHT` (default placeholder 0.75; must calibrate)
- `entity_overlap` = Szymkiewicz-Simpson on canonical entity sets, minus `_GENERIC_TERMS`
- Sparse documents: `entity_overlap → 0` → `combined → cosine_sim` naturally
- Batch-fetch all entity sets from SQLite before matrix construction

This is better than embedding-only because two documents can be stylistically similar (similar embedding) but topically unrelated (different entity sets). The combined signal catches this case.

### 3.3 Threshold Policy

| Parameter | Config key | Default | Calibration status |
|---|---|---|---|
| Dendrogram cut height | `EAC_CLUSTER_DISTANCE_THRESHOLD` | **None — must calibrate** | Pre-ship blocker |
| Min cluster size | `EAC_CLUSTER_MIN_SIZE` | `2` | Reasonable; validate against benchmark |
| Ambiguity margin | `EAC_CLUSTER_AMBIGUITY_MARGIN` | `0.08` | Placeholder; calibrate against Suite 3 |
| Entity weight α | `EAC_CLUSTER_ENTITY_WEIGHT` | `0.75` | Placeholder; calibrate against Suite 1 |
| **Existing-folder guard** | — | **`0.60`** (`_SCORE_STRONG_THRESHOLD`) | **Already calibrated** — reuse as-is |

Pre-ship calibration requirement: run benchmark Suites 1–2 at `EAC_CLUSTER_DISTANCE_THRESHOLD` values 0.20, 0.25, 0.30, 0.35, 0.40. Choose the value maximizing cluster purity while keeping over-clustering rate ≤ 1.3. Document the chosen value in an ADR.

### 3.4 Proposal Gate Constants

Passing the distance threshold is necessary but not sufficient to produce a proposal. The proposal gate is a secondary evidence check applied after clustering (step 6 of the data flow). These constants are calibrated separately from the clustering threshold.

| Constant | Default | Description |
|---|---|---|
| `_PROPOSAL_TIGHTNESS_MIN` | `0.45` | Minimum mean pairwise combined_sim for any cluster |
| `_PROPOSAL_TIGHTNESS_MIN_PAIR` | `0.55` | Minimum combined_sim for a size-2 cluster (the single pair must be strongly related) |
| `_PROPOSAL_ENTITY_OVERLAP_MIN` | `0.08` | Minimum mean entity overlap across all pairs (semantic coherence floor) |
| `_PROPOSAL_ENTITY_TOKENS_MIN` | `2` | Minimum count of distinct non-generic entity tokens shared by ≥ 2 members |
| `_PROPOSAL_AMBIGUITY_MAX` | `0.50` | Maximum fraction of ambiguous-flagged members |
| `_PROPOSAL_HIGH_SIZE` | `4` | Minimum size for HIGH confidence |
| `_PROPOSAL_HIGH_ENTITY_OVERLAP` | `0.15` | Minimum mean entity overlap for HIGH confidence |
| `_PROPOSAL_HIGH_TIGHTNESS` | `0.55` | Minimum tightness for HIGH confidence |
| `_PROPOSAL_HIGH_AMBIGUITY_MAX` | `0.20` | Maximum ambiguous fraction for HIGH confidence |

**Why the size-2 tightness rule is separate from `_PROPOSAL_TIGHTNESS_MIN`:**
With 2 members, mean_pairwise_sim equals the single pair's similarity. A 2-document cluster is the thinnest possible evidence basis for a permanent folder — it requires the pair to be strongly related (0.55), not just above the general tightness floor (0.45). Without this rule, every threshold-crossing pair would become a proposal.

**What "suppressed" means operationally:**
A suppressed cluster's members are treated identically to outliers: they stay in place, are not surfaced in the UI as proposals, and are not moved. The only UI trace is the summary count ("N clusters suppressed; X files remain unorganized"). This is a success state, not a failure.

---

## Part 4 — Revised Graph / RAG Integration

The knowledge graph is used in **three** roles, not one:

**Role 1 — Clustering INPUT** (`ClusterScorer`):
Entity overlap is the `(1-α)` term in `combined_sim`. Documents sharing rare domain-specific entities are attracted to each other beyond what embedding similarity provides. Uses `SqliteGraphScoreAdapter.get_canonicals_for_document()` — existing, tested, no changes.

**Role 2 — Cluster cohesion VALIDATION** (`ClusterEngine`, post-clustering):
Mean entity overlap across all member pairs within a cluster. Produces the confidence label (High / Medium / Low). Catches clusters that are embedding-similar but topically unrelated (low overlap → Low confidence).

**Role 3 — Folder name SIGNAL** (`FolderNamingService`):
Canonical entity names ranked by frequency across cluster members are the primary deterministic naming input. `_GENERIC_TERMS` filter applied (reused from `placement_scorer.py`). `filename_keywords()` and `filename_bigrams()` from `placement_ports.py` supplement sparse documents.

RAG infrastructure (`HybridRerankAdapter`) is used only by the existing-folder guard via `PlacementScorer.score_all()`. Unchanged.

---

## Part 5 — Revised Floating File Definition

### Precise Definition

A document is a **floating file candidate** if and only if ALL of the following hold:

1. Present in `DocumentRepository` (is indexed)
2. Not under `Path.home() / "Downloads"`
3. Filename stem has no `_PERSONAL_FILENAME_TOKENS` tokens
4. Filename does not match `_IGNORED_PREFIXES` (temp/lock files: `~$`, etc.)
5. Not under any path in `EXCLUDED_DIRS` or `_BLOCKED_ROOTS`
6. Not under any path in `EAC_SYSTEM_INDEX_PATHS`
7. No active pending recommendation in `RecommendationRepository`
8. **Parent directory is a floating zone** — at least ONE of the following three tiers must hold:

   **(a) Workspace root tier**: The parent is a watched workspace root registered with `WatcherService` (a path directly added by the user for indexing). Workspace roots are always floating zones regardless of whether subfolders exist under them. **This is the fix for flat workspaces**: when `Documents/` has 30 files and zero subfolders, `get_known_folder_paths()` returns `["Documents/"]` as its only leaf — making the original ancestor condition impossible to satisfy. Under the revised rule, `Documents/` IS a workspace root → tier (a) triggers → all 30 files are candidates.

   **(b) Ancestor tier**: The parent is NOT in `get_known_folder_paths()` results — meaning it was pruned as an ancestor of deeper leaf subfolders. The file sits in a root/dump zone within an existing organizational hierarchy. Example: `Documents/report.pdf` where `Documents/Finance/` and `Documents/HR/` exist → `Documents/` is pruned from the leaf set → tier (b) triggers → file is floating.

   **(c) Dump folder tier**: The parent IS in `get_known_folder_paths()` but its folder name (case-insensitive stem) matches `DUMP_FOLDER_NAMES`. Example: `Documents/Misc/budget.pdf` → `Misc` is in the dump set → tier (c) triggers → file is floating.

Rule 8 decisions:
- `Documents/report.pdf` (no subfolders) → tier (a) workspace root → **floating** ✓
- `Documents/report.pdf` (Finance/, HR/ exist) → tier (b) ancestor → **floating** ✓
- `Documents/Finance/budget.xlsx` → not (a), not (b), Finance is not a dump name → **NOT floating** → Scenario 2 ✓
- `Documents/Misc/notes.docx` → `Misc` in DUMP_FOLDER_NAMES → tier (c) → **floating** ✓
- `Documents/Project Phoenix/spec.docx` → not (a), not (b), not (c) → **NOT floating** → Scenario 2 ✓

### FloatingFileFilter

```python
class FloatingFileFilter:
    """Single source of truth for floating file candidate rules.

    Used by both AuditService (Scenario 2) and ClusterDiscoveryService (Scenario 3)
    so the exclusion logic is never duplicated.

    Requires workspace_roots: the set of watched folder paths from WatcherService,
    used for the workspace-root tier of Rule 8 (tier a).
    """
    DUMP_FOLDER_NAMES: frozenset[str] = frozenset({
        "misc", "miscellaneous", "temp", "temporary", "tmp", "unsorted",
        "new folder", "various", "other", "general", "dump", "inbox",
        "staging", "to sort", "random", "junk", "files", "stuff",
    })

    def __init__(self, workspace_roots: set[str], ...) -> None: ...

    async def get_candidates(self) -> list[IndexedDocument]: ...

    def _is_floating_zone(self, file_path: str, leaf_folders: set[str]) -> bool:
        parent = str(Path(file_path).parent.resolve())
        # Tier (a): workspace root
        if parent in self._workspace_roots:
            return True
        # Tier (b): ancestor — not in leaf set
        if parent not in leaf_folders:
            return True
        # Tier (c): dump folder name
        if Path(parent).name.lower() in self.DUMP_FOLDER_NAMES:
            return True
        return False
```

`FloatingFileFilter` receives `workspace_roots` injected at construction from `WatcherService.get_watched_paths()`. This is the only new dependency relative to the original plan.

`AuditService` is refactored in Phase A to call `FloatingFileFilter.get_candidates()` instead of its current inline filtering. No change to audit behaviour — only extraction.

---

## Part 6 — Revised Folder Naming Strategy

### Deterministic first; LLM as fallback only

```
Step 1 — Collect entity signals:
  - SqliteGraphScoreAdapter.get_canonicals_for_document() for each member
  - Union all canonical names; rank by frequency (member count)
  - Filter _GENERIC_TERMS (reused from placement_scorer.py)
  - Supplement with filename_keywords() from placement_ports.py

Step 2 — Detect existing naming convention:
  - Sample from PlacementScorer.discover_candidate_folders()
  - Detect: Title Case / ALL CAPS / YYYY - Name / Name - Category / kebab-case

Step 3 — Build deterministic candidate name:
  - Top 1–3 ranked non-generic entities
  - Apply detected naming convention

Step 4 — Validate:
  - Not identical to any existing folder
  - Not composed entirely of _GENERIC_TERMS
  - Length ≤ 40 characters
  - Contains ≥ 1 token from a cluster member entity set
  - Not a single overly common word (block: "Data", "Files", "Documents")

Step 5 — Accept deterministic name if valid.
  Most clusters should pass without ever calling the LLM.

Step 6 — LLM ONLY if step 4 fails:
  Input: top-10 entity names + sample existing folder names
  No document content. No file paths.
  Validate LLM output with same step 4 rules.
  On second failure: entity concatenation fallback ("Entity A & Entity B")
```

### Cloud AI / Privacy Model

What is already sent to the GenAI Hub APIM today:
- Document chunk text (entity extraction, during indexing)
- Conversation messages + retrieved context chunks (Chat)

For LLM naming fallback:
- Sends: top-10 canonical entity names + existing folder name samples
- Does NOT send: document content, file paths, user-identifiable data
- Canonical entity names were originally produced BY the LLM (entity extraction). Sending them back is logically consistent and lower-risk than document content.

**Pre-ship blocker:** Obtain explicit data governance confirmation that sending entity names and folder name strings to the Volvo GenAI Hub APIM is acceptable. Track as a release-blocking issue.

**Kill switch:** `EAC_CLUSTER_NAMING_LLM_ENABLED=false` — disables all LLM calls. Deterministic naming and entity-concatenation fallback remain active.

---

## Part 7 — Revised Migration Architecture

### What State Actually Depends on File Path

Verified by reading `file_mover.py`, `chunk_repository.py`, `placement_adapters.py`:

| Store | Path-dependent field | Action on file move |
|---|---|---|
| SQLite `documents` | `file_path`, `workspace_path` | **UPDATE both** — FileMover already does this |
| SQLite `chunks` | FK `document_id` only | **No action needed** |
| SQLite `chunks_fts` | FK `chunk_id` only | **No action needed** |
| SQLite `graph_entities` | FK `source_document_id` (UUID) | **No action needed** — references doc UUID, not path |
| SQLite `graph_relationships` | FK entity IDs | **No action needed** |
| Qdrant | `chunk_id`, `document_id`, `chunk_index` | **No action needed** — FileMover comment explicitly confirms this |

The original plan was wrong on two counts: Qdrant needs no update, and graph_entities needs no update.

### Migration Implementation

`FileMover` already handles everything correctly. The accept handler uses it directly:

```python
async def _accept_proposal(proposal, file_mover, proposal_repo):
    # Pre-validate all files exist before touching filesystem
    missing = [m for m in proposal.members if not Path(m.file_path).exists()]
    if missing:
        raise FileNotFoundError(...)

    dest = Path(proposal.target_folder_path)
    dest.mkdir(parents=False, exist_ok=False)  # fail if already exists

    moved: list[tuple[str, str]] = []
    try:
        for member in proposal.members:
            new_path = await file_mover.move(
                member.file_path, str(dest), conflict_strategy="error"
            )
            moved.append((member.file_path, new_path))
    except Exception:
        # Best-effort rollback — FileMover is not transactional
        for original, moved_to in reversed(moved):
            shutil.move(moved_to, original)
            await file_mover.move(moved_to, str(Path(original).parent), ...)
        if dest.exists() and not any(dest.iterdir()):
            dest.rmdir()
        raise

    await proposal_repo.accept(proposal.id)
```

**Known limitation:** `FileMover.move()` is not atomically reversible (filesystem and SQLite are separate operations). The rollback above is best-effort. A production-quality improvement would add a `move_with_savepoint()` to `FileMover` that wraps the SQLite update in a savepoint. Document as a known limitation in Phase G; address in Phase 11 (Polish).

---

## Part 8 — Schema

```sql
-- 0XX_cluster_proposals.sql

CREATE TABLE IF NOT EXISTS cluster_proposals (
    id                 TEXT PRIMARY KEY,
    folder_name        TEXT NOT NULL,
    target_folder_path TEXT NOT NULL DEFAULT '',
    created_at         TEXT NOT NULL,
    status             TEXT NOT NULL DEFAULT 'pending',
    confidence         TEXT NOT NULL DEFAULT 'medium',
    reasoning          TEXT NOT NULL DEFAULT '',
    entity_signals     TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS cluster_proposal_members (
    proposal_id TEXT NOT NULL REFERENCES cluster_proposals(id) ON DELETE CASCADE,
    file_path   TEXT NOT NULL,
    score       REAL NOT NULL DEFAULT 0.0,
    ambiguous   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (proposal_id, file_path)
);

CREATE INDEX IF NOT EXISTS idx_cluster_proposals_status
    ON cluster_proposals(status);
CREATE INDEX IF NOT EXISTS idx_cluster_members_proposal
    ON cluster_proposal_members(proposal_id);
```

---

## Part 9 — Revised Benchmark

Ten suites covering the full variation space:

### Suite 1: Basic Discovery
50 docs, 0 existing destination folders, 4 thematic groups + 5 personal outliers.
Expected: 4 proposals, 5 outliers ungrouped.

### Suite 2: Existing Folder Preference
50 docs. 30 belong to EXISTING indexed folders (score ≥ 0.60). 15 form 2 new groups. 5 outliers.
Critical: existing-folder guard routes the 30 to Scenario 2, not Scenario 3. New clusters for the 15 only.

### Suite 2b: Proposal Gate — Weak Cluster Suppression
20 docs arranged in 3 groups: (a) 2 docs with forced weak similarity (combined_sim ≈ 0.38, shared entity overlap < 0.05), (b) 5 docs with moderate similarity but no non-generic entities, (c) 3 docs whose majority members are ambiguous between two centroids.
Expected: all three groups SUPPRESSED by the gate. Zero proposals generated. All 20 files remain in place.
This suite specifically validates that the gate does not produce proposals for weak-evidence clusters.

### Suite 3: Ambiguous / Multi-Topic Documents
20 docs. 5 clearly in group A. 5 clearly in group B. 5 spanning both. 5 true outliers.
Expected: ambiguous docs flagged with indicator. Not silently assigned.

### Suite 4: Misleading Filenames
20 docs with content that contradicts their filenames.
Expected: entity overlap and embedding override filename tokens.

### Suite 5: Semantically Related, Different Filenames
15 docs on the same topic with completely different naming styles.
Expected: content/entity signal groups them without shared filename tokens.

### Suite 6: Duplicate Versions
10 pairs of near-duplicate docs (v1, v2 of same file — different `file_hash`).
Expected: pairs cluster together; "possible duplicate" indicator shown in review drawer. No automatic deduplication.

### Suite 7: Cluster Size Extremes
One 2-doc cluster (minimum). One 20-doc cluster (large).
Expected: both handled; min_cluster_size=2 kept; large cluster not over-split.

### Suite 8: Mixed File Types
15 docs — PDF, DOCX, XLSX, PPTX — within the same semantic group.
Expected: file type does not affect clustering.

### Suite 9: Sparse Documents
10 docs with thin content (spreadsheets with column headers only).
Expected: filename bigrams compensate OR docs become outliers — both are correct.

### Suite 10: Indexing Failures / Empty Embeddings
5 docs with missing Qdrant vectors. 15 normal docs in 2 groups.
Expected: docs with missing embeddings excluded gracefully; rest cluster correctly.

### Metrics

| Metric | Target |
|---|---|
| Cluster recall | ≥ 0.85 |
| Cluster precision | ≥ 0.80 |
| Cluster purity | ≥ 0.90 |
| Outlier recall | ≥ 0.90 |
| Over-clustering rate | ≤ 1.3 |
| Naming quality (token overlap ≥ 0.5) | ≥ 0.75 |
| Existing-folder preference (Suite 2) | ≥ 0.95 |
| Ambiguity detection (Suite 3) | ≥ 0.70 |
| Misleading filename resistance (Suite 4) | ≥ 0.80 |
| Gate suppression precision (Suite 2b) | = 1.00 — all three weak groups suppressed, zero false proposals |
| Gate false-suppression rate (true clusters suppressed) | ≤ 0.15 across Suites 1, 2, 7 |

---

## Part 10 — Revised UX

### Entry point

"Discover Folders" is a collapsible section within the existing `OrganiseDashboard.tsx`, not a new tab. Minimises navigation complexity.

### Empty states (non-coverage is correct behaviour)

| Situation | Copy |
|---|---|
| No floating files | "Your floating files are already well-placed or matched to existing folders." |
| All outliers / suppressed | "No clear groups found. Your files are too varied to group meaningfully. Nothing was moved." |
| No files at all | "No floating files found. Everything is already organised." |

When clusters were found but suppressed (evidence below gate), append a secondary line rather than replacing the empty state:
> "N groups found but had insufficient evidence to create a folder. X files remain where they are."

This line is informational only. It surfaces the suppression without offering any action.

Empty state is a **success state**, not an error state. Suppressed clusters are never surfaced as actionable cards.

### Confidence badges

| Level | Badge colour | Default card state | Notes |
|---|---|---|---|
| HIGH | Green | Expanded | Size ≥ 4, tight cluster, strong entity overlap |
| MEDIUM | Amber | Collapsed | Passed gate; weaker on at least one dimension |
| LOW | — | Not shown | Suppressed; no card created |

Size-2 MEDIUM proposals display a note in `ClusterReviewDrawer`: "This proposal is based on 2 files. Consider whether a new folder is warranted."

### Cards and review flow

`ClusterProposalCard` shows folder name, confidence badge, file count, file list, [Create Folder & Move] and [Review] buttons. `ClusterReviewDrawer` shows editable folder name, full file list with checkboxes, "possible duplicate" indicators, ambiguous-file warnings, tightness and entity overlap stats (shown as a reasoning section), destination path preview.

---

## Part 11 — Revised Implementation Phases

```
Phase A — FloatingFileFilter extraction
  Extract inline filtering from AuditService._run() into floating_file_filter.py.
  Refactor AuditService to use it. All existing AuditService tests must still pass.
  No new feature. Low risk. Does not change audit behaviour.

Phase B — DocumentVectorService
  Fetch chunk embeddings from Qdrant, mean-pool per document.
  Tests: unit with mock Qdrant.
  Dependencies: QdrantClient (existing), ChunkRepository (existing).

Phase C — ClusterScorer
  Build combined similarity matrix.
  Tests: verify entity_overlap weight, _GENERIC_TERMS filtering, sparse-doc degradation.
  Dependencies: Phase B, SqliteGraphScoreAdapter (existing).

Phase D — ClusterEngine
  Agglomerative clustering, average linkage.
  New dependency: scipy.
  Tests: synthetic 3-class vectors, outlier detection, ambiguity flagging.

Phase E — Schema + ClusterProposalRepository
  SQL migration + CRUD.
  Tests: CRUD round-trips; auto-dismiss on member removal below min_cluster_size.

Phase F — FolderNamingService
  Deterministic naming; LLM fallback (guarded by EAC_CLUSTER_NAMING_LLM_ENABLED).
  Tests: generic rejection, convention detection, fallback, LLM fallback path.
  GATE: data governance confirmation required before LLM path can ship enabled.

Phase G — ClusterDiscoveryService + API
  Pipeline orchestrator; REST endpoints.
  Integration tests with Suite 1 + Suite 2.
  Dependencies: A, B, C, D, E, F.

Phase H — Frontend
  ClusterProposalCard, ClusterReviewDrawer, OrganiseDashboard extension.
  Vitest component tests.
  Dependencies: Phase G.

Phase I — Benchmark Calibration (PRE-RELEASE BLOCKER)
  Run all 10 suites.
  Calibrate EAC_CLUSTER_DISTANCE_THRESHOLD, EAC_CLUSTER_ENTITY_WEIGHT.
  Document final values + benchmark scores in an ADR.
  No release without passing all 9 metrics at their targets.
```

Parallel start: B, D, and E have no inter-dependencies. Start all three after A completes.
C depends on B. F can start any time (only needs entities, not clustering). G is the integration gate.

---

## Part 12 — Decisions That Are FINAL

These are confirmed by the actual codebase and do not require experimentation:

1. **Migration uses `FileMover` as-is.** Only SQLite `documents` updated on move. No Qdrant update. No graph_entities update. Source: `file_mover.py` comment + `chunk_repository.py` Qdrant payload inspection.

2. **Existing-folder guard uses `_SCORE_STRONG_THRESHOLD = 0.60`.** Already calibrated against real benchmark data. Do not invent a new threshold.

3. **Module lives inside `organisation/`.** Not a sibling capability.

4. **`FloatingFileFilter` is the single source of truth.** Both `AuditService` and `ClusterDiscoveryService` use it. It requires `workspace_roots: set[str]` injected from `WatcherService.get_watched_paths()` to evaluate the workspace-root tier of Rule 8. `DUMP_FOLDER_NAMES` is a class-level frozenset.

5. **LLM naming is opt-in fallback, not primary.** Deterministic entity-based naming runs first.

6. **`_GENERIC_TERMS` from `placement_scorer.py` reused in naming.** No new list.

7. **`filename_keywords()` and `filename_bigrams()` from `placement_ports.py` reused.** No new tokenisation.

8. **Clustering algorithm: agglomerative with average linkage.** scipy only. No HDBSCAN for Phase 1.

9. **`min_cluster_size = 2`.** A single document cannot justify creating a new folder.

10. **No "apply all" button.** Each proposal accepted individually.

11. **Duplicate files detected via `file_hash` from `documents` table.** Flagged in review drawer. No automatic deduplication.

12. **Cluster proposals older than 7 days show a staleness warning.** Not auto-dismissed.

13. **Proposal gate is a hard secondary filter after clustering.** Passing the distance threshold is not sufficient to produce a proposal. The gate applies five criteria (tightness, size-2 tightness, entity overlap, entity token count, ambiguity fraction). Failing any criterion = suppressed cluster. No LOW confidence proposals exist — LOW maps to suppressed, not a dim card.

14. **ClusterDiscoveryService owns gate logic; ClusterEngine owns only the algorithm.** ClusterEngine returns raw clusters with metrics. ClusterDiscoveryService applies product-policy gates and assigns confidence. This keeps algorithm and product policy separate so gate thresholds can change without touching the clustering code.

15. **`_PROPOSAL_TIGHTNESS_MIN_PAIR` (0.55) is distinct from `_PROPOSAL_TIGHTNESS_MIN` (0.45).** For size-2 clusters, the single pair must be strongly related. This is not a misconfiguration — it is an intentional higher bar for thin-evidence proposals.

---

## Part 13 — Decisions That Require Experimentation

These cannot be resolved without running the benchmark:

1. **`EAC_CLUSTER_DISTANCE_THRESHOLD`** — dendrogram cut height. Test range 0.20–0.45. Must be calibrated before setting any default. Pre-ship blocker.

2. **`EAC_CLUSTER_ENTITY_WEIGHT` (α)** — balance between embedding and entity overlap. Starting point 0.75. May need adjustment if entity extraction coverage is sparse on user's real corpus.

3. **Whether deterministic naming is sufficient without LLM.** Measure step-4 validation pass rate across Suite 1 clusters. If ≥ 75% pass without LLM, the LLM path may be unnecessary for most clusters.

4. **`EAC_CLUSTER_AMBIGUITY_MARGIN`** — default 0.08 is a starting estimate. Calibrate against Suite 3.

5. **Performance at 300–500 documents.** The combined similarity matrix is O(n²) pairs. At 500 docs = 250,000 pairs. Estimate fast (set intersection < 1ms/pair), but verify empirically before setting a corpus size cap.

6. **Proposal gate threshold calibration.** The default values for `_PROPOSAL_TIGHTNESS_MIN` (0.45), `_PROPOSAL_ENTITY_OVERLAP_MIN` (0.08), and `_PROPOSAL_ENTITY_TOKENS_MIN` (2) are informed estimates. Calibrate against Suite 1 (precision target) and the new Suite 2b (gate precision — see benchmark). If the gate is suppressing true clusters at > 15% rate, loosen entity overlap floor. If it is passing false clusters at > 20% rate, tighten tightness floor.

7. **Whether `_PROPOSAL_TIGHTNESS_MIN_PAIR` of 0.55 is appropriate for size-2 clusters.** This can only be validated against Suite 7 (cluster size extremes, minimum 2-doc cluster). If legitimate 2-document clusters are being suppressed, the threshold can be lowered to 0.50.

---

## Part 14 — Product Principle: Non-Coverage Is Correct Behaviour

The system MUST NOT attempt to organise everything.

The following outputs are **correct** and must never be treated as system failures:
- No floating files found → success
- All floating files became outliers → success (files are too varied to group)
- Only 1 of 40 files grouped → success (1 genuine cluster; the rest are outliers)

The UI communicates these as **success states**, not errors. Precision over recall. A missed opportunity to group files is always preferable to a wrong grouping that moves files into the wrong new folder.

---

*Plan review complete. No codebase modifications were made.*
*All findings are traceable to source files read in this session.*
