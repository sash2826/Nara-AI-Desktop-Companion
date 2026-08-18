#!/usr/bin/env python3
"""Audit benchmark — copies benchmark files into test-drive/ root and scores
the AuditService pipeline's ability to recommend the correct subfolder.

This simulates the real-world scenario where files land in a folder root
instead of a project subfolder, then the audit surfaces where they belong.
The scoring replicates AuditService._score_doc logic exactly (ancestor
detection, _MIN_TOP_SCORE, _MIN_SCORE_DELTA) without creating DB records.

Prerequisites
-------------
- Backend must NOT be running (script needs exclusive SQLite write access).
- test-drive/ must already be indexed (index via the app, then stop it).
- download-recommendations/ must contain the benchmark files.

Usage (from repo root, with the backend venv activated)
-------------------------------------------------------
    cd backend
    python ../scripts/benchmark_audit.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT   = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "backend" / "src"
ONEDRIVE    = Path.home() / "OneDrive - Volvo Group"
TEST_DRIVE  = ONEDRIVE / "test-drive"
DOWNLOAD_RECS = ONEDRIVE / "download-recommendations"

# Must match AuditService thresholds exactly
_MIN_TOP_SCORE  = 0.22
_MIN_SCORE_DELTA = 0.10

sys.path.insert(0, str(BACKEND_SRC))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / "backend" / ".env")
except ImportError:
    pass

# ── Ground truth ──────────────────────────────────────────────────────────────

GROUND_TRUTH: dict[str, str | list[str] | None] = {
    "Aurora_Mobility_Charging_Deployment_Proposal.pdf": "Aurora-Mobility",
    "Northstar_Dashboard_Requirements_Update.docx":     "Northstar-Analytics",
    "Horizon_Warehouse_Optimization_Proposal.pdf":      "Horizon-Logistics",
    "Atlas_Meeting_Room_Technology_Proposal.pdf":       "Atlas-Workplace",
    "Polaris_Carbon_Reporting_Guidelines.pdf":          "Polaris-Sustainability",
    "Smart_Energy_Load_Management_Study.pdf":           "Aurora-Mobility",
    "Data_Quality_Monitoring_Framework.docx":           "Northstar-Analytics",
    "Warehouse_Demand_Forecasting_Model.xlsx":          "Horizon-Logistics",
    "Workspace_Access_Experience_Study.pdf":            "Atlas-Workplace",
    "Supplier_Emissions_Data_Framework.docx":           "Polaris-Sustainability",
    "Enterprise_Data_Governance_Guide.pdf":      ["Northstar-Analytics", "Polaris-Sustainability"],
    "Energy_Consumption_Analytics_Report.xlsx":  ["Aurora-Mobility", "Polaris-Sustainability"],
    "Operations_Performance_Review.pdf":         ["Horizon-Logistics", "Northstar-Analytics"],
    "Access_Security_Architecture.pdf":          ["Atlas-Workplace", "Aurora-Mobility"],
    "Vendor_Performance_Framework.docx":         None,
    "Aurora_Analytics_Dashboard.pdf":     "Northstar-Analytics",
    "Horizon_Employee_Workplace_Report.pdf": "Atlas-Workplace",
    "Polaris_Logistics_Data_Report.pdf":   "Horizon-Logistics",
    "Atlas_Sustainability_Review.pdf":     "Polaris-Sustainability",
    "Personal_Travel_Insurance.pdf":       None,
    "Home_Garden_Improvement_Budget.xlsx": None,
    "Photography_Equipment_Guide.pdf":     None,
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


def _score_result(
    filename: str,
    top_folder: str | None,
    all_folders: list[str],
) -> tuple[int, str]:
    expected = GROUND_TRUTH[filename]
    cat = CATEGORIES[filename]

    if cat == 5:
        if top_folder is None:
            return 2, "PASS  correct rejection"
        return 0, f"FAIL  wrongly placed → {top_folder}"

    if cat == 3:
        if expected is None:
            return (2, "PASS  correct rejection") if top_folder is None else (0, f"FAIL  wrongly placed → {top_folder}")
        assert isinstance(expected, list)
        if top_folder is None:
            return 2, "PASS  no confident rec (OK for ambiguous)"
        if top_folder in expected:
            return 2, f"PASS  plausible → {top_folder}"
        if any(f in expected for f in all_folders):
            return 1, f"PART  correct in top-3; top1={top_folder}"
        return 0, f"FAIL  wrong → {top_folder}, expected one of {expected}"

    assert isinstance(expected, str)
    if top_folder is None:
        return 0, f"FAIL  no recommendation (expected {expected})"
    if top_folder == expected:
        return 2, f"PASS  → {top_folder}"
    if expected in all_folders:
        return 1, f"PART  correct in top-3; top1={top_folder}, expected={expected}"
    return 0, f"FAIL  → {top_folder} (expected {expected})"


# ── Cleanup ───────────────────────────────────────────────────────────────────

async def _remove_from_index(conn, chunk_repo, doc_ids: list[str]) -> None:
    for doc_id in doc_ids:
        await chunk_repo.delete_by_document(doc_id)

        async with conn.execute(
            "SELECT id FROM graph_entities WHERE source_document_id = ?", (doc_id,)
        ) as cur:
            ent_ids = [row[0] for row in await cur.fetchall()]

        if ent_ids:
            ph = ",".join("?" * len(ent_ids))
            await conn.execute(
                f"DELETE FROM graph_relationships WHERE source_id IN ({ph}) OR target_id IN ({ph})",
                ent_ids + ent_ids,
            )
            await conn.execute(f"DELETE FROM graph_entities WHERE id IN ({ph})", ent_ids)

        await conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        await conn.commit()


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    for label, path in [("test-drive/", TEST_DRIVE), ("download-recommendations/", DOWNLOAD_RECS)]:
        if not path.exists():
            print(f"ERROR: {label} not found at {path}")
            sys.exit(1)

    # ── Imports ────────────────────────────────────────────────────────────
    from enterprise_ai_companion.infrastructure.database import open_db, close_db
    from enterprise_ai_companion.infrastructure.qdrant_provider import QdrantProvider
    from enterprise_ai_companion.capabilities.graph.sqlite_graph_provider import SQLiteGraphProvider
    from enterprise_ai_companion.capabilities.indexing.document_repository import DocumentRepository
    from enterprise_ai_companion.capabilities.indexing.chunk_repository import ChunkRepository
    from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
    from enterprise_ai_companion.capabilities.indexing.file_indexer import FileIndexer
    from enterprise_ai_companion.capabilities.organisation.placement_adapters import (
        HybridRerankAdapter,
        SqliteGraphScoreAdapter,
    )
    from enterprise_ai_companion.capabilities.organisation.placement_scorer import PlacementScorer

    print("Opening database and Qdrant…")
    conn = await open_db()
    await conn.execute("PRAGMA busy_timeout=30000")
    qdrant = QdrantProvider()
    qdrant.initialize()
    graph = SQLiteGraphProvider(conn)
    await graph.initialize()

    embedding_service = EmbeddingService()
    qdrant_client = qdrant.get_client()
    doc_repo = DocumentRepository(conn)
    chunk_repo = ChunkRepository(conn, qdrant_client)
    file_indexer = FileIndexer(doc_repo, chunk_repo, embedding_service, graph_provider=graph)
    scorer = PlacementScorer(
        graph_score_port=SqliteGraphScoreAdapter(conn=conn),
        rerank_port=HybridRerankAdapter(
            conn=conn,
            embedding_service=embedding_service,
            qdrant_client=qdrant_client,
        ),
    )

    # ── Copy benchmark files into test-drive/ root ─────────────────────────
    bench_files = sorted(p for p in DOWNLOAD_RECS.iterdir() if p.is_file() and p.name in GROUND_TRUTH)
    copied: list[Path] = []
    skipped_copy: list[str] = []

    print(f"\nCopying {len(bench_files)} benchmark files to {TEST_DRIVE.name}/ root…")
    for src in bench_files:
        dst = TEST_DRIVE / src.name
        if dst.exists():
            skipped_copy.append(src.name)
        else:
            shutil.copy2(src, dst)
            copied.append(dst)

    if skipped_copy:
        print(f"  Skipped {len(skipped_copy)} already-present file(s): {skipped_copy}")
    print(f"  Copied {len(copied)} file(s).\n")

    # ── Index the root-level copies ────────────────────────────────────────
    all_root_files = [TEST_DRIVE / f for f in GROUND_TRUTH if (TEST_DRIVE / f).exists()]
    print(f"Indexing {len(all_root_files)} file(s) from test-drive/ root…")
    print("(LLM entity extraction — takes a few minutes)\n")

    indexed_count = skipped_count = error_count = 0
    for fpath in all_root_files:
        doc_id = await file_indexer.index_file(str(fpath), str(TEST_DRIVE))
        if doc_id:
            indexed_count += 1
        else:
            skipped_count += 1

    print(f"  {indexed_count} indexed, {skipped_count} skipped, {error_count} errors\n")

    # ── Discover candidate subfolders (same as AuditService) ──────────────
    candidate_paths = await scorer.discover_candidate_folders(
        exclude_paths={str(TEST_DRIVE)}  # root itself is not a destination
    )
    print(f"Candidate subfolders: {[Path(c).name for c in candidate_paths]}\n")

    # ── Score each benchmark file ──────────────────────────────────────────
    current_folder = str(TEST_DRIVE)
    current_sep = current_folder.rstrip(os.sep) + os.sep

    # Root is an ancestor of all subfolders → current_score = 0.0 for all files
    current_folder_is_ancestor = any(c.startswith(current_sep) for c in candidate_paths)

    non_current_candidates = [
        f for f in candidate_paths
        if f != current_folder and not current_folder.startswith(f.rstrip(os.sep) + os.sep)
    ]

    print(f"Scoring {len(GROUND_TRUTH)} benchmark files against audit thresholds "
          f"(min_score={_MIN_TOP_SCORE}, min_delta={_MIN_SCORE_DELTA})…\n")

    rows: list[tuple[str, int, str | None, str | None, float, int, str]] = []
    indexed_doc_ids: list[str] = []

    for filename in sorted(GROUND_TRUTH.keys()):
        file_path = str(TEST_DRIVE / filename)
        doc = await doc_repo.get_by_path(file_path)

        if doc is None:
            rows.append((filename, CATEGORIES[filename], None, None, 0.0, 0,
                         "SKIP  not in DB (indexing failed?)"))
            continue

        indexed_doc_ids.append(doc.id)

        if not non_current_candidates:
            rows.append((filename, CATEGORIES[filename], None, None, 0.0, 0,
                         "SKIP  no candidate subfolders"))
            continue

        current_score = 0.0  # root is ancestor

        scores = await scorer.score_all(
            doc.id, non_current_candidates, file_path=file_path, graph_gate=0.0
        )

        if not scores or scores[0]["score"] < _MIN_TOP_SCORE:
            top_folder = None
            all_folders: list[str] = []
            score_val = scores[0]["score"] if scores else 0.0
            reason = f"below min_score ({score_val:.3f} < {_MIN_TOP_SCORE})"
        elif (scores[0]["score"] - current_score) < _MIN_SCORE_DELTA:
            top_folder = None
            all_folders = []
            score_val = scores[0]["score"]
            reason = f"delta too small ({score_val:.3f} - {current_score:.3f} < {_MIN_SCORE_DELTA})"
        else:
            top_folder = Path(scores[0]["folder"]).name
            all_folders = [Path(s["folder"]).name for s in scores]
            score_val = scores[0]["score"]
            reason = ""

        pts, verdict = _score_result(filename, top_folder, all_folders)
        # Only override verdict for categories where missing a recommendation is wrong.
        # Cat 3 (ambiguous) and Cat 5 (unrelated) grant full points for no recommendation,
        # so don't overwrite their verdict text with a misleading FAIL label.
        if reason and top_folder is None and CATEGORIES[filename] not in (3, 5):
            verdict = f"FAIL  no rec — {reason}"
        rows.append((filename, CATEGORIES[filename], top_folder, None, score_val, pts, verdict))

    # ── Cleanup ────────────────────────────────────────────────────────────
    print(f"\nCleaning up index for {len(indexed_doc_ids)} benchmark document(s)…")
    await _remove_from_index(conn, chunk_repo, indexed_doc_ids)

    print(f"Removing {len(copied)} copied file(s) from test-drive/ root…")
    for dst in copied:
        dst.unlink(missing_ok=True)

    await close_db(conn)
    qdrant.close()
    await graph.close()

    # ── Scorecard ──────────────────────────────────────────────────────────
    max_pts = len(rows) * 2
    total_pts = sum(r[5] for r in rows)
    W = 50

    print()
    print("=" * 110)
    print("  EAC AUDIT BENCHMARK  (files in test-drive/ root → recommended subfolder)")
    print("=" * 110)
    print(f"  {'File':<{W}} {'Cat':>4}  {'Recommended':<22}  {'Score':>6}  {'Pts':>4}  Verdict")
    print("-" * 110)

    cat_pts: dict[int, list[int]] = {c: [] for c in range(1, 7)}
    prev_cat = 0
    for filename, cat, top_folder, _, score_val, pts, verdict in rows:
        if cat != prev_cat:
            if prev_cat:
                print()
            print(f"  -- Category {cat}: {CAT_NAMES[cat]} --")
            prev_cat = cat
        score_str = f"{score_val:.3f}" if score_val > 0 else "     -"
        folder_str = top_folder or "(none)"
        print(f"  {filename:<{W}} {cat:>4}  {folder_str:<22}  {score_str}  {pts:>2}/2  {verdict}")
        cat_pts[cat].append(pts)

    print()
    print("-" * 110)
    print(f"  {'TOTAL':<{W + 4}}  {total_pts:>3}/{max_pts}  ({100 * total_pts // max_pts}%)")
    print()
    print("  By category:")
    for cat_num in range(1, 7):
        pts_list = cat_pts[cat_num]
        if not pts_list:
            continue
        s, m = sum(pts_list), len(pts_list) * 2
        bar = "█" * s + "░" * (m - s)
        print(f"    Cat {cat_num} {CAT_NAMES[cat_num]:<18}  {s:>2}/{m}  {bar}")
    print()
    print("=" * 110)


if __name__ == "__main__":
    asyncio.run(main())
