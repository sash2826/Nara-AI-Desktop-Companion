#!/usr/bin/env python3
"""Downloads-watcher benchmark for EAC subfolder organisation.

Drops each file from download-recommendations/ into the real Windows Downloads
folder one at a time, waits for the backend watcher to detect, index, and score
it, reads the resulting recommendation from the database, then compares against
the ground truth in FILE_ORGANIZATION_GROUND_TRUTH.md.

This tests the full Phase 09 pipeline end-to-end:
  watchdog detection → FileIndexer → RecommendationService → PlacementScorer

Prerequisites
-------------
- Backend must be RUNNING (the watcher must be active).
- test-drive/ must already be indexed.
- download-recommendations/ must exist at the same level as test-drive/.

Usage (from repo root, with the backend venv activated)
-------------------------------------------------------
    cd backend
    python ../scripts/benchmark_downloads.py

Cleanup
-------
The script deletes each file from Downloads and dismisses every recommendation
it created, leaving the corpus and the Suggestions inbox unchanged.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "backend" / "src"
ONEDRIVE = Path.home() / "OneDrive - Volvo Group"
DOWNLOADS = Path.home() / "Downloads"
TEST_DRIVE = ONEDRIVE / "test-drive"
DOWNLOAD_RECS = ONEDRIVE / "download-recommendations"

DB_PATH = REPO_ROOT / "enterprise_ai_companion.db"

sys.path.insert(0, str(BACKEND_SRC))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / "backend" / ".env")
except ImportError:
    pass

# ── Ground truth ──────────────────────────────────────────────────────────────

GROUND_TRUTH: dict[str, str | list[str] | None] = {
    # Category 1 — Obvious
    "Aurora_Mobility_Charging_Deployment_Proposal.pdf": "Aurora-Mobility",
    "Northstar_Dashboard_Requirements_Update.docx":     "Northstar-Analytics",
    "Horizon_Warehouse_Optimization_Proposal.pdf":      "Horizon-Logistics",
    "Atlas_Meeting_Room_Technology_Proposal.pdf":       "Atlas-Workplace",
    "Polaris_Carbon_Reporting_Guidelines.pdf":          "Polaris-Sustainability",
    # Category 2 — Semantic
    "Smart_Energy_Load_Management_Study.pdf":           "Aurora-Mobility",
    "Data_Quality_Monitoring_Framework.docx":           "Northstar-Analytics",
    "Warehouse_Demand_Forecasting_Model.xlsx":          "Horizon-Logistics",
    "Workspace_Access_Experience_Study.pdf":            "Atlas-Workplace",
    "Supplier_Emissions_Data_Framework.docx":           "Polaris-Sustainability",
    # Category 3 — Ambiguous (any listed folder or no-rec acceptable)
    "Enterprise_Data_Governance_Guide.pdf":      ["Northstar-Analytics", "Polaris-Sustainability"],
    "Energy_Consumption_Analytics_Report.xlsx":  ["Aurora-Mobility", "Polaris-Sustainability"],
    "Operations_Performance_Review.pdf":         ["Horizon-Logistics", "Northstar-Analytics"],
    "Access_Security_Architecture.pdf":          ["Atlas-Workplace", "Aurora-Mobility"],
    "Vendor_Performance_Framework.docx":         None,
    # Category 4 — Wrong-project (content overrides filename)
    "Aurora_Analytics_Dashboard.pdf":            "Northstar-Analytics",
    "Horizon_Employee_Workplace_Report.pdf":     "Atlas-Workplace",
    "Polaris_Logistics_Data_Report.pdf":         "Horizon-Logistics",
    "Atlas_Sustainability_Review.pdf":           "Polaris-Sustainability",
    # Category 5 — Unrelated
    "Personal_Travel_Insurance.pdf":             None,
    "Home_Garden_Improvement_Budget.xlsx":       None,
    "Photography_Equipment_Guide.pdf":           None,
    # Category 6 — Duplicate/Update
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

# Seconds to wait for the backend to detect, index, and create a recommendation.
# The pipeline is: watchdog debounce (2s) + indexing + LLM entity extraction +
# PlacementScorer.  Allow generous time for LLM latency on larger files.
_TIMEOUT_PER_FILE = 180
_POLL_INTERVAL = 3


# ── Scoring ───────────────────────────────────────────────────────────────────

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
        return 0, f"FAIL  wrongly recommended → {top_folder}"

    if cat == 3:
        if expected is None:
            return (2, "PASS  correct rejection") if top_folder is None else (0, f"FAIL  wrongly recommended → {top_folder}")
        assert isinstance(expected, list)
        if top_folder is None:
            return 2, "PASS  no confident rec (correct for ambiguous)"
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


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _open_db():
    import aiosqlite
    conn = await aiosqlite.connect(str(DB_PATH), isolation_level=None)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA busy_timeout=30000")
    return conn


async def _poll_for_recommendation(
    conn,
    downloads_path: str,
    timeout: int,
) -> tuple[dict | None, str]:
    """Poll until a pending recommendation exists for downloads_path or timeout.

    Returns (result_dict_or_None, status_string) where status is one of:
      "found"      — recommendation created
      "indexed"    — document indexed but scorer created no recommendation
      "not_indexed"— document never appeared in the DB (watcher/indexing issue)
    """
    deadline = time.monotonic() + timeout
    doc_indexed = False

    while time.monotonic() < deadline:
        # Check for recommendation first
        async with conn.execute(
            "SELECT id, recommendations FROM file_placement_recommendations "
            "WHERE source_path = ? AND status = 'pending'",
            (downloads_path,),
        ) as cur:
            row = await cur.fetchone()
        if row:
            return {"id": row["id"], "recommendations": json.loads(row["recommendations"])}, "found"

        # Track whether the document was indexed even if no rec was created
        if not doc_indexed:
            async with conn.execute(
                "SELECT id FROM documents WHERE file_path = ?", (downloads_path,)
            ) as cur:
                doc_row = await cur.fetchone()
            if doc_row:
                doc_indexed = True

        await asyncio.sleep(_POLL_INTERVAL)

    status = "indexed" if doc_indexed else "not_indexed"
    return None, status


async def _dismiss_recommendation(conn, rec_id: str) -> None:
    from datetime import UTC, datetime
    await conn.execute(
        "UPDATE file_placement_recommendations "
        "SET status='dismissed', resolved_at=? WHERE id=?",
        (datetime.now(UTC).isoformat(), rec_id),
    )
    await conn.commit()


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    logging.basicConfig(level=logging.WARNING)

    for label, path in [
        ("download-recommendations/", DOWNLOAD_RECS),
        ("test-drive/",               TEST_DRIVE),
        ("Downloads/",                DOWNLOADS),
        ("enterprise_ai_companion.db", DB_PATH),
    ]:
        if not path.exists():
            print(f"ERROR: {label} not found at {path}")
            sys.exit(1)

    print(f"Database : {DB_PATH}")
    print(f"Downloads: {DOWNLOADS}")
    print(f"Files    : {len(GROUND_TRUTH)} benchmark files")
    print()

    conn = await _open_db()
    rows: list[tuple[str, int, str | None, str | None, float, int, str]] = []
    created_rec_ids: list[str] = []
    dropped_files: list[Path] = []

    try:
        for filename in sorted(GROUND_TRUTH.keys()):
            src = DOWNLOAD_RECS / filename
            dst = DOWNLOADS / filename

            if not src.exists():
                rows.append((filename, CATEGORIES[filename], None, None, 0.0, 0, "SKIP  source file missing"))
                continue

            # Remove any stale recommendation from a previous run.
            async with conn.execute(
                "SELECT id FROM file_placement_recommendations "
                "WHERE source_path = ? AND status = 'pending'",
                (str(dst),),
            ) as cur:
                stale = await cur.fetchone()
            if stale:
                await _dismiss_recommendation(conn, stale["id"])

            # Drop the file into Downloads.
            shutil.copy2(str(src), str(dst))
            dropped_files.append(dst)
            drop_time = time.monotonic()
            print(f"  [{filename:<55}] dropped — waiting…", end="", flush=True)

            # Wait for the backend to process it.
            result, poll_status = await _poll_for_recommendation(conn, str(dst), _TIMEOUT_PER_FILE)
            elapsed = time.monotonic() - drop_time

            if result is None:
                if poll_status == "indexed":
                    # Scorer returned no results — treat as no-recommendation and
                    # score properly (correct for Cat 5/ambiguous Cat 3).
                    pts, verdict = _score_result(filename, None, [])
                    elapsed_str = f"{elapsed:5.1f}s"
                    print(f" {elapsed_str}  →  (none)                   -      {pts}/2  {verdict}")
                    rows.append((filename, CATEGORIES[filename], None, None, 0.0, pts, verdict))
                else:
                    diag = "not indexed within timeout — watcher may not have detected the drop"
                    print(f" TIMEOUT ({_TIMEOUT_PER_FILE}s)  [{diag}]")
                    rows.append((filename, CATEGORIES[filename], None, None, 0.0, 0, f"SKIP  {diag}"))
                # Remove the file regardless.
                dst.unlink(missing_ok=True)
                dropped_files.remove(dst)
                continue

            recs: list[dict] = result["recommendations"]
            created_rec_ids.append(result["id"])

            top_folder = Path(recs[0]["folder"]).name if recs else None
            all_folders = [Path(r["folder"]).name for r in recs]
            label_str: str | None = recs[0]["label"] if recs else None
            score_val: float = recs[0]["score"] if recs else 0.0

            pts, verdict = _score_result(filename, top_folder, all_folders)
            rows.append((filename, CATEGORIES[filename], top_folder, label_str, score_val, pts, verdict))

            print(f" {elapsed:5.1f}s  →  {top_folder or '(none)':<22}  {score_val:.3f}  {pts}/2  {verdict}")

            # Remove the file from Downloads immediately.
            dst.unlink(missing_ok=True)
            dropped_files.remove(dst)

            # Small gap between files so the watcher doesn't overlap events.
            await asyncio.sleep(2)

    finally:
        # Clean up any files left in Downloads on early exit.
        for p in dropped_files:
            p.unlink(missing_ok=True)

        # Dismiss all recommendations created during this run.
        for rec_id in created_rec_ids:
            await _dismiss_recommendation(conn, rec_id)

        await conn.close()

    # ── Scorecard ─────────────────────────────────────────────────────────
    max_pts = len(rows) * 2
    total_pts = sum(r[5] for r in rows)

    W = 50
    print()
    print("=" * 105)
    print("  EAC SUBFOLDER ORGANISATION BENCHMARK  (Downloads watcher)")
    print("=" * 105)
    print(f"  {'File':<{W}} {'Cat':>4}  {'Recommended':<22}  {'Score':>6}  {'Pts':>4}  Verdict")
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
        print(f"  {filename:<{W}} {cat:>4}  {(top_folder or '(none)'):<22}  {score_str}  {pts:>2}/2  {verdict}")
        cat_pts[cat].append(pts)

    print()
    print("-" * 105)
    pct = 100 * total_pts // max_pts if max_pts else 0
    print(f"  {'TOTAL':<{W + 4}}  {total_pts:>3}/{max_pts}  ({pct}%)")
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
