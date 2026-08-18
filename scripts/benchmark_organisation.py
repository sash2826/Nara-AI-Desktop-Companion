#!/usr/bin/env python3
"""One-shot placement-scorer benchmark for the Enterprise AI Companion.

Indexes every file in download-recommendations/ against the live test-drive
corpus, scores each against the five project subfolders, compares with the
ground truth in FILE_ORGANIZATION_GROUND_TRUTH.md, and prints a scorecard.

Prerequisites
-------------
- Backend must NOT be running (the script needs exclusive SQLite write access).
- test-drive/ must already be indexed (index it via the app, then stop it).
- download-recommendations/ must exist at the same level as test-drive/.

Usage (from repo root, with the backend venv activated)
-------------------------------------------------------
    cd backend
    python ../scripts/benchmark_organisation.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

# ── Path setup ────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "backend" / "src"
ONEDRIVE = Path.home() / "OneDrive - Volvo Group"
TEST_DRIVE = ONEDRIVE / "test-drive"
DOWNLOAD_RECS = ONEDRIVE / "download-recommendations"

SUBFOLDERS = [
    str(TEST_DRIVE / "Atlas-Workplace"),
    str(TEST_DRIVE / "Aurora-Mobility"),
    str(TEST_DRIVE / "Horizon-Logistics"),
    str(TEST_DRIVE / "Northstar-Analytics"),
    str(TEST_DRIVE / "Polaris-Sustainability"),
]

sys.path.insert(0, str(BACKEND_SRC))

# Load .env so config can read LLM credentials.
try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / "backend" / ".env")
except ImportError:
    pass  # python-dotenv optional; env vars may already be set

# ── Ground truth ──────────────────────────────────────────────────────────────

# None  → expect no recommendation
# list  → any listed folder is acceptable (ambiguous files)
# str   → single expected folder (basename)
GROUND_TRUTH: dict[str, str | list[str] | None] = {
    # Category 1 — Obvious: filename names the target project
    "Aurora_Mobility_Charging_Deployment_Proposal.pdf": "Aurora-Mobility",
    "Northstar_Dashboard_Requirements_Update.docx":     "Northstar-Analytics",
    "Horizon_Warehouse_Optimization_Proposal.pdf":      "Horizon-Logistics",
    "Atlas_Meeting_Room_Technology_Proposal.pdf":       "Atlas-Workplace",
    "Polaris_Carbon_Reporting_Guidelines.pdf":          "Polaris-Sustainability",
    # Category 2 — Semantic: content determines destination
    "Smart_Energy_Load_Management_Study.pdf":           "Aurora-Mobility",
    "Data_Quality_Monitoring_Framework.docx":           "Northstar-Analytics",
    "Warehouse_Demand_Forecasting_Model.xlsx":          "Horizon-Logistics",
    "Workspace_Access_Experience_Study.pdf":            "Atlas-Workplace",
    "Supplier_Emissions_Data_Framework.docx":           "Polaris-Sustainability",
    # Category 3 — Ambiguous: multiple plausible destinations
    "Enterprise_Data_Governance_Guide.pdf":      ["Northstar-Analytics", "Polaris-Sustainability"],
    "Energy_Consumption_Analytics_Report.xlsx":  ["Aurora-Mobility", "Polaris-Sustainability"],
    "Operations_Performance_Review.pdf":         ["Horizon-Logistics", "Northstar-Analytics"],
    "Access_Security_Architecture.pdf":          ["Atlas-Workplace", "Aurora-Mobility"],
    "Vendor_Performance_Framework.docx":         None,  # generic; no project match
    # Category 4 — Wrong-project: content overrides misleading filename
    "Aurora_Analytics_Dashboard.pdf":     "Northstar-Analytics",
    "Horizon_Employee_Workplace_Report.pdf": "Atlas-Workplace",
    "Polaris_Logistics_Data_Report.pdf":   "Horizon-Logistics",
    "Atlas_Sustainability_Review.pdf":     "Polaris-Sustainability",
    # Category 5 — Unrelated: expect no recommendation
    "Personal_Travel_Insurance.pdf":       None,
    "Home_Garden_Improvement_Budget.xlsx": None,
    "Photography_Equipment_Guide.pdf":     None,
    # Category 6 — Duplicate/Update: newer version, still needs correct folder
    "Aurora_Technical_Architecture_v2.pdf":       "Aurora-Mobility",
    "Data_Platform_Requirements_RevB.docx":       "Northstar-Analytics",
    "Warehouse_Requirements_Updated.pdf":         "Horizon-Logistics",
    "Access_Control_Plan_v2.pdf":                 "Atlas-Workplace",
    "Carbon_Reporting_Framework_2026_Update.pdf": "Polaris-Sustainability",
}

CATEGORIES: dict[str, int] = {
    "Aurora_Mobility_Charging_Deployment_Proposal.pdf": 1,
    "Northstar_Dashboard_Requirements_Update.docx":     1,
    "Horizon_Warehouse_Optimization_Proposal.pdf":      1,
    "Atlas_Meeting_Room_Technology_Proposal.pdf":       1,
    "Polaris_Carbon_Reporting_Guidelines.pdf":          1,
    "Smart_Energy_Load_Management_Study.pdf":           2,
    "Data_Quality_Monitoring_Framework.docx":           2,
    "Warehouse_Demand_Forecasting_Model.xlsx":          2,
    "Workspace_Access_Experience_Study.pdf":            2,
    "Supplier_Emissions_Data_Framework.docx":           2,
    "Enterprise_Data_Governance_Guide.pdf":             3,
    "Energy_Consumption_Analytics_Report.xlsx":         3,
    "Operations_Performance_Review.pdf":                3,
    "Access_Security_Architecture.pdf":                 3,
    "Vendor_Performance_Framework.docx":                3,
    "Aurora_Analytics_Dashboard.pdf":                   4,
    "Horizon_Employee_Workplace_Report.pdf":            4,
    "Polaris_Logistics_Data_Report.pdf":                4,
    "Atlas_Sustainability_Review.pdf":                  4,
    "Personal_Travel_Insurance.pdf":                    5,
    "Home_Garden_Improvement_Budget.xlsx":              5,
    "Photography_Equipment_Guide.pdf":                  5,
    "Aurora_Technical_Architecture_v2.pdf":             6,
    "Data_Platform_Requirements_RevB.docx":             6,
    "Warehouse_Requirements_Updated.pdf":               6,
    "Access_Control_Plan_v2.pdf":                       6,
    "Carbon_Reporting_Framework_2026_Update.pdf":       6,
}

CAT_NAMES = {
    1: "Obvious",
    2: "Semantic",
    3: "Ambiguous",
    4: "Wrong-project",
    5: "Unrelated",
    6: "Duplicate/Update",
}

# ── Scoring logic ─────────────────────────────────────────────────────────────

def _score_result(
    filename: str,
    top_folder: str | None,
    all_folders: list[str],
    label: str | None,
) -> tuple[int, str]:
    """Return (points 0/1/2, verdict string) for one benchmark file."""
    expected = GROUND_TRUTH[filename]
    cat = CATEGORIES[filename]

    # Category 5 — unrelated files should produce no recommendation
    if cat == 5:
        if top_folder is None:
            return 2, "PASS  correct rejection"
        return 0, f"FAIL  wrongly placed → {top_folder}"

    # Category 3 — ambiguous: any listed folder is OK; no-rec also OK
    if cat == 3:
        if expected is None:
            # Vendor_Performance_Framework — truly generic
            return (2, "PASS  correct rejection") if top_folder is None else (0, f"FAIL  wrongly placed → {top_folder}")
        assert isinstance(expected, list)
        if top_folder is None:
            return 2, "PASS  no confident rec (correct for ambiguous)"
        if top_folder in expected:
            return 2, f"PASS  plausible → {top_folder}"
        if any(f in expected for f in all_folders):
            return 1, f"PART  correct in top-3; top1={top_folder}"
        return 0, f"FAIL  wrong → {top_folder}, expected one of {expected}"

    # Categories 1, 2, 4, 6 — single expected folder
    assert isinstance(expected, str)
    if top_folder is None:
        return 0, f"FAIL  no recommendation (expected {expected})"
    if top_folder == expected:
        return 2, f"PASS  → {top_folder}"
    if expected in all_folders:
        return 1, f"PART  correct in top-3; top1={top_folder}, expected={expected}"
    return 0, f"FAIL  → {top_folder} (expected {expected})"


# ── Cleanup helpers ───────────────────────────────────────────────────────────

async def _cleanup_indexed_files(conn, chunk_repo, doc_ids: list[str]) -> None:
    """Remove benchmark documents, chunks, and graph data from the index."""
    for doc_id in doc_ids:
        await chunk_repo.delete_by_document(doc_id)

        async with conn.execute(
            "SELECT id FROM graph_entities WHERE source_document_id = ?", (doc_id,)
        ) as cur:
            ent_ids = [row[0] for row in await cur.fetchall()]

        if ent_ids:
            ph = ",".join("?" * len(ent_ids))
            await conn.execute(
                f"DELETE FROM graph_relationships "
                f"WHERE source_id IN ({ph}) OR target_id IN ({ph})",
                ent_ids + ent_ids,
            )
            await conn.execute(
                f"DELETE FROM graph_entities WHERE id IN ({ph})", ent_ids
            )

        await conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        await conn.commit()


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    # Validate paths
    for label, path in [("test-drive/", TEST_DRIVE), ("download-recommendations/", DOWNLOAD_RECS)]:
        if not path.exists():
            print(f"ERROR: {label} not found at {path}")
            sys.exit(1)

    # ── Initialise infrastructure ──────────────────────────────────────────
    from enterprise_ai_companion.infrastructure.database import open_db, close_db
    from enterprise_ai_companion.infrastructure.qdrant_provider import QdrantProvider
    from enterprise_ai_companion.capabilities.graph.sqlite_graph_provider import SQLiteGraphProvider
    from enterprise_ai_companion.capabilities.indexing.document_repository import DocumentRepository
    from enterprise_ai_companion.capabilities.indexing.chunk_repository import ChunkRepository
    from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
    from enterprise_ai_companion.capabilities.indexing.file_indexer import FileIndexer
    from enterprise_ai_companion.capabilities.organisation.placement_scorer import PlacementScorer
    from enterprise_ai_companion.capabilities.organisation.placement_adapters import (
        SqliteGraphScoreAdapter,
        HybridRerankAdapter,
    )

    print("Opening database and Qdrant…")
    conn = await open_db()
    qdrant = QdrantProvider()
    qdrant.initialize()
    graph = SQLiteGraphProvider(conn)
    await graph.initialize()

    embedding_service = EmbeddingService()
    qdrant_client = qdrant.get_client()
    doc_repo = DocumentRepository(conn)
    chunk_repo = ChunkRepository(conn, qdrant_client)

    file_indexer = FileIndexer(
        doc_repo,
        chunk_repo,
        embedding_service,
        graph_provider=graph,
    )

    scorer = PlacementScorer(
        graph_score_port=SqliteGraphScoreAdapter(conn),
        rerank_port=HybridRerankAdapter(conn, embedding_service, qdrant_client),
    )

    # ── Index benchmark files ──────────────────────────────────────────────
    benchmark_files = sorted(
        p for p in DOWNLOAD_RECS.iterdir()
        if p.is_file() and p.name in GROUND_TRUTH
    )
    print(f"\nIndexing {len(benchmark_files)} benchmark files from {DOWNLOAD_RECS.name}/…")
    print("(Requires LLM calls — this takes a few minutes)\n")

    index_result = await file_indexer.index_workspace(str(DOWNLOAD_RECS))
    print(
        f"  {index_result.files_indexed} indexed, "
        f"{index_result.files_skipped} skipped (already up-to-date), "
        f"{len(index_result.errors)} errors\n"
    )

    # ── Score each file ────────────────────────────────────────────────────
    print(f"Scoring against {len(SUBFOLDERS)} candidate folder(s)…\n")

    rows: list[tuple[str, int, str | None, str | None, float, int, str]] = []
    indexed_doc_ids: list[str] = []

    for filename in sorted(GROUND_TRUTH.keys()):
        file_path = str(DOWNLOAD_RECS / filename)
        doc = await doc_repo.get_by_path(file_path)

        if doc is None:
            rows.append((filename, CATEGORIES[filename], None, None, 0.0, 0, "SKIP  not in DB (indexing failed?)"))
            continue

        indexed_doc_ids.append(doc.id)

        scores = await scorer.score_all(doc.id, SUBFOLDERS, file_path=file_path)

        if scores:
            top_folder = Path(scores[0]["folder"]).name
            all_folders = [Path(s["folder"]).name for s in scores]
            label: str | None = scores[0]["label"]
            score_val: float = scores[0]["score"]
        else:
            top_folder = None
            all_folders = []
            label = None
            score_val = 0.0

        pts, verdict = _score_result(filename, top_folder, all_folders, label)
        rows.append((filename, CATEGORIES[filename], top_folder, label, score_val, pts, verdict))

    # ── Cleanup ────────────────────────────────────────────────────────────
    print(f"\nCleaning up {len(indexed_doc_ids)} indexed benchmark document(s)…")
    await _cleanup_indexed_files(conn, chunk_repo, indexed_doc_ids)

    await close_db(conn)
    qdrant.close()
    await graph.close()

    # ── Print scorecard ────────────────────────────────────────────────────
    max_pts = len(rows) * 2
    total_pts = sum(r[5] for r in rows)

    W_FILE = 50
    print()
    print("=" * 105)
    print("  EAC SUBFOLDER ORGANISATION BENCHMARK")
    print("=" * 105)
    print(f"  {'File':<{W_FILE}} {'Cat':>4}  {'Recommended':<22}  {'Score':>6}  {'Pts':>4}  Verdict")
    print("-" * 105)

    cat_pts: dict[int, list[int]] = {c: [] for c in range(1, 7)}
    prev_cat = 0
    for filename, cat, top_folder, label, score_val, pts, verdict in rows:
        if cat != prev_cat:
            if prev_cat:
                print()
            print(f"  -- Category {cat}: {CAT_NAMES[cat]} --")
            prev_cat = cat
        score_str = f"{score_val:.3f}" if score_val > 0 else "     -"
        folder_str = (top_folder or "(none)")
        print(f"  {filename:<{W_FILE}} {cat:>4}  {folder_str:<22}  {score_str}  {pts:>2}/2  {verdict}")
        cat_pts[cat].append(pts)

    print()
    print("-" * 105)
    print(f"  {'TOTAL':<{W_FILE + 4}}  {total_pts:>3}/{max_pts}  ({100 * total_pts // max_pts}%)")
    print()
    print("  By category:")
    for cat_num in range(1, 7):
        pts_list = cat_pts[cat_num]
        if not pts_list:
            continue
        s = sum(pts_list)
        m = len(pts_list) * 2
        bar = "█" * s + "░" * (m - s)
        print(f"    Cat {cat_num} {CAT_NAMES[cat_num]:<18}  {s:>2}/{m}  {bar}")
    print()
    print("=" * 105)


if __name__ == "__main__":
    asyncio.run(main())
