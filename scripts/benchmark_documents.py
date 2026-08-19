#!/usr/bin/env python3
"""EAC placement benchmark — three real-world suites.

Simulates a real Documents folder with organised project subfolders,
a Downloads folder of incoming files, floating files at the root, and
some files that have already landed in the wrong folder.

Suite 1 — Downloads Placement (50 synthetic files)
    Simulates a new file arriving in Downloads.
    The scorer must recommend the correct project subfolder.

Suite 2 — Floating Files Placement (30 real files)
    Simulates files sitting loose at the Documents root (no subfolder).
    Same mechanism as Suite 1; measures real-world generalisation.

Suite 3 — Audit Detection (16 files)
    Simulates an audit over already-organised files.
    8 files are "misplaced" in the wrong project folder — the audit must
    detect them and recommend the correct folder.
    8 files are correctly placed — the audit must NOT flag them (false
    positive check).

Corpus (pre-index via EAC app):
    Enterprise-AI-Companion-Benchmark/synthetic-projects/   ← 8 project folders

Test files (indexed fresh each run, cleaned up after):
    Enterprise-AI-Companion-Benchmark/synthetic-downloads/  ← Suite 1
    OneDrive - Volvo Group/floating files/                  ← Suite 2
    (Suite 3 reuses Suite 1 indexed docs with different scoring perspective)

Audit thresholds (mirroring AuditService constants):
    _AUDIT_MIN_TOP_SCORE = 0.22   best non-current folder must reach this
    _AUDIT_MIN_DELTA     = 0.25   best_score − current_score must reach this

Prerequisites
-------------
- Backend must NOT be running (script needs exclusive SQLite/Qdrant access).
- synthetic-projects/ must already be indexed via the EAC app.
- Run from the backend/ directory with the backend venv activated.

Usage
-----
    cd backend
    python ../scripts/benchmark_documents.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT      = Path(__file__).resolve().parents[1]
BACKEND_SRC    = REPO_ROOT / "backend" / "src"
ONEDRIVE       = Path.home() / "OneDrive - Volvo Group"
BENCHMARK_ROOT = ONEDRIVE / "Enterprise-AI-Companion-Benchmark"
CORPUS_ROOT    = BENCHMARK_ROOT / "synthetic-projects"
DOWNLOADS_ROOT = BENCHMARK_ROOT / "synthetic-downloads"
FLOATING_ROOT  = ONEDRIVE / "floating files"

PROJECT_FOLDERS = [
    str(CORPUS_ROOT / name)
    for name in [
        "Atlas-Workplace",
        "Aurora-Mobility",
        "Cedar-Events",
        "Horizon-Logistics",
        "Meridian-Travel",
        "Northstar-Analytics",
        "Polaris-Sustainability",
        "Redwood-Facilities",
    ]
]

sys.path.insert(0, str(BACKEND_SRC))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / "backend" / ".env")
except ImportError:
    pass

# ── Audit thresholds (mirror AuditService._MIN_TOP_SCORE / _MIN_SCORE_DELTA) ─

_AUDIT_MIN_TOP_SCORE = 0.22
_AUDIT_MIN_DELTA     = 0.25

# ── Category constants ────────────────────────────────────────────────────────

# Suite 1 — Downloads
CAT_OBVIOUS   = "Obvious"
CAT_SEMANTIC  = "Semantic"
CAT_AMBIGUOUS = "Ambiguous"
CAT_WRONG     = "Wrong-Project"
CAT_UNRELATED = "Unrelated"
CAT_DUPLICATE = "Duplicate/Updated"
SUITE1_CATS   = {CAT_OBVIOUS, CAT_SEMANTIC, CAT_AMBIGUOUS, CAT_WRONG, CAT_UNRELATED, CAT_DUPLICATE}

# Suite 2 — Floating files
CAT_RW_OBVIOUS   = "RW-Obvious"
CAT_RW_SEMANTIC  = "RW-Semantic"
CAT_RW_WRONG     = "RW-Wrong-Project"
CAT_RW_AMBIGUOUS = "RW-Ambiguous"
CAT_RW_UNRELATED = "RW-Unrelated"
SUITE2_CATS = {CAT_RW_OBVIOUS, CAT_RW_SEMANTIC, CAT_RW_WRONG, CAT_RW_AMBIGUOUS, CAT_RW_UNRELATED}

_AMBIGUOUS_CATS = {CAT_AMBIGUOUS, CAT_RW_AMBIGUOUS}
_UNRELATED_CATS = {CAT_UNRELATED, CAT_RW_UNRELATED}

CATEGORY_NOTES = {
    CAT_OBVIOUS:      "filename + content name the project",
    CAT_SEMANTIC:     "content matches; no project name in filename",
    CAT_WRONG:        "misleading filename; content overrides to correct project",
    CAT_DUPLICATE:    "revised version; correct project folder still expected",
    CAT_AMBIGUOUS:    "multi-project; no-rec or any listed folder accepted",
    CAT_UNRELATED:    "personal files; expect no recommendation",
    CAT_RW_OBVIOUS:   "real file: filename clearly names the project",
    CAT_RW_SEMANTIC:  "real file: content matches; no project name in filename",
    CAT_RW_WRONG:     "real file: misleading filename; content overrides",
    CAT_RW_AMBIGUOUS: "real file: genuinely multi-project; any listed folder accepted",
    CAT_RW_UNRELATED: "real file: personal; expect no recommendation",
}

S1_ORDER = [CAT_OBVIOUS, CAT_SEMANTIC, CAT_WRONG, CAT_DUPLICATE, CAT_AMBIGUOUS, CAT_UNRELATED]
S2_ORDER = [CAT_RW_OBVIOUS, CAT_RW_SEMANTIC, CAT_RW_WRONG, CAT_RW_AMBIGUOUS, CAT_RW_UNRELATED]

# ── Suite 1 & 2: Placement test cases ─────────────────────────────────────────

@dataclass(frozen=True)
class PlacementTest:
    filename: str
    category: str
    # str = single correct folder, list = any of these acceptable, None = no recommendation
    expected: str | list[str] | None


PLACEMENT_TESTS: list[PlacementTest] = [
    # ── Obvious ───────────────────────────────────────────────────────────────
    PlacementTest("Aurora_Mobility_Deployment_Proposal.pdf",               CAT_OBVIOUS,   "Aurora-Mobility"),
    PlacementTest("Northstar_Analytics_Dashboard_Rollout.pptx",            CAT_OBVIOUS,   "Northstar-Analytics"),
    PlacementTest("Horizon_Logistics_Slotting_Report.pdf",                 CAT_OBVIOUS,   "Horizon-Logistics"),
    PlacementTest("Atlas_Workplace_Room_Technology_Spec.docx",             CAT_OBVIOUS,   "Atlas-Workplace"),
    PlacementTest("Polaris_Sustainability_Scope3_Plan.pdf",                CAT_OBVIOUS,   "Polaris-Sustainability"),
    PlacementTest("Meridian_Travel_Booking_Tool_Config.xlsx",              CAT_OBVIOUS,   "Meridian-Travel"),
    PlacementTest("Redwood_Facilities_Preventive_Maintenance_Schedule.xlsx", CAT_OBVIOUS, "Redwood-Facilities"),
    PlacementTest("Cedar_Events_Conference_Run_Sheet.docx",                CAT_OBVIOUS,   "Cedar-Events"),
    PlacementTest("Aurora_Mobility_Grid_Interconnection_Update.docx",      CAT_OBVIOUS,   "Aurora-Mobility"),
    PlacementTest("Northstar_Analytics_Data_Quality_Runbook.pdf",          CAT_OBVIOUS,   "Northstar-Analytics"),

    # ── Semantic ──────────────────────────────────────────────────────────────
    PlacementTest("Smart_Energy_Load_Management_Report.pdf",               CAT_SEMANTIC,  "Aurora-Mobility"),
    PlacementTest("Single_Source_Of_Truth_Reporting.docx",                 CAT_SEMANTIC,  "Northstar-Analytics"),
    PlacementTest("Warehouse_Picking_Efficiency_Study.pdf",                CAT_SEMANTIC,  "Horizon-Logistics"),
    PlacementTest("Hybrid_Office_Space_Utilisation.pptx",                  CAT_SEMANTIC,  "Atlas-Workplace"),
    PlacementTest("Corporate_Carbon_Footprint_Methodology.pdf",            CAT_SEMANTIC,  "Polaris-Sustainability"),
    PlacementTest("Managing_Business_Trip_Spend_And_Safety.docx",          CAT_SEMANTIC,  "Meridian-Travel"),
    PlacementTest("From_Reactive_To_Preventive_Building_Upkeep.pdf",       CAT_SEMANTIC,  "Redwood-Facilities"),
    PlacementTest("Running_A_Large_Industry_Conference.docx",              CAT_SEMANTIC,  "Cedar-Events"),
    PlacementTest("Depot_Charging_Off_Peak_Scheduling.xlsx",               CAT_SEMANTIC,  "Aurora-Mobility"),
    PlacementTest("Retail_Inventory_Analytics_Model.xlsx",                 CAT_SEMANTIC,  "Northstar-Analytics"),

    # ── Wrong-Project ─────────────────────────────────────────────────────────
    PlacementTest("Aurora_Analytics_Dashboard.pdf",                        CAT_WRONG,     "Northstar-Analytics"),
    PlacementTest("Northstar_Charging_Network_Plan.pdf",                   CAT_WRONG,     "Aurora-Mobility"),
    PlacementTest("Polaris_Warehouse_Slotting_Notes.docx",                 CAT_WRONG,     "Horizon-Logistics"),
    PlacementTest("Meridian_Room_Booking_Overview.pdf",                    CAT_WRONG,     "Atlas-Workplace"),
    PlacementTest("Horizon_Carbon_Disclosure_Draft.pdf",                   CAT_WRONG,     "Polaris-Sustainability"),
    PlacementTest("Atlas_Traveller_Duty_Of_Care.docx",                     CAT_WRONG,     "Meridian-Travel"),
    PlacementTest("Cedar_Preventive_Maintenance_Overview.pdf",             CAT_WRONG,     "Redwood-Facilities"),
    PlacementTest("Redwood_Conference_Sponsorship_Deck.pptx",              CAT_WRONG,     "Cedar-Events"),

    # ── Duplicate / Updated ───────────────────────────────────────────────────
    PlacementTest("Aurora_Technical_Architecture_v2.pdf",                  CAT_DUPLICATE, "Aurora-Mobility"),
    PlacementTest("Northstar_Requirements_Update.docx",                    CAT_DUPLICATE, "Northstar-Analytics"),
    PlacementTest("Horizon_Budget_Revised.xlsx",                           CAT_DUPLICATE, "Horizon-Logistics"),
    PlacementTest("Atlas_Deployment_Plan_Final.pdf",                       CAT_DUPLICATE, "Atlas-Workplace"),
    PlacementTest("Polaris_Risk_Assessment_Rev.pdf",                       CAT_DUPLICATE, "Polaris-Sustainability"),
    PlacementTest("Meridian_Overview_Copy.pdf",                            CAT_DUPLICATE, "Meridian-Travel"),
    PlacementTest("Redwood_Asset_Register_v3.xlsx",                        CAT_DUPLICATE, "Redwood-Facilities"),
    PlacementTest("Cedar_Status_Report_Latest.pdf",                        CAT_DUPLICATE, "Cedar-Events"),

    # ── Ambiguous ─────────────────────────────────────────────────────────────
    PlacementTest("Enterprise_Data_Governance_Framework.pdf",              CAT_AMBIGUOUS, ["Northstar-Analytics", "Polaris-Sustainability"]),
    PlacementTest("Energy_Consumption_Analytics_Report.pdf",               CAT_AMBIGUOUS, ["Aurora-Mobility", "Northstar-Analytics", "Polaris-Sustainability"]),
    PlacementTest("Supplier_Performance_Scorecard.xlsx",                   CAT_AMBIGUOUS, ["Horizon-Logistics", "Polaris-Sustainability", "Meridian-Travel"]),
    PlacementTest("Change_Management_And_Adoption_Playbook.docx",          CAT_AMBIGUOUS, ["Atlas-Workplace", "Northstar-Analytics", "Meridian-Travel", "Redwood-Facilities"]),
    PlacementTest("Data_Privacy_Impact_Assessment.pdf",                    CAT_AMBIGUOUS, ["Atlas-Workplace", "Meridian-Travel"]),
    PlacementTest("Vendor_Contract_Negotiation_Guide.docx",                CAT_AMBIGUOUS, ["Aurora-Mobility", "Horizon-Logistics", "Cedar-Events"]),
    PlacementTest("Sustainability_Reporting_Dashboard_Requirements.pdf",   CAT_AMBIGUOUS, ["Polaris-Sustainability", "Northstar-Analytics"]),
    PlacementTest("Facilities_Energy_Efficiency_Review.pdf",               CAT_AMBIGUOUS, ["Redwood-Facilities", "Polaris-Sustainability"]),

    # ── Unrelated ─────────────────────────────────────────────────────────────
    PlacementTest("Family_Travel_Insurance_Policy.pdf",                    CAT_UNRELATED, None),
    PlacementTest("Weeknight_Recipe_Collection.docx",                      CAT_UNRELATED, None),
    PlacementTest("Beginner_Photography_Guide.pdf",                        CAT_UNRELATED, None),
    PlacementTest("Kitchen_Renovation_Estimate.xlsx",                      CAT_UNRELATED, None),
    PlacementTest("Personal_Tax_Return_Notes.pdf",                         CAT_UNRELATED, None),
    PlacementTest("Movie_Night_Planning.xlsx",                             CAT_UNRELATED, None),

    # ── RW-Obvious ────────────────────────────────────────────────────────────
    PlacementTest("Aurora_Charging_Deployment_Notes.pdf",                  CAT_RW_OBVIOUS, "Aurora-Mobility"),
    PlacementTest("Cedar_Sponsorship_Tracker.xlsx",                        CAT_RW_OBVIOUS, "Cedar-Events"),
    PlacementTest("Northstar_Dashboard_Feedback.docx",                     CAT_RW_OBVIOUS, "Northstar-Analytics"),
    PlacementTest("Polaris_Emissions_Data_Notes.pdf",                      CAT_RW_OBVIOUS, "Polaris-Sustainability"),
    PlacementTest("Horizon_Warehouse_B_Notes.docx",                        CAT_RW_OBVIOUS, "Horizon-Logistics"),
    PlacementTest("Redwood_Work_Order_Backlog.xlsx",                        CAT_RW_OBVIOUS, "Redwood-Facilities"),
    PlacementTest("Event_Operating_Plan_Copy.pdf",                         CAT_RW_OBVIOUS, "Cedar-Events"),
    PlacementTest("Operations_Blueprint_v2.pdf",                           CAT_RW_OBVIOUS, "Horizon-Logistics"),

    # ── RW-Semantic ───────────────────────────────────────────────────────────
    PlacementTest("Analytics_Platform_Data_Quality.pdf",                   CAT_RW_SEMANTIC, "Northstar-Analytics"),
    PlacementTest("Data_Platform_Architecture_Draft.pdf",                  CAT_RW_SEMANTIC, "Northstar-Analytics"),
    PlacementTest("Environmental_Data_Analysis.pdf",                       CAT_RW_SEMANTIC, "Polaris-Sustainability"),
    PlacementTest("Fleet_Energy_Load_Study.pdf",                           CAT_RW_SEMANTIC, "Aurora-Mobility"),
    PlacementTest("Meeting_Room_Utilisation_Analysis.pptx",                CAT_RW_SEMANTIC, "Atlas-Workplace"),
    PlacementTest("Negotiated_Airfare_Savings.xlsx",                       CAT_RW_SEMANTIC, "Meridian-Travel"),
    PlacementTest("Reducing_Picking_Travel.pdf",                           CAT_RW_SEMANTIC, "Horizon-Logistics"),
    PlacementTest("Reporting_Methodology_Updated.docx",                    CAT_RW_SEMANTIC, "Polaris-Sustainability"),
    PlacementTest("Supplier_Emissions_Collection.pdf",                     CAT_RW_SEMANTIC, "Polaris-Sustainability"),
    PlacementTest("Month_End_Reporting_Bottlenecks.docx",                  CAT_RW_SEMANTIC, "Northstar-Analytics"),
    PlacementTest("Technical_Architecture_Final.pdf",                      CAT_RW_SEMANTIC, "Aurora-Mobility"),

    # ── RW-Wrong-Project ──────────────────────────────────────────────────────
    PlacementTest("Aurora_Data_Report.pdf",                                CAT_RW_WRONG, "Northstar-Analytics"),
    PlacementTest("Horizon_Travel_Policy_Notes.docx",                      CAT_RW_WRONG, "Meridian-Travel"),
    PlacementTest("Northstar_Site_Charging_Notes.docx",                    CAT_RW_WRONG, "Aurora-Mobility"),
    PlacementTest("Polaris_Room_Booking_Notes.pdf",                        CAT_RW_WRONG, "Atlas-Workplace"),

    # ── RW-Ambiguous ──────────────────────────────────────────────────────────
    PlacementTest("Contractor_And_Vendor_Compliance.docx",                 CAT_RW_AMBIGUOUS, ["Redwood-Facilities", "Horizon-Logistics"]),
    PlacementTest("Event_Or_Workplace_AV_Standard.docx",                   CAT_RW_AMBIGUOUS, ["Cedar-Events", "Atlas-Workplace"]),
    PlacementTest("Space_And_Travel_Cost_Review.xlsx",                     CAT_RW_AMBIGUOUS, ["Meridian-Travel", "Atlas-Workplace"]),

    # ── RW-Unrelated ──────────────────────────────────────────────────────────
    PlacementTest("Home_Renovation_Budget.xlsx",                           CAT_RW_UNRELATED, None),
    PlacementTest("Personal_Insurance_Information.pdf",                    CAT_RW_UNRELATED, None),
    PlacementTest("Personal_Travel_Plans.pdf",                             CAT_RW_UNRELATED, None),
    PlacementTest("Photography_Gear_Guide.pdf",                            CAT_RW_UNRELATED, None),
]

S1_TESTS = [t for t in PLACEMENT_TESTS if t.category in SUITE1_CATS]
S2_TESTS = [t for t in PLACEMENT_TESTS if t.category in SUITE2_CATS]

# ── Suite 3: Audit test cases ─────────────────────────────────────────────────

@dataclass(frozen=True)
class AuditTest:
    filename: str           # file from synthetic-downloads/ (already indexed by Suite 1)
    simulated_folder: str   # project folder name the file is "pretending" to live in
    correct_folder: str     # where it actually belongs
    expect_flagged: bool    # should the audit detect this?
    label: str              # human description


AUDIT_TESTS: list[AuditTest] = [
    # ── Misplaced: must be detected (expect_flagged=True) ─────────────────────
    # These use the wrong-project synthetic files, scored as if already sitting
    # inside the wrong folder. The audit must recommend the correct folder.
    AuditTest("Aurora_Analytics_Dashboard.pdf",      "Aurora-Mobility",      "Northstar-Analytics", True,  "BI dashboard in EV project"),
    AuditTest("Northstar_Charging_Network_Plan.pdf", "Northstar-Analytics",  "Aurora-Mobility",     True,  "EV charging plan in analytics project"),
    AuditTest("Polaris_Warehouse_Slotting_Notes.docx","Polaris-Sustainability","Horizon-Logistics",  True,  "Warehouse notes in sustainability project"),
    AuditTest("Meridian_Room_Booking_Overview.pdf",  "Meridian-Travel",      "Atlas-Workplace",     True,  "Room booking doc in travel project"),
    AuditTest("Horizon_Carbon_Disclosure_Draft.pdf", "Horizon-Logistics",    "Polaris-Sustainability",True, "Carbon disclosure in logistics project"),
    AuditTest("Atlas_Traveller_Duty_Of_Care.docx",   "Atlas-Workplace",      "Meridian-Travel",     True,  "Travel duty-of-care in workplace project"),
    AuditTest("Cedar_Preventive_Maintenance_Overview.pdf","Cedar-Events",     "Redwood-Facilities",  True,  "Maintenance doc in events project"),
    AuditTest("Redwood_Conference_Sponsorship_Deck.pptx","Redwood-Facilities","Cedar-Events",        True,  "Sponsorship deck in facilities project"),

    # ── Correctly placed: must NOT be flagged (expect_flagged=False) ──────────
    # These use obvious-match files. The audit should not suggest moving them.
    AuditTest("Aurora_Mobility_Deployment_Proposal.pdf",    "Aurora-Mobility",     "Aurora-Mobility",     False, "EV deployment in correct folder"),
    AuditTest("Northstar_Analytics_Dashboard_Rollout.pptx", "Northstar-Analytics", "Northstar-Analytics", False, "Dashboard rollout in correct folder"),
    AuditTest("Polaris_Sustainability_Scope3_Plan.pdf",     "Polaris-Sustainability","Polaris-Sustainability",False,"Scope 3 plan in correct folder"),
    AuditTest("Atlas_Workplace_Room_Technology_Spec.docx",  "Atlas-Workplace",     "Atlas-Workplace",     False, "Room tech spec in correct folder"),
    AuditTest("Horizon_Logistics_Slotting_Report.pdf",      "Horizon-Logistics",   "Horizon-Logistics",   False, "Slotting report in correct folder"),
    AuditTest("Cedar_Events_Conference_Run_Sheet.docx",     "Cedar-Events",        "Cedar-Events",        False, "Run sheet in correct folder"),
    AuditTest("Meridian_Travel_Booking_Tool_Config.xlsx",   "Meridian-Travel",     "Meridian-Travel",     False, "Booking config in correct folder"),
    AuditTest("Redwood_Facilities_Preventive_Maintenance_Schedule.xlsx","Redwood-Facilities","Redwood-Facilities",False,"Maintenance schedule in correct folder"),
]

# ── Scoring helpers ───────────────────────────────────────────────────────────

def _score_placement(tc: PlacementTest, top_folder: str | None, all_top3: list[str]) -> tuple[int, str]:
    """Return (pts 0/1/2, verdict) for a placement test case."""
    top  = Path(top_folder).name if top_folder else None
    top3 = [Path(f).name for f in all_top3]

    if tc.category in _UNRELATED_CATS:
        return (2, "PASS  correct rejection") if top is None else (0, f"FAIL  wrongly placed → {top}")

    if tc.category in _AMBIGUOUS_CATS:
        acceptable: list[str] = tc.expected  # type: ignore[assignment]
        if top is None:
            return 2, "PASS  no confident rec (correct for ambiguous)"
        if top in acceptable:
            return 2, f"PASS  plausible → {top}"
        if any(f in acceptable for f in top3):
            return 1, f"PART  acceptable in top-3; top1={top}"
        return 0, f"FAIL  wrong → {top} (acceptable: {', '.join(acceptable)})"

    expected: str = tc.expected  # type: ignore[assignment]
    if top is None:
        return 0, f"FAIL  no recommendation (expected {expected})"
    if top == expected:
        return 2, f"PASS  → {top}"
    if expected in top3:
        return 1, f"PART  correct in top-3; top1={top}"
    return 0, f"FAIL  → {top} (expected {expected})"


def _score_audit(
    at: AuditTest,
    would_flag: bool,
    best_folder: str | None,
    current_score: float,
    top_score: float,
    delta: float,
) -> tuple[int, str]:
    """Return (pts 0/1/2, verdict) for an audit test case."""
    best = Path(best_folder).name if best_folder else None

    if at.expect_flagged:
        if not would_flag:
            return 0, f"FAIL  not detected (current={current_score:.3f}, best={top_score:.3f}, delta={delta:.3f})"
        if best == at.correct_folder:
            return 2, f"PASS  flagged → {best} (delta={delta:.3f})"
        return 1, f"PART  flagged but → {best}, expected {at.correct_folder}"
    else:
        if would_flag:
            return 0, f"FAIL  false positive → {best} (delta={delta:.3f})"
        return 2, f"PASS  correctly left in place (delta={delta:.3f})"


# ── Cleanup ───────────────────────────────────────────────────────────────────

async def _cleanup(conn, chunk_repo, doc_ids: list[str]) -> None:
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
            await conn.execute(f"DELETE FROM graph_entities WHERE id IN ({ph})", ent_ids)

        await conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        await conn.commit()


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    # Validate paths
    for label, path in [
        ("synthetic-projects/ (corpus)", CORPUS_ROOT),
        ("synthetic-downloads/ (Suite 1)", DOWNLOADS_ROOT),
        ("floating files/ (Suite 2)", FLOATING_ROOT),
    ]:
        if not path.exists():
            print(f"ERROR: {label} not found at {path}")
            sys.exit(1)

    missing = [p for p in PROJECT_FOLDERS if not Path(p).is_dir()]
    if missing:
        print("ERROR: missing project folders:")
        for p in missing:
            print(f"  {p}")
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
    await conn.execute("PRAGMA busy_timeout=30000")
    qdrant = QdrantProvider()
    qdrant.initialize()
    graph = SQLiteGraphProvider(conn)
    await graph.initialize()

    embedding_service = EmbeddingService()
    qdrant_client     = qdrant.get_client()
    doc_repo          = DocumentRepository(conn)
    chunk_repo        = ChunkRepository(conn, qdrant_client)

    file_indexer = FileIndexer(
        doc_repo, chunk_repo, embedding_service, graph_provider=graph,
    )
    scorer = PlacementScorer(
        graph_score_port=SqliteGraphScoreAdapter(conn),
        rerank_port=HybridRerankAdapter(conn, embedding_service, qdrant_client),
    )

    # ── Verify corpus ──────────────────────────────────────────────────────
    async with conn.execute(
        "SELECT COUNT(*) FROM documents WHERE file_path LIKE ?",
        (str(CORPUS_ROOT).replace("\\", "/") + "%",),
    ) as cur:
        row = await cur.fetchone()
    corpus_count = row[0] if row else 0
    if corpus_count == 0:
        print(f"\nWARNING: No corpus documents found. Index synthetic-projects/ via the EAC app first.\n")
    else:
        print(f"Corpus: {corpus_count} indexed document(s) across 8 project folders\n")

    # ── Index Suite 1 (Downloads) ──────────────────────────────────────────
    print(f"Suite 1 — indexing {len(S1_TESTS)} synthetic download file(s)…")
    print("(LLM entity extraction — several minutes)\n")
    r1 = await file_indexer.index_workspace(str(DOWNLOADS_ROOT))
    print(f"  {r1.files_indexed} indexed, {r1.files_skipped} skipped, {len(r1.errors)} errors\n")

    # ── Index Suite 2 (Floating files) ────────────────────────────────────
    print(f"Suite 2 — indexing {len(S2_TESTS)} real floating file(s)…\n")
    r2 = await file_indexer.index_workspace(str(FLOATING_ROOT))
    print(f"  {r2.files_indexed} indexed, {r2.files_skipped} skipped, {len(r2.errors)} errors\n")

    # ── Score Suite 1 ─────────────────────────────────────────────────────
    print(f"Scoring Suite 1 ({len(S1_TESTS)} files) — Downloads placement…")

    @dataclass
    class PlacementRow:
        tc: PlacementTest
        top_folder: str | None
        all_top3: list[str]
        score_val: float
        pts: int
        verdict: str
        skipped: bool = False

    s1_rows: list[PlacementRow] = []
    s1_doc_ids: list[str] = []

    for tc in S1_TESTS:
        file_path = str(DOWNLOADS_ROOT / tc.filename)
        doc = await doc_repo.get_by_path(file_path)
        if doc is None:
            s1_rows.append(PlacementRow(tc=tc, top_folder=None, all_top3=[], score_val=0.0,
                                        pts=0, verdict="SKIP  not in DB", skipped=True))
            continue
        s1_doc_ids.append(doc.id)
        scores = await scorer.score_all(doc.id, PROJECT_FOLDERS, file_path=file_path)
        top_folder = scores[0]["folder"] if scores else None
        all_top3   = [s["folder"] for s in scores]
        score_val  = scores[0]["score"] if scores else 0.0
        pts, verdict = _score_placement(tc, top_folder, all_top3)
        s1_rows.append(PlacementRow(tc=tc, top_folder=top_folder, all_top3=all_top3,
                                    score_val=score_val, pts=pts, verdict=verdict))

    # ── Score Suite 2 ─────────────────────────────────────────────────────
    print(f"Scoring Suite 2 ({len(S2_TESTS)} files) — Floating file placement…")

    s2_rows: list[PlacementRow] = []
    s2_doc_ids: list[str] = []

    for tc in S2_TESTS:
        file_path = str(FLOATING_ROOT / tc.filename)
        doc = await doc_repo.get_by_path(file_path)
        if doc is None:
            s2_rows.append(PlacementRow(tc=tc, top_folder=None, all_top3=[], score_val=0.0,
                                        pts=0, verdict="SKIP  not in DB", skipped=True))
            continue
        s2_doc_ids.append(doc.id)
        scores = await scorer.score_all(doc.id, PROJECT_FOLDERS, file_path=file_path)
        top_folder = scores[0]["folder"] if scores else None
        all_top3   = [s["folder"] for s in scores]
        score_val  = scores[0]["score"] if scores else 0.0
        pts, verdict = _score_placement(tc, top_folder, all_top3)
        s2_rows.append(PlacementRow(tc=tc, top_folder=top_folder, all_top3=all_top3,
                                    score_val=score_val, pts=pts, verdict=verdict))

    # ── Score Suite 3 (Audit) ──────────────────────────────────────────────
    # Reuses files already indexed in Suite 1. For each audit test:
    #   - Treat simulated_folder as the file's "current home"
    #   - Score the file against all OTHER project folders
    #   - Compute delta = best_other_score - current_score
    #   - Apply audit thresholds: flag if delta >= 0.10 AND best_score >= 0.22
    print(f"Scoring Suite 3 ({len(AUDIT_TESTS)} files) — Audit detection…")

    @dataclass
    class AuditRow:
        at: AuditTest
        current_score: float
        top_score: float
        best_folder: str | None
        delta: float
        would_flag: bool
        pts: int
        verdict: str
        skipped: bool = False

    s3_rows: list[AuditRow] = []

    folder_by_name = {Path(f).name: f for f in PROJECT_FOLDERS}

    for at in AUDIT_TESTS:
        file_path = str(DOWNLOADS_ROOT / at.filename)
        doc = await doc_repo.get_by_path(file_path)
        if doc is None:
            s3_rows.append(AuditRow(at=at, current_score=0.0, top_score=0.0, best_folder=None,
                                    delta=0.0, would_flag=False, pts=0,
                                    verdict="SKIP  not in DB (Suite 1 indexing failed?)", skipped=True))
            continue

        simulated_folder_path = folder_by_name.get(at.simulated_folder, "")
        other_folders = [f for f in PROJECT_FOLDERS if Path(f).name != at.simulated_folder]

        # Score against "current" (simulated) folder
        current_score = await scorer.score_one(doc.id, simulated_folder_path, file_path=file_path) \
            if simulated_folder_path else 0.0

        # Score against all other folders
        scores = await scorer.score_all(doc.id, other_folders, file_path=file_path)
        top_score  = scores[0]["score"]  if scores else 0.0
        best_folder = scores[0]["folder"] if scores else None
        delta = top_score - current_score

        would_flag = (top_score >= _AUDIT_MIN_TOP_SCORE) and (delta >= _AUDIT_MIN_DELTA)
        pts, verdict = _score_audit(at, would_flag, best_folder, current_score, top_score, delta)

        s3_rows.append(AuditRow(at=at, current_score=current_score, top_score=top_score,
                                best_folder=best_folder, delta=delta,
                                would_flag=would_flag, pts=pts, verdict=verdict))

    # ── Cleanup ────────────────────────────────────────────────────────────
    all_doc_ids = list(dict.fromkeys(s1_doc_ids + s2_doc_ids))
    print(f"\nCleaning up {len(all_doc_ids)} indexed test document(s)…")
    await _cleanup(conn, chunk_repo, all_doc_ids)
    await close_db(conn)
    qdrant.close()
    await graph.close()

    # ── Scorecard ──────────────────────────────────────────────────────────
    def _pct(pts: int, mx: int) -> str:
        return f"{100 * pts // mx}%" if mx else "n/a"

    def _bar(pts: int, mx: int, width: int = 20) -> str:
        filled = pts * width // mx if mx else 0
        return "█" * filled + "░" * (width - filled)

    W = 55
    print()
    print("=" * 115)
    print("  EAC PLACEMENT BENCHMARK  —  3 suites  |  80 placement tests  |  16 audit tests")
    print("=" * 115)

    # ── Suite 1 ────────────────────────────────────────────────────────────
    s1_pts   = sum(r.pts for r in s1_rows if not r.skipped)
    s1_max   = sum(2     for r in s1_rows if not r.skipped)
    s1_skip  = sum(1     for r in s1_rows if r.skipped)
    s1_rows_by_cat: dict[str, list[PlacementRow]] = {c: [] for c in S1_ORDER}
    for r in s1_rows:
        s1_rows_by_cat[r.tc.category].append(r)

    print(f"\n  ┌─ SUITE 1 — Downloads Placement  {s1_pts}/{s1_max}  ({_pct(s1_pts, s1_max)})"
          + (f"  [{s1_skip} skipped]" if s1_skip else ""))
    print(f"  │  Simulates files arriving in Downloads → scored against 8 project folders")

    for cat in S1_ORDER:
        cat_rows = s1_rows_by_cat[cat]
        if not cat_rows:
            continue
        c_pts = sum(r.pts for r in cat_rows if not r.skipped)
        c_max = sum(2     for r in cat_rows if not r.skipped)
        print(f"\n  │  -- {cat}  {c_pts}/{c_max}  {CATEGORY_NOTES[cat]}")
        for r in cat_rows:
            folder_str = Path(r.top_folder).name if r.top_folder else "(none)"
            score_str  = f"{r.score_val:.3f}" if r.score_val > 0 else "    -"
            bar = "██" if r.pts == 2 else ("█░" if r.pts == 1 else "░░")
            print(f"  │    {r.tc.filename:<{W}} {folder_str:<24} {score_str}  [{bar}] {r.verdict}")

    # ── Suite 2 ────────────────────────────────────────────────────────────
    s2_pts   = sum(r.pts for r in s2_rows if not r.skipped)
    s2_max   = sum(2     for r in s2_rows if not r.skipped)
    s2_skip  = sum(1     for r in s2_rows if r.skipped)
    s2_rows_by_cat: dict[str, list[PlacementRow]] = {c: [] for c in S2_ORDER}
    for r in s2_rows:
        s2_rows_by_cat[r.tc.category].append(r)

    print(f"\n  ├─ SUITE 2 — Floating File Placement  {s2_pts}/{s2_max}  ({_pct(s2_pts, s2_max)})"
          + (f"  [{s2_skip} skipped]" if s2_skip else ""))
    print(f"  │  Simulates files loose at Documents root (no subfolder)")

    for cat in S2_ORDER:
        cat_rows = s2_rows_by_cat[cat]
        if not cat_rows:
            continue
        c_pts = sum(r.pts for r in cat_rows if not r.skipped)
        c_max = sum(2     for r in cat_rows if not r.skipped)
        print(f"\n  │  -- {cat}  {c_pts}/{c_max}  {CATEGORY_NOTES[cat]}")
        for r in cat_rows:
            folder_str = Path(r.top_folder).name if r.top_folder else "(none)"
            score_str  = f"{r.score_val:.3f}" if r.score_val > 0 else "    -"
            bar = "██" if r.pts == 2 else ("█░" if r.pts == 1 else "░░")
            print(f"  │    {r.tc.filename:<{W}} {folder_str:<24} {score_str}  [{bar}] {r.verdict}")

    # ── Suite 3 ────────────────────────────────────────────────────────────
    s3_pts    = sum(r.pts for r in s3_rows if not r.skipped)
    s3_max    = sum(2     for r in s3_rows if not r.skipped)
    s3_skip   = sum(1     for r in s3_rows if r.skipped)
    misplaced = [r for r in s3_rows if r.at.expect_flagged]
    correct   = [r for r in s3_rows if not r.at.expect_flagged]
    mp_pts    = sum(r.pts for r in misplaced if not r.skipped)
    mp_max    = sum(2     for r in misplaced if not r.skipped)
    fp_pts    = sum(r.pts for r in correct   if not r.skipped)
    fp_max    = sum(2     for r in correct   if not r.skipped)

    print(f"\n  └─ SUITE 3 — Audit Detection  {s3_pts}/{s3_max}  ({_pct(s3_pts, s3_max)})"
          + (f"  [{s3_skip} skipped]" if s3_skip else ""))
    print(f"     Simulates an audit run over already-organised files")
    print(f"     Thresholds: top_score ≥ {_AUDIT_MIN_TOP_SCORE}  AND  delta ≥ {_AUDIT_MIN_DELTA}")

    print(f"\n     -- Misplaced files (must be detected)  {mp_pts}/{mp_max}")
    for r in misplaced:
        best = Path(r.best_folder).name if r.best_folder else "(none)"
        bar  = "██" if r.pts == 2 else ("█░" if r.pts == 1 else "░░")
        print(f"       {r.at.label:<45} [{bar}] {r.verdict}")
        print(f"         file: {r.at.filename}")
        print(f"         simulated-in={r.at.simulated_folder:<22} current={r.current_score:.3f}  best={best} ({r.top_score:.3f})  delta={r.delta:.3f}")

    print(f"\n     -- Correctly placed (must NOT be flagged)  {fp_pts}/{fp_max}")
    for r in correct:
        bar = "██" if r.pts == 2 else "░░"
        print(f"       {r.at.label:<45} [{bar}] {r.verdict}")

    # ── Grand totals ───────────────────────────────────────────────────────
    all_pts = s1_pts + s2_pts + s3_pts
    all_max = s1_max + s2_max + s3_max

    print()
    print("=" * 115)
    print(f"  OVERALL  {all_pts}/{all_max}  ({_pct(all_pts, all_max)})")
    print()
    print(f"  Suite 1  Downloads   {s1_pts:>3}/{s1_max:<3}  {_pct(s1_pts, s1_max):>4}  {_bar(s1_pts, s1_max)}  50 synthetic files")
    print(f"  Suite 2  Floating    {s2_pts:>3}/{s2_max:<3}  {_pct(s2_pts, s2_max):>4}  {_bar(s2_pts, s2_max)}  30 real files")
    print(f"  Suite 3  Audit       {s3_pts:>3}/{s3_max:<3}  {_pct(s3_pts, s3_max):>4}  {_bar(s3_pts, s3_max)}  8 misplaced + 8 correct")
    print(f"             ├─ detect {mp_pts:>3}/{mp_max:<3}  {_pct(mp_pts, mp_max):>4}  (catch misplaced files)")
    print(f"             └─ no FP  {fp_pts:>3}/{fp_max:<3}  {_pct(fp_pts, fp_max):>4}  (don't move correct files)")
    print()
    print("=" * 115)


if __name__ == "__main__":
    asyncio.run(main())
