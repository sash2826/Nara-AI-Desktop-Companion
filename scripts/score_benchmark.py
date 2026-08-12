"""Benchmark scorecard updater for the file-organisation pipeline.

Reads accepted/dismissed recommendations from the SQLite DB, compares each
against the ground truth, calculates points, and rewrites SCORECARD.md.

Usage:
    python scripts/score_benchmark.py

The script is idempotent — run it after every test file to keep the scorecard
current. It does not modify the DB.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, UTC
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "enterprise_ai_companion.db"
SCORECARD_PATH = REPO_ROOT / "test-drive" / "SCORECARD.md"

# ---------------------------------------------------------------------------
# Ground truth
# ---------------------------------------------------------------------------

# Scoring key: filename stem (case-insensitive) → dict
#   expected_folder: str | list[str]  — acceptable folder name(s) (basename only)
#   category: int
#   unrelated: bool  — True means correct answer is NO recommendation
#   ambiguous: bool  — True means pass condition is low confidence or no rec

GROUND_TRUTH: dict[str, dict] = {
    # Category 1 — Obvious
    "Aurora_Mobility_Charging_Deployment_Proposal": {
        "category": 1, "expected_folder": ["Aurora-Mobility"],
    },
    "Northstar_Dashboard_Requirements_Update": {
        "category": 1, "expected_folder": ["Northstar-Analytics"],
    },
    "Horizon_Warehouse_Optimization_Proposal": {
        "category": 1, "expected_folder": ["Horizon-Logistics"],
    },
    "Atlas_Meeting_Room_Technology_Proposal": {
        "category": 1, "expected_folder": ["Atlas-Workplace"],
    },
    "Polaris_Carbon_Reporting_Guidelines": {
        "category": 1, "expected_folder": ["Polaris-Sustainability"],
    },
    # Category 2 — Semantic
    "Smart_Energy_Load_Management_Study": {
        "category": 2, "expected_folder": ["Aurora-Mobility"],
    },
    "Data_Quality_Monitoring_Framework": {
        "category": 2, "expected_folder": ["Northstar-Analytics"],
    },
    "Warehouse_Demand_Forecasting_Model": {
        "category": 2, "expected_folder": ["Horizon-Logistics"],
    },
    "Workspace_Access_Experience_Study": {
        "category": 2, "expected_folder": ["Atlas-Workplace"],
    },
    "Supplier_Emissions_Data_Framework": {
        "category": 2, "expected_folder": ["Polaris-Sustainability"],
    },
    # Category 3 — Ambiguous (pass = no rec OR low confidence)
    "Enterprise_Data_Governance_Guide": {
        "category": 3, "ambiguous": True,
        "expected_folder": ["Northstar-Analytics", "Polaris-Sustainability"],
    },
    "Energy_Consumption_Analytics_Report": {
        "category": 3, "ambiguous": True,
        "expected_folder": ["Aurora-Mobility", "Polaris-Sustainability", "Northstar-Analytics"],
    },
    "Operations_Performance_Review": {
        "category": 3, "ambiguous": True,
        "expected_folder": ["Horizon-Logistics", "Northstar-Analytics"],
    },
    "Access_Security_Architecture": {
        "category": 3, "ambiguous": True,
        "expected_folder": ["Atlas-Workplace", "Aurora-Mobility"],
    },
    "Vendor_Performance_Framework": {
        "category": 3, "ambiguous": True,
        "expected_folder": ["Aurora-Mobility", "Northstar-Analytics", "Horizon-Logistics",
                            "Atlas-Workplace", "Polaris-Sustainability"],
    },
    # Category 4 — Wrong-project (filename misleads; content decides)
    "Aurora_Analytics_Dashboard": {
        "category": 4, "expected_folder": ["Northstar-Analytics"],
    },
    "Horizon_Employee_Workplace_Report": {
        "category": 4, "expected_folder": ["Atlas-Workplace"],
    },
    "Polaris_Logistics_Data_Report": {
        "category": 4, "expected_folder": ["Horizon-Logistics"],
    },
    "Atlas_Sustainability_Review": {
        "category": 4, "expected_folder": ["Polaris-Sustainability"],
    },
    # Category 5 — Unrelated (correct answer = no recommendation)
    "Personal_Travel_Insurance": {
        "category": 5, "unrelated": True, "expected_folder": [],
    },
    "Home_Garden_Improvement_Budget": {
        "category": 5, "unrelated": True, "expected_folder": [],
    },
    "Photography_Equipment_Guide": {
        "category": 5, "unrelated": True, "expected_folder": [],
    },
    # Category 6 — Duplicate/Updated versions
    "Aurora_Technical_Architecture_v2": {
        "category": 6, "expected_folder": ["Aurora-Mobility"],
    },
    "Data_Platform_Requirements_RevB": {
        "category": 6, "expected_folder": ["Northstar-Analytics"],
    },
    "Warehouse_Requirements_Updated": {
        "category": 6, "expected_folder": ["Horizon-Logistics"],
    },
    "Access_Control_Plan_v2": {
        "category": 6, "expected_folder": ["Atlas-Workplace"],
    },
    "Carbon_Reporting_Framework_2026_Update": {
        "category": 6, "expected_folder": ["Polaris-Sustainability"],
    },
}

CAT_MAX = {1: 10, 2: 10, 3: 10, 4: 8, 5: 6, 6: 10}
CAT_NAMES = {
    1: "Obvious Matches",
    2: "Semantic Matches",
    3: "Ambiguous Matches",
    4: "Wrong-Project Matches",
    5: "Unrelated Files",
    6: "Duplicate / Updated Versions",
}

# ---------------------------------------------------------------------------
# DB query
# ---------------------------------------------------------------------------

def _stem(path: str) -> str:
    return Path(path).stem


def load_recommendations() -> list[dict]:
    """Return the most-recent recommendation per file stem, pending-first.

    Scoring rule: only a *pending* record counts as an active recommendation
    shown to the user. An *accepted* or *dismissed* record means the suggestion
    was already acted on / cleaned up — for scoring purposes that is equivalent
    to "no recommendation currently shown."

    Within pending records, the most recently created one wins (covers the case
    where a file is re-dropped and a fresh record supersedes an older one).
    """
    if not DB_PATH.exists():
        print(f"[warn] DB not found at {DB_PATH} — no results yet.")
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Order oldest → newest so the last write per stem is the most recent.
    cur = conn.execute(
        "SELECT id, source_path, status, recommendations, accepted_folder "
        "FROM file_placement_recommendations "
        "ORDER BY created_at ASC"
    )
    rows = cur.fetchall()
    conn.close()

    # Build two indexes: most-recent pending, and most-recent of any status.
    pending_by_stem: dict[str, dict] = {}
    any_by_stem: dict[str, dict] = {}
    for row in rows:
        recs = json.loads(row["recommendations"]) if row["recommendations"] else []
        entry = {
            "id": row["id"],
            "source_path": row["source_path"],
            "status": row["status"],
            "candidates": recs,
            "accepted_folder": row["accepted_folder"],
        }
        stem = _stem(row["source_path"]).lower()
        any_by_stem[stem] = entry
        if row["status"] == "pending":
            pending_by_stem[stem] = entry

    # Prefer pending — if none exists for this stem, fall back to the most
    # recent record but clear its candidates so it scores as "no recommendation."
    results: list[dict] = []
    seen: set[str] = set()
    for stem, entry in pending_by_stem.items():
        results.append(entry)
        seen.add(stem)
    for stem, entry in any_by_stem.items():
        if stem not in seen:
            # Non-pending (dismissed/accepted) — treat as no recommendation.
            results.append({**entry, "candidates": []})
    return results


# ---------------------------------------------------------------------------
# Scoring logic
# ---------------------------------------------------------------------------

def _folder_name(path: str | None) -> str:
    """Return the basename of a path, or '' if None."""
    if not path:
        return ""
    return Path(path).name


def score_result(truth: dict, rec: dict) -> tuple[int, str]:
    """Return (points, note) for a single recommendation result."""
    candidates = rec["candidates"]
    top_folder = _folder_name(candidates[0]["folder"]) if candidates else ""
    top_label = candidates[0]["label"] if candidates else ""
    top_score = candidates[0]["score"] if candidates else 0.0
    has_rec = bool(top_folder)
    status = rec["status"]

    # Category 5 — unrelated: correct = no recommendation surfaced
    if truth.get("unrelated"):
        if not has_rec:
            return 2, "Correct rejection ✓"
        return 0, f"False positive → {top_folder}"

    # Category 3 — ambiguous: correct = no rec OR low-confidence match to acceptable folder
    if truth.get("ambiguous"):
        acceptable = truth["expected_folder"]
        if not has_rec:
            return 2, "No recommendation (correct for ambiguous) ✓"
        if top_folder in acceptable:
            if top_label in ("Possible",) or top_score < 0.35:
                return 2, f"Low-confidence match to acceptable folder {top_folder} ✓"
            return 1, f"Matched acceptable folder {top_folder} but confidence too high ({top_label})"
        return 0, f"Wrong folder → {top_folder}"

    # All other categories
    expected = truth["expected_folder"]
    if not has_rec:
        return 0, "No recommendation shown"
    if top_folder in expected:
        if top_label in ("Most Likely", "Likely"):
            return 2, f"Correct ✓ ({top_label})"
        return 1, f"Correct folder but low confidence ({top_label})"
    return 0, f"Wrong folder → {top_folder} (expected {expected[0]})"


# ---------------------------------------------------------------------------
# Scorecard builder
# ---------------------------------------------------------------------------

def build_scorecard(recs: list[dict]) -> str:
    # Index recommendations by file stem (case-insensitive)
    rec_by_stem: dict[str, dict] = {}
    for rec in recs:
        stem = _stem(rec["source_path"]).lower()
        # Prefer most-recent if duplicate stems exist
        rec_by_stem[stem] = rec

    # Score everything
    results: dict[str, tuple[int, str, dict | None]] = {}  # stem → (pts, note, rec)
    for stem_key, truth in GROUND_TRUTH.items():
        rec = rec_by_stem.get(stem_key.lower())
        if rec is None:
            results[stem_key] = (-1, "Not yet tested", None)
        else:
            pts, note = score_result(truth, rec)
            results[stem_key] = (pts, note, rec)

    tested = sum(1 for pts, _, __ in results.values() if pts >= 0)
    total_pts = sum(pts for pts, _, __ in results.values() if pts >= 0)
    max_pts = 54
    pct = round(total_pts / max_pts * 100) if tested else 0

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = [
        "# Benchmark Scorecard — File Organisation",
        "",
        f"Auto-updated by `scripts/score_benchmark.py`. Last updated: {now}",
        "",
        "## Running Total",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Files tested | {tested} / 27 |",
        f"| Points scored | {total_pts} / {max_pts} |",
        f"| Score % | {pct}% |",
        "",
        "---",
        "",
    ]

    def _actual(stem: str) -> tuple[str, str, str]:
        pts, note, rec = results[stem]
        if rec is None:
            return "—", "—", "—"
        candidates = rec["candidates"]
        folder = _folder_name(candidates[0]["folder"]) if candidates else "No rec"
        label = candidates[0]["label"] if candidates else "—"
        score_val = f"{round(candidates[0]['score'] * 100)}%" if candidates else "—"
        label_disp = f"{label} ({score_val})" if candidates else "—"
        pts_disp = str(pts) if pts >= 0 else "—"
        return folder, label_disp, pts_disp

    def _pts_disp(stem: str) -> str:
        pts, note, _ = results[stem]
        if pts < 0:
            return "—"
        return f"**{pts}**" if pts == 2 else str(pts)

    def _note(stem: str) -> str:
        _, note, _ = results[stem]
        return note if results[stem][0] >= 0 else "—"

    # Category 1
    cat1_pts = sum(results[s][0] for s in [
        "Aurora_Mobility_Charging_Deployment_Proposal",
        "Northstar_Dashboard_Requirements_Update",
        "Horizon_Warehouse_Optimization_Proposal",
        "Atlas_Meeting_Room_Technology_Proposal",
        "Polaris_Carbon_Reporting_Guidelines",
    ] if results[s][0] >= 0)
    lines += [
        f"## Category 1 — Obvious Matches (scored {cat1_pts} / 10)",
        "",
        "| File | Expected | Actual Folder | Label | Pts | Notes |",
        "|------|----------|---------------|-------|-----|-------|",
    ]
    for stem, exp in [
        ("Aurora_Mobility_Charging_Deployment_Proposal", "Aurora-Mobility"),
        ("Northstar_Dashboard_Requirements_Update", "Northstar-Analytics"),
        ("Horizon_Warehouse_Optimization_Proposal", "Horizon-Logistics"),
        ("Atlas_Meeting_Room_Technology_Proposal", "Atlas-Workplace"),
        ("Polaris_Carbon_Reporting_Guidelines", "Polaris-Sustainability"),
    ]:
        folder, label, _ = _actual(stem)
        lines.append(f"| {stem}.* | {exp} | {folder} | {label} | {_pts_disp(stem)} | {_note(stem)} |")

    lines += ["", "---", ""]

    # Category 2
    cat2_pts = sum(results[s][0] for s in [
        "Smart_Energy_Load_Management_Study",
        "Data_Quality_Monitoring_Framework",
        "Warehouse_Demand_Forecasting_Model",
        "Workspace_Access_Experience_Study",
        "Supplier_Emissions_Data_Framework",
    ] if results[s][0] >= 0)
    lines += [
        f"## Category 2 — Semantic Matches (scored {cat2_pts} / 10)",
        "",
        "| File | Expected | Actual Folder | Label | Pts | Notes |",
        "|------|----------|---------------|-------|-----|-------|",
    ]
    for stem, exp in [
        ("Smart_Energy_Load_Management_Study", "Aurora-Mobility"),
        ("Data_Quality_Monitoring_Framework", "Northstar-Analytics"),
        ("Warehouse_Demand_Forecasting_Model", "Horizon-Logistics"),
        ("Workspace_Access_Experience_Study", "Atlas-Workplace"),
        ("Supplier_Emissions_Data_Framework", "Polaris-Sustainability"),
    ]:
        folder, label, _ = _actual(stem)
        lines.append(f"| {stem}.* | {exp} | {folder} | {label} | {_pts_disp(stem)} | {_note(stem)} |")

    lines += ["", "---", ""]

    # Category 3
    cat3_pts = sum(results[s][0] for s in [
        "Enterprise_Data_Governance_Guide",
        "Energy_Consumption_Analytics_Report",
        "Operations_Performance_Review",
        "Access_Security_Architecture",
        "Vendor_Performance_Framework",
    ] if results[s][0] >= 0)
    lines += [
        f"## Category 3 — Ambiguous Matches (scored {cat3_pts} / 10)",
        "",
        "Pass = no recommendation OR low-confidence match to an acceptable folder.",
        "",
        "| File | Acceptable Folders | Actual Folder | Label | Pts | Notes |",
        "|------|--------------------|---------------|-------|-----|-------|",
    ]
    for stem, acceptable in [
        ("Enterprise_Data_Governance_Guide", "Northstar / Polaris"),
        ("Energy_Consumption_Analytics_Report", "Aurora / Polaris"),
        ("Operations_Performance_Review", "Horizon / Northstar"),
        ("Access_Security_Architecture", "Atlas / Aurora"),
        ("Vendor_Performance_Framework", "any"),
    ]:
        folder, label, _ = _actual(stem)
        lines.append(f"| {stem}.* | {acceptable} | {folder} | {label} | {_pts_disp(stem)} | {_note(stem)} |")

    lines += ["", "---", ""]

    # Category 4
    cat4_pts = sum(results[s][0] for s in [
        "Aurora_Analytics_Dashboard",
        "Horizon_Employee_Workplace_Report",
        "Polaris_Logistics_Data_Report",
        "Atlas_Sustainability_Review",
    ] if results[s][0] >= 0)
    lines += [
        f"## Category 4 — Wrong-Project Matches (scored {cat4_pts} / 8)",
        "",
        "| File | Filename Suggests | Correct Folder | Actual Folder | Label | Pts | Notes |",
        "|------|------------------|----------------|---------------|-------|-----|-------|",
    ]
    for stem, misleading, correct in [
        ("Aurora_Analytics_Dashboard", "Aurora-Mobility", "Northstar-Analytics"),
        ("Horizon_Employee_Workplace_Report", "Horizon-Logistics", "Atlas-Workplace"),
        ("Polaris_Logistics_Data_Report", "Polaris-Sustainability", "Horizon-Logistics"),
        ("Atlas_Sustainability_Review", "Atlas-Workplace", "Polaris-Sustainability"),
    ]:
        folder, label, _ = _actual(stem)
        lines.append(f"| {stem}.* | {misleading} | {correct} | {folder} | {label} | {_pts_disp(stem)} | {_note(stem)} |")

    lines += ["", "---", ""]

    # Category 5
    cat5_pts = sum(results[s][0] for s in [
        "Personal_Travel_Insurance",
        "Home_Garden_Improvement_Budget",
        "Photography_Equipment_Guide",
    ] if results[s][0] >= 0)
    lines += [
        f"## Category 5 — Unrelated Files (scored {cat5_pts} / 6)",
        "",
        "Pass = no recommendation shown.",
        "",
        "| File | Expected | Actual Folder | Pts | Notes |",
        "|------|----------|---------------|-----|-------|",
    ]
    for stem in [
        "Personal_Travel_Insurance",
        "Home_Garden_Improvement_Budget",
        "Photography_Equipment_Guide",
    ]:
        folder, label, _ = _actual(stem)
        lines.append(f"| {stem}.* | No recommendation | {folder} | {_pts_disp(stem)} | {_note(stem)} |")

    lines += ["", "---", ""]

    # Category 6
    cat6_pts = sum(results[s][0] for s in [
        "Aurora_Technical_Architecture_v2",
        "Data_Platform_Requirements_RevB",
        "Warehouse_Requirements_Updated",
        "Access_Control_Plan_v2",
        "Carbon_Reporting_Framework_2026_Update",
    ] if results[s][0] >= 0)
    lines += [
        f"## Category 6 — Duplicate / Updated Versions (scored {cat6_pts} / 10)",
        "",
        "| Downloaded File | Correct Folder | Actual Folder | Label | Pts | Notes |",
        "|----------------|----------------|---------------|-------|-----|-------|",
    ]
    for stem, correct in [
        ("Aurora_Technical_Architecture_v2", "Aurora-Mobility"),
        ("Data_Platform_Requirements_RevB", "Northstar-Analytics"),
        ("Warehouse_Requirements_Updated", "Horizon-Logistics"),
        ("Access_Control_Plan_v2", "Atlas-Workplace"),
        ("Carbon_Reporting_Framework_2026_Update", "Polaris-Sustainability"),
    ]:
        folder, label, _ = _actual(stem)
        lines.append(f"| {stem}.* | {correct} | {folder} | {label} | {_pts_disp(stem)} | {_note(stem)} |")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    recs = load_recommendations()
    scorecard = build_scorecard(recs)
    SCORECARD_PATH.write_text(scorecard, encoding="utf-8")
    print(f"Scorecard written to {SCORECARD_PATH}")

    # Quick summary to stdout
    tested = sum(1 for line in scorecard.splitlines() if "Files tested" in line)
    for line in scorecard.splitlines():
        if any(k in line for k in ("Files tested", "Points scored", "Score %")):
            print(" ", line.strip("| ").strip())
