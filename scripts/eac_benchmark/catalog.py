"""Catalogue of download and floating test files with embedded ground truth.

Every test file is described once, as a :class:`TestFile`, carrying both its
rendered content and the ground-truth expectation used to score the Enterprise
AI Companion. The same objects drive document generation (``generate.py``) and
the ground-truth / matrix / scorecard reports (``reports.py``), so the corpus and
its answer key can never drift apart.

Categories
----------
``obvious``     Filename and content clearly name one project (sanity checks).
``semantic``    Filename hides the project; content implies it (needs reading).
``ambiguous``   Content plausibly fits two or more projects (ask the user).
``wrong``       Filename points at project A; content is about project B.
``unrelated``   Personal / off-topic; must yield no project recommendation.
``duplicate``   A revised copy of an existing project document.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from scripts.benchmark_corpus.common import SheetSpec, SlideSpec

from .data import PROJECTS_BY_KEY, Project

# Expected-action vocabulary (kept in one place for report consistency).
SUGGEST_MOVE = "SUGGEST_MOVE"
ASK_USER = "ASK_USER"
SUGGEST_LOW = "SUGGEST_WITH_LOW_CONFIDENCE"
NO_REC = "NO_RECOMMENDATION"
POSSIBLE_DUP = "POSSIBLE_DUPLICATE"
UPDATED_VERSION = "UPDATED_VERSION"

# Relationship labels for duplicate/updated cases.
REL_DUPLICATE = "DUPLICATE"
REL_UPDATED = "UPDATED_VERSION"
REL_REVISED = "REVISED_VERSION"
REL_POSSIBLE = "POSSIBLE_DUPLICATE"


@dataclass
class TestFile:
    """A single benchmark file plus its ground-truth expectation."""

    filename: str
    fmt: str                       # "pdf" | "docx" | "xlsx" | "pptx"
    category: str                  # obvious|semantic|ambiguous|wrong|unrelated|duplicate
    scope: str                     # "download" | "floating"
    expected_project: str | None   # project key, or None for unrelated
    expected_action: str
    confidence: str                # High | Medium | Low | None
    reason: str
    candidates: list[str] = field(default_factory=list)  # ambiguous destinations
    misleading_filename: bool = False
    semantic_required: bool = False
    semantic_evidence: str = ""
    existing_file: str = ""        # "Project-Key/File.ext" for duplicates
    relationship: str = ""         # REL_* for duplicates
    blocks: list = field(default_factory=list)           # pdf/docx
    sheets: list = field(default_factory=list)           # xlsx
    slides: tuple | None = None    # (title, subtitle, [SlideSpec]) for pptx


def _p(key: str) -> Project:
    return PROJECTS_BY_KEY[key]


# --- Content helpers ---------------------------------------------------------
def _report(title: str, meta: str, sections: list[tuple[str, object]]) -> list:
    """Assemble ordered blocks for a PDF/DOCX report from titled sections."""
    blocks: list = [("title", title), ("para", meta)]
    for heading, content in sections:
        blocks.append(("heading", heading))
        if isinstance(content, list):
            if content and isinstance(content[0], (list, tuple)) and heading.lower().startswith("table"):
                blocks.append(content)  # already a ("table", ...) payload
            else:
                blocks.append(("bullets", content))
        elif isinstance(content, tuple):
            blocks.append(content)      # a raw ("table", payload) block
        else:
            blocks.append(("para", content))
    return blocks


def _vocab_line(p: Project, a: int, b: int, c: int, d: int) -> str:
    v = p.vocab
    return (f"Key themes include {v[a]}, {v[b]}, {v[c]}, and {v[d]}. These recur "
            "throughout the analysis and frame the recommendations that follow.")


# ===========================================================================
# DOWNLOADS
# ===========================================================================

# --- Category 1: Obvious matches (>=10) ------------------------------------
def _obvious_downloads() -> list[TestFile]:
    files: list[TestFile] = []

    am = _p("Aurora-Mobility")
    files.append(TestFile(
        filename="Aurora_Mobility_Deployment_Proposal.pdf", fmt="pdf",
        category="obvious", scope="download", expected_project=am.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Filename and content both name Aurora Mobility and its EV charging deployment.",
        blocks=_report(
            "Aurora Mobility — Deployment Proposal (Vendor Draft)",
            "Prepared by VoltGrid Systems for Aurora Mobility  |  Ref: VG-AM-2026-114  |  2026-04-22",
            [
                ("Proposal Summary",
                 "VoltGrid Systems proposes a phased deployment of charging stations for the "
                 "Aurora Mobility network across the three service zones. The proposal aligns "
                 "to the Aurora Mobility component baseline and the depot load caps agreed "
                 "during programme initiation."),
                ("Scope of Supply",
                 [f"Charging stations and OCPP 2.0.1 controllers for Zone 1 depot charging",
                  "Commissioning of fleet charging bays with local load balancing",
                  "Integration with the Energy Management Core for off-peak tariff scheduling"]),
                ("Delivery Approach",
                 "Deployment follows the Aurora Mobility phase plan, beginning with the "
                 "Foundation phase and Zone 1, then expanding to Zones 2 and 3. Grid "
                 "interconnection milestones are respected so that aggregate depot load "
                 "remains below the connection limit."),
                ("Commercial Notes",
                 _vocab_line(am, 0, 1, 2, 4)),
            ]),
    ))

    ns = _p("Northstar-Analytics")
    files.append(TestFile(
        filename="Northstar_Analytics_Dashboard_Rollout.pptx", fmt="pptx",
        category="obvious", scope="download", expected_project=ns.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Filename and slides both name Northstar Analytics and its BI dashboard rollout.",
        slides=(
            "Northstar Analytics", "Certified Dashboard Rollout  |  Vendor Briefing",
            [
                SlideSpec(title="Rollout Overview",
                          subtitle="Prismview BI rollout plan for the Northstar Analytics certified dashboards."),
                SlideSpec(title="Certified Dashboards",
                          bullets=["Sales performance by store and region",
                                   "Inventory position and stock-out risk",
                                   "Customer segmentation from the semantic model"]),
                SlideSpec(title="Governance",
                          bullets=["Row-level security by business unit",
                                   "Metrics certified only through the semantic model",
                                   "Data-quality alerts routed to data owners"]),
                SlideSpec(title="Adoption",
                          bullets=["Retire legacy spreadsheet reports",
                                   "Analyst enablement for self-service analytics"]),
            ]),
    ))

    hl = _p("Horizon-Logistics")
    files.append(TestFile(
        filename="Horizon_Logistics_Slotting_Report.pdf", fmt="pdf",
        category="obvious", scope="download", expected_project=hl.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Filename and content name Horizon Logistics and its slotting optimisation work.",
        blocks=_report(
            "Horizon Logistics — Slotting Optimisation Pilot Report",
            "Continental Distribution Partners  |  Ref: HL-PILOT-07  |  2026-08-11",
            [
                ("Pilot Result",
                 "The Horizon Logistics slotting pilot at Warehouse B reduced average picking "
                 "travel distance and eased dock congestion during outbound waves. Results "
                 "support extending slotting optimisation to the remaining warehouses."),
                ("Measured Improvements",
                 [f"Picking travel distance reduced against the Warehouse B baseline",
                  "Fewer replenishment stock-outs on high-velocity SKUs",
                  "Improved outbound on-time dispatch during peak waves"]),
                ("Recommendation",
                 "Proceed with forecasting and replenishment rollout, then dock scheduling, "
                 "per the Horizon Logistics operations blueprint. " + _vocab_line(hl, 1, 3, 6, 8)),
            ]),
    ))

    at = _p("Atlas-Workplace")
    files.append(TestFile(
        filename="Atlas_Workplace_Room_Technology_Spec.docx", fmt="docx",
        category="obvious", scope="download", expected_project=at.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Filename and content name Atlas Workplace and its meeting-room technology.",
        blocks=_report(
            "Atlas Workplace — Room Technology Standard (Vendor Spec)",
            "RoomSync for Atlas Workplace  |  Ref: RS-AT-STD-02  |  2026-04-19",
            [
                ("Purpose",
                 "This specification details the standardised meeting-room technology for the "
                 "Atlas Workplace programme, covering door panels, audio-visual control, and "
                 "occupancy sensing across the three buildings."),
                ("Standard Components",
                 ["Door panels showing real-time room availability",
                  "One-touch AV control integrated with room booking",
                  "Aggregate occupancy sensors feeding workplace analytics"]),
                ("Notes",
                 _vocab_line(at, 1, 2, 3, 6)),
            ]),
    ))

    ps = _p("Polaris-Sustainability")
    files.append(TestFile(
        filename="Polaris_Sustainability_Scope3_Plan.pdf", fmt="pdf",
        category="obvious", scope="download", expected_project=ps.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Filename and content name Polaris Sustainability and its Scope 3 programme.",
        blocks=_report(
            "Polaris Sustainability — Scope 3 Supplier Engagement Plan",
            "Evergreen Holdings  |  Ref: PS-S3-PLAN  |  2026-04-25",
            [
                ("Objective",
                 "This plan describes how Polaris Sustainability will collect Scope 3 supplier "
                 "emissions data covering the majority of purchased-goods spend, using tiered "
                 "engagement and estimation fallback where responses are missing."),
                ("Engagement Tiers",
                 ["Tier 1: strategic suppliers with primary emissions data",
                  "Tier 2: significant suppliers with questionnaire-based data",
                  "Tier 3: remaining suppliers estimated from spend-based factors"]),
                ("Assurance",
                 "Every reported figure retains an audit trail and records the estimation "
                 "method used, supporting external assurance. " + _vocab_line(ps, 0, 2, 3, 6)),
            ]),
    ))

    mt = _p("Meridian-Travel")
    files.append(TestFile(
        filename="Meridian_Travel_Booking_Tool_Config.xlsx", fmt="xlsx",
        category="obvious", scope="download", expected_project=mt.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Filename and workbook name Meridian Travel and its online booking tool configuration.",
        sheets=[
            SheetSpec(
                title="Policy Rules",
                intro=["Meridian Travel — Online Booking Tool Policy Configuration",
                       "Vendor: Voyanta OBT  |  Ref: MT-OBT-CFG"],
                header=["Rule", "Threshold", "Approval"],
                rows=[
                    ["Domestic flight", "Economy only", "Line manager"],
                    ["International flight > 6h", "Premium economy", "Department head"],
                    ["Hotel per night", "EUR 180 cap", "Auto-approve under cap"],
                    ["Out-of-policy booking", "Any", "Pre-trip approval required"],
                ]),
            SheetSpec(
                title="Duty of Care",
                intro=["Traveller tracking and alert routing for duty of care."],
                header=["Event", "Action"],
                rows=[
                    ["High-risk destination", "Pre-trip risk briefing"],
                    ["Disruption alert", "Notify affected travellers"],
                    ["SOS", "Escalate to traveller care team"],
                ]),
        ],
    ))

    rf = _p("Redwood-Facilities")
    files.append(TestFile(
        filename="Redwood_Facilities_Preventive_Maintenance_Schedule.xlsx", fmt="xlsx",
        category="obvious", scope="download", expected_project=rf.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Filename and workbook name Redwood Facilities and its preventive maintenance schedule.",
        sheets=[
            SheetSpec(
                title="PM Schedule",
                intro=["Redwood Facilities — Preventive Maintenance Schedule",
                       "System: MaintainPro CMMS  |  Ref: RF-PM-SCH"],
                header=["Asset", "Building", "Interval", "Criticality"],
                rows=[
                    ["Chiller CH-01", "Harbor House", "Quarterly", "Critical"],
                    ["Passenger lift LF-03", "Harbor House", "Monthly", "Critical"],
                    ["AHU-12", "Dockside Tower", "Quarterly", "High"],
                    ["Fire pump FP-02", "Dockside Tower", "Monthly", "Critical"],
                    ["Standby generator GN-01", "Quayside Annex", "Monthly", "Critical"],
                ]),
        ],
    ))

    ce = _p("Cedar-Events")
    files.append(TestFile(
        filename="Cedar_Events_Conference_Run_Sheet.docx", fmt="docx",
        category="obvious", scope="download", expected_project=ce.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Filename and content name Cedar Events and its flagship conference logistics.",
        blocks=_report(
            "Cedar Events — Flagship Conference Run Sheet",
            "Summit Communications  |  Ref: CE-RUN-01  |  2026-10-28",
            [
                ("Overview",
                 "This run sheet covers on-site logistics for the Cedar Events flagship "
                 "conference for 1,200 attendees, including check-in, agenda flow, and AV cues."),
                ("On-site Logistics",
                 ["Multiple check-in lanes with pre-printed badges and app QR",
                  "Agenda and speaker changeovers managed against the master schedule",
                  "Staging and live streaming handled by StageWorks AV"]),
                ("Attendee Experience",
                 _vocab_line(ce, 0, 2, 4, 6)),
            ]),
    ))

    # Two more obvious to comfortably exceed 10.
    files.append(TestFile(
        filename="Aurora_Mobility_Grid_Interconnection_Update.docx", fmt="docx",
        category="obvious", scope="download", expected_project=am.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Filename and content name Aurora Mobility and its grid interconnection works.",
        blocks=_report(
            "Aurora Mobility — Grid Interconnection Update",
            "NordConnect Utilities for Aurora Mobility  |  Ref: NC-AM-INT-9  |  2026-05-06",
            [
                ("Status",
                 "Interconnection studies for Zones 1 and 2 of the Aurora Mobility charging "
                 "network are complete. Zone 1 can support the agreed depot load cap; Zone 2 "
                 "requires a minor transformer upgrade before depot charging expands."),
                ("Actions",
                 ["Confirm Zone 2 transformer upgrade window",
                  "Update the Energy Management Core load limits for Zone 1",
                  "Schedule metering reconciliation with the distribution operator"]),
                ("Themes", _vocab_line(am, 5, 7, 8, 9)),
            ]),
    ))

    files.append(TestFile(
        filename="Northstar_Analytics_Data_Quality_Runbook.pdf", fmt="pdf",
        category="obvious", scope="download", expected_project=ns.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Filename and content name Northstar Analytics and its data-quality monitoring.",
        blocks=_report(
            "Northstar Analytics — Data Quality Runbook",
            "Lakeside Retail Group  |  Ref: NS-DQ-RUN  |  2026-05-02",
            [
                ("Purpose",
                 "This runbook defines how the Northstar Analytics platform monitors data "
                 "quality across sales and inventory feeds and how alerts are routed to data "
                 "owners for resolution before metrics are certified."),
                ("Checks",
                 ["Completeness of daily store feeds",
                  "Referential integrity against the semantic model",
                  "Anomaly detection on key certified metrics"]),
                ("Escalation", _vocab_line(ns, 6, 7, 9, 11)),
            ]),
    ))

    return files


# --- Category 2: Semantic matches (>=10) -----------------------------------
def _semantic_downloads() -> list[TestFile]:
    files: list[TestFile] = []

    am = _p("Aurora-Mobility")
    files.append(TestFile(
        filename="Smart_Energy_Load_Management_Report.pdf", fmt="pdf",
        category="semantic", scope="download", expected_project=am.key,
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="No project name, but content is squarely EV charging, depot load, and off-peak tariffs.",
        semantic_required=True,
        semantic_evidence="EV charging, fleet/depot charging, off-peak tariff, grid connection limit, load balancing.",
        blocks=_report(
            "Smart Energy Load Management for Vehicle Fleets",
            "Independent Research Note  |  Ref: SE-LM-2026  |  2026-04-28",
            [
                ("Context",
                 "As commercial fleets electrify, depot charging concentrates large loads that "
                 "can breach grid connection limits. Managing when and how vehicles charge is "
                 "now as important as installing the charging stations themselves."),
                ("Load Management Techniques",
                 ["Shifting depot charging into off-peak tariff windows",
                  "Dynamic load balancing across charging bays to respect connection caps",
                  "Reservation-based charging schedules for managed fleets"]),
                ("Findings",
                 "Sites that combined off-peak scheduling with active load balancing kept "
                 "aggregate demand below the grid limit while meeting fleet availability "
                 "targets. An energy-management layer coordinating charging across depots was "
                 "the decisive factor. " + _vocab_line(am, 0, 2, 5, 6)),
            ]),
    ))

    ns = _p("Northstar-Analytics")
    files.append(TestFile(
        filename="Single_Source_Of_Truth_Reporting.docx", fmt="docx",
        category="semantic", scope="download", expected_project=ns.key,
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="No project name, but content is governed BI: semantic model, certified metrics, row-level security.",
        semantic_required=True,
        semantic_evidence="Semantic model, certified metrics, data catalogue, self-service analytics, month-end reporting.",
        blocks=_report(
            "Establishing a Single Source of Truth for Retail Reporting",
            "Practitioner Guide  |  Ref: SSOT-BI  |  2026-04-30",
            [
                ("Problem",
                 "When sales and inventory numbers live in disconnected spreadsheets, "
                 "departments argue over whose figure is correct and month-end reporting "
                 "drags on for days. A governed data platform resolves this."),
                ("Approach",
                 ["Consolidate feeds into a warehouse using an ELT pattern",
                  "Certify metrics through one semantic model",
                  "Enforce row-level security so each unit sees only its data",
                  "Offer governed self-service analytics to trusted analysts"]),
                ("Outcome",
                 "Certified dashboards replaced manual reports and the month-end cycle shrank "
                 "materially. " + _vocab_line(ns, 1, 2, 3, 5)),
            ]),
    ))

    hl = _p("Horizon-Logistics")
    files.append(TestFile(
        filename="Warehouse_Picking_Efficiency_Study.pdf", fmt="pdf",
        category="semantic", scope="download", expected_project=hl.key,
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="No project name, but content is warehouse slotting, picking travel, and dispatch.",
        semantic_required=True,
        semantic_evidence="Slotting, picking travel distance, replenishment, dock scheduling, on-time dispatch.",
        blocks=_report(
            "Improving Picking Efficiency in Multi-Site Distribution",
            "Operations Research Brief  |  Ref: WPE-2026  |  2026-05-04",
            [
                ("Overview",
                 "Picking travel dominates labour cost in manual warehouses. Velocity-based "
                 "slotting places fast-moving SKUs closer to dispatch, cutting travel distance "
                 "and easing dock congestion during outbound waves."),
                ("Levers",
                 ["Velocity- and volume-based slot assignment",
                  "Demand forecasting to size safety stock and replenishment",
                  "Dock and yard scheduling to smooth outbound flow"]),
                ("Results",
                 "Combining slotting with better forecasting improved on-time dispatch and "
                 "reduced stock-outs. " + _vocab_line(hl, 1, 2, 3, 6)),
            ]),
    ))

    at = _p("Atlas-Workplace")
    files.append(TestFile(
        filename="Hybrid_Office_Space_Utilisation.pptx", fmt="pptx",
        category="semantic", scope="download", expected_project=at.key,
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="No project name, but content is desk/room booking and occupancy analytics for hybrid work.",
        semantic_required=True,
        semantic_evidence="Desk booking, meeting room availability, occupancy analytics, hybrid working, wayfinding.",
        slides=(
            "Making Hybrid Offices Work", "Space utilisation and booking",
            [
                SlideSpec(title="The Problem",
                          subtitle="Rooms overbooked, desks empty, inconsistent technology."),
                SlideSpec(title="Booking",
                          bullets=["Desk and meeting-room booking from one app",
                                   "Real-time room availability on door panels",
                                   "Check-in to release no-shows"]),
                SlideSpec(title="Insight",
                          bullets=["Occupancy analytics by floor and building",
                                   "Right-size space from measured utilisation",
                                   "Wayfinding to booked spaces"]),
            ]),
    ))

    ps = _p("Polaris-Sustainability")
    files.append(TestFile(
        filename="Corporate_Carbon_Footprint_Methodology.pdf", fmt="pdf",
        category="semantic", scope="download", expected_project=ps.key,
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="No project name, but content is carbon accounting across scopes with emission factors.",
        semantic_required=True,
        semantic_evidence="Scope 1/2/3 emissions, emission factors, supplier emissions, audit trail, disclosure.",
        blocks=_report(
            "A Practical Methodology for Corporate Carbon Footprinting",
            "Sustainability Methods Paper  |  Ref: CCF-M  |  2026-05-07",
            [
                ("Framing",
                 "Credible carbon reporting requires consistent activity data, versioned "
                 "emission factors, and an audit trail for every figure. Scope 3 supplier "
                 "emissions are usually the largest and hardest part."),
                ("Method",
                 ["Collect Scope 1 and 2 activity data by site",
                  "Apply versioned emission factors with traceable methodology",
                  "Engage suppliers for Scope 3 purchased-goods data",
                  "Retain an audit trail to support external assurance"]),
                ("Reporting",
                 "Standard-aligned templates turn the accounting into an auditable annual "
                 "disclosure. " + _vocab_line(ps, 0, 2, 3, 8)),
            ]),
    ))

    mt = _p("Meridian-Travel")
    files.append(TestFile(
        filename="Managing_Business_Trip_Spend_And_Safety.docx", fmt="docx",
        category="semantic", scope="download", expected_project=mt.key,
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="No project name, but content is managed corporate travel: booking tool, policy, duty of care.",
        semantic_required=True,
        semantic_evidence="Online booking tool, pre-trip approval, negotiated rates, duty of care, traveller tracking.",
        blocks=_report(
            "Controlling Business Trip Spend While Keeping Travellers Safe",
            "Programme Practitioner Note  |  Ref: BTS-2026  |  2026-05-09",
            [
                ("The Challenge",
                 "When employees book trips through many channels, spend leaks and no one "
                 "knows where travellers are. A managed programme fixes both at once."),
                ("Programme Elements",
                 ["An online booking tool that applies negotiated rates automatically",
                  "Pre-trip approval enforcing travel policy",
                  "Duty-of-care tracking with alerts to affected travellers"]),
                ("Benefit",
                 "Channelling bookings through the managed tool cut average trip cost and gave "
                 "real-time traveller visibility. " + _vocab_line(mt, 1, 3, 4, 6)),
            ]),
    ))

    rf = _p("Redwood-Facilities")
    files.append(TestFile(
        filename="From_Reactive_To_Preventive_Building_Upkeep.pdf", fmt="pdf",
        category="semantic", scope="download", expected_project=rf.key,
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="No project name, but content is CMMS, asset register, and preventive maintenance.",
        semantic_required=True,
        semantic_evidence="CMMS, asset register, preventive maintenance, work orders, equipment downtime.",
        blocks=_report(
            "Shifting Building Upkeep from Reactive to Preventive",
            "Facilities Practice Brief  |  Ref: RPB-2026  |  2026-05-11",
            [
                ("Why It Matters",
                 "Reactive repairs are costly and disruptive. Moving to preventive maintenance "
                 "requires an accurate asset register and scheduled tasks per asset."),
                ("Building Blocks",
                 ["A complete asset register with location and criticality",
                  "Preventive schedules generated by asset and interval",
                  "Work-order management from request to completion",
                  "Contractor coordination with compliance documents"]),
                ("Payoff",
                 "Critical-equipment downtime fell once preventive maintenance covered the "
                 "most critical systems. " + _vocab_line(rf, 1, 2, 3, 7)),
            ]),
    ))

    ce = _p("Cedar-Events")
    files.append(TestFile(
        filename="Running_A_Large_Industry_Conference.docx", fmt="docx",
        category="semantic", scope="download", expected_project=ce.key,
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="No project name, but content is conference registration, sponsorship, and on-site logistics.",
        semantic_required=True,
        semantic_evidence="Registration, ticketing, sponsorship, attendee app, venue and on-site logistics.",
        blocks=_report(
            "How to Run a 1,000-Plus Attendee Industry Conference",
            "Events Practitioner Guide  |  Ref: LIC-2026  |  2026-05-13",
            [
                ("Setup",
                 "A large conference lives or dies on smooth registration, strong sponsorship, "
                 "and calm on-site logistics. One integrated platform removes duplicated tools."),
                ("Workstreams",
                 ["Registration and ticketing with an attendee app",
                  "Tiered sponsorship packages and deliverables",
                  "Agenda and speaker management",
                  "On-site check-in, badging, and venue coordination"]),
                ("Experience",
                 "Pre-printed badges and multiple check-in lanes prevented bottlenecks and "
                 "lifted attendee satisfaction. " + _vocab_line(ce, 2, 3, 4, 6)),
            ]),
    ))

    # Two more semantic to exceed 10.
    files.append(TestFile(
        filename="Depot_Charging_Off_Peak_Scheduling.xlsx", fmt="xlsx",
        category="semantic", scope="download", expected_project=am.key,
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="No project name, but the schedule is clearly EV depot charging against tariff windows.",
        semantic_required=True,
        semantic_evidence="Depot charging bays, off-peak tariff windows, load cap, charging schedule.",
        sheets=[
            SheetSpec(
                title="Charging Schedule",
                intro=["Depot Charging — Off-Peak Scheduling Model",
                       "Fleet charging against time-of-use tariffs and load cap"],
                header=["Bay", "Start", "End", "Tariff Window", "kW"],
                rows=[
                    ["Bay 1", "22:00", "05:00", "Off-peak", "60"],
                    ["Bay 2", "23:00", "05:00", "Off-peak", "60"],
                    ["Bay 3", "01:00", "05:00", "Off-peak", "50"],
                    ["Site cap", "-", "-", "Grid connection limit", "1200"],
                ]),
        ],
    ))

    files.append(TestFile(
        filename="Retail_Inventory_Analytics_Model.xlsx", fmt="xlsx",
        category="semantic", scope="download", expected_project=ns.key,
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="No project name, but the model is governed retail BI metrics from a semantic layer.",
        semantic_required=True,
        semantic_evidence="Certified metrics, inventory and sales measures, row-level security by business unit.",
        sheets=[
            SheetSpec(
                title="Certified Metrics",
                intro=["Retail Inventory & Sales — Certified Metric Definitions",
                       "Metrics certified through the semantic model only"],
                header=["Metric", "Definition", "Owner"],
                rows=[
                    ["Net sales", "Gross sales less returns", "Sales BU"],
                    ["Stock cover days", "On-hand / average daily demand", "Supply BU"],
                    ["Sell-through", "Units sold / units received", "Merch BU"],
                    ["Stock-out rate", "SKUs at zero on-hand / total SKUs", "Supply BU"],
                ]),
        ],
    ))

    return files


# --- Category 3: Ambiguous matches (>=8) -----------------------------------
def _ambiguous_downloads() -> list[TestFile]:
    files: list[TestFile] = []

    files.append(TestFile(
        filename="Enterprise_Data_Governance_Framework.pdf", fmt="pdf",
        category="ambiguous", scope="download", expected_project=None,
        expected_action=ASK_USER, confidence="Low",
        reason="Data governance fits Northstar's platform governance and Polaris's ESG data controls.",
        candidates=["Northstar-Analytics", "Polaris-Sustainability"],
        semantic_required=True,
        blocks=_report(
            "Enterprise Data Governance Framework",
            "Cross-Programme Reference  |  Ref: EDG-FW  |  2026-05-15",
            [
                ("Purpose",
                 "This framework sets out data ownership, quality, lineage, and audit-trail "
                 "expectations for enterprise data assets. It applies wherever governed data "
                 "supports certified reporting or external assurance."),
                ("Principles",
                 ["Clear data ownership and stewardship",
                  "Documented lineage from source to report",
                  "Data-quality monitoring with owner accountability",
                  "Audit trail for figures used in disclosure or certified metrics"]),
                ("Applicability",
                 "The controls are equally relevant to a governed analytics platform and to a "
                 "carbon-accounting disclosure process; the sponsoring programme should confirm "
                 "ownership before adoption."),
            ]),
    ))

    files.append(TestFile(
        filename="Energy_Consumption_Analytics_Report.pdf", fmt="pdf",
        category="ambiguous", scope="download", expected_project=None,
        expected_action=ASK_USER, confidence="Low",
        reason="Energy analytics spans Aurora (charging load), Northstar (analytics), and Polaris (emissions).",
        candidates=["Aurora-Mobility", "Northstar-Analytics", "Polaris-Sustainability"],
        semantic_required=True,
        blocks=_report(
            "Energy Consumption Analytics Report",
            "Cross-Domain Analysis  |  Ref: ECA-2026  |  2026-05-16",
            [
                ("Scope",
                 "This report analyses energy consumption patterns and their cost and emissions "
                 "implications. It draws on load data, analytical dashboards, and emission "
                 "factors, touching several programmes at once."),
                ("Themes",
                 ["Electricity load profiles and demand peaks",
                  "Analytical dashboards for consumption trends",
                  "Emission factors converting energy use to carbon"]),
                ("Note",
                 "Because the report blends charging load, analytics tooling, and carbon "
                 "accounting, its ownership is genuinely ambiguous and should be confirmed."),
            ]),
    ))

    files.append(TestFile(
        filename="Supplier_Performance_Scorecard.xlsx", fmt="xlsx",
        category="ambiguous", scope="download", expected_project=None,
        expected_action=ASK_USER, confidence="Low",
        reason="Supplier scorecards fit Horizon (carriers/vendors), Polaris (supplier emissions), and Meridian (travel suppliers).",
        candidates=["Horizon-Logistics", "Polaris-Sustainability", "Meridian-Travel"],
        semantic_required=True,
        sheets=[
            SheetSpec(
                title="Scorecard",
                intro=["Supplier Performance Scorecard (Template)",
                       "Applicable to multiple programmes — confirm owner"],
                header=["Supplier", "On-time", "Quality", "Sustainability", "Cost"],
                rows=[
                    ["Supplier A", "96%", "Good", "Data provided", "On plan"],
                    ["Supplier B", "89%", "Fair", "Partial data", "Over plan"],
                    ["Supplier C", "93%", "Good", "No data", "On plan"],
                ]),
        ],
    ))

    files.append(TestFile(
        filename="Change_Management_And_Adoption_Playbook.docx", fmt="docx",
        category="ambiguous", scope="download", expected_project=None,
        expected_action=ASK_USER, confidence="Low",
        reason="Adoption playbooks fit Atlas, Northstar, Meridian, and Redwood equally.",
        candidates=["Atlas-Workplace", "Northstar-Analytics", "Meridian-Travel", "Redwood-Facilities"],
        semantic_required=True,
        blocks=_report(
            "Change Management and Adoption Playbook",
            "Reusable Programme Asset  |  Ref: CMA-PB  |  2026-05-17",
            [
                ("Purpose",
                 "A generic playbook for driving adoption of a new system: stakeholder mapping, "
                 "communications, training, and reinforcement. It is deliberately programme-neutral."),
                ("Plays",
                 ["Map stakeholders and adoption barriers",
                  "Run a phased communications campaign",
                  "Deliver role-based training and support",
                  "Reinforce with metrics and leadership example"]),
                ("Note",
                 "The playbook could support any of several rollouts; the owning programme "
                 "should be confirmed rather than assumed from filename."),
            ]),
    ))

    files.append(TestFile(
        filename="Data_Privacy_Impact_Assessment.pdf", fmt="pdf",
        category="ambiguous", scope="download", expected_project=None,
        expected_action=ASK_USER, confidence="Low",
        reason="Privacy assessments fit Atlas (occupancy sensors) and Meridian (traveller tracking).",
        candidates=["Atlas-Workplace", "Meridian-Travel"],
        semantic_required=True,
        blocks=_report(
            "Data Privacy Impact Assessment",
            "Compliance Template  |  Ref: DPIA-2026  |  2026-05-18",
            [
                ("Purpose",
                 "This assessment evaluates privacy risk where personal or location data is "
                 "collected. It considers purpose limitation, consent, aggregation, and "
                 "works-council review."),
                ("Considerations",
                 ["Data minimisation and aggregation",
                  "Purpose limitation and retention",
                  "Consent and transparency to individuals",
                  "Works-council and regulatory review"]),
                ("Note",
                 "The assessment applies wherever occupancy or traveller-location data is "
                 "processed; the sponsoring programme must be identified."),
            ]),
    ))

    files.append(TestFile(
        filename="Vendor_Contract_Negotiation_Guide.docx", fmt="docx",
        category="ambiguous", scope="download", expected_project=None,
        expected_action=ASK_USER, confidence="Low",
        reason="Vendor negotiation guidance is common to every programme's procurement.",
        candidates=["Aurora-Mobility", "Horizon-Logistics", "Cedar-Events"],
        semantic_required=True,
        blocks=_report(
            "Vendor Contract Negotiation Guide",
            "Procurement Reference  |  Ref: VCN-G  |  2026-05-19",
            [
                ("Purpose",
                 "General guidance for negotiating vendor contracts: scope, service levels, "
                 "pricing, and exit terms. It is not specific to any single programme."),
                ("Checklist",
                 ["Confirm scope against the component or service baseline",
                  "Tie payments to milestones and acceptance",
                  "Set service levels and remedies",
                  "Preserve exit and data-portability rights"]),
                ("Note",
                 "Applicable across programmes; the owning programme should claim it."),
            ]),
    ))

    files.append(TestFile(
        filename="Sustainability_Reporting_Dashboard_Requirements.pdf", fmt="pdf",
        category="ambiguous", scope="download", expected_project=None,
        expected_action=ASK_USER, confidence="Low",
        reason="A sustainability dashboard sits between Polaris (subject) and Northstar (dashboard platform).",
        candidates=["Polaris-Sustainability", "Northstar-Analytics"],
        semantic_required=True,
        blocks=_report(
            "Requirements for a Sustainability Reporting Dashboard",
            "Cross-Programme Requirement  |  Ref: SRD-REQ  |  2026-05-20",
            [
                ("Purpose",
                 "This note specifies a dashboard presenting emissions and sustainability "
                 "metrics. It requires both carbon-accounting subject expertise and a governed "
                 "dashboard platform to deliver."),
                ("Requirements",
                 ["Present Scope 1, 2, and 3 emissions trends",
                  "Certified metrics with row-level security",
                  "Drill-down by site and supplier",
                  "Audit trail for reported figures"]),
                ("Note",
                 "Ownership genuinely splits between the sustainability and analytics "
                 "programmes; confirm before filing."),
            ]),
    ))

    files.append(TestFile(
        filename="Facilities_Energy_Efficiency_Review.pdf", fmt="pdf",
        category="ambiguous", scope="download", expected_project=None,
        expected_action=ASK_USER, confidence="Low",
        reason="Building energy efficiency spans Redwood (facilities) and Polaris (emissions).",
        candidates=["Redwood-Facilities", "Polaris-Sustainability"],
        semantic_required=True,
        blocks=_report(
            "Facilities Energy Efficiency Review",
            "Estate Review  |  Ref: FEE-2026  |  2026-05-21",
            [
                ("Purpose",
                 "This review examines building energy use, plant efficiency, and the emissions "
                 "these generate, linking maintenance decisions to carbon outcomes."),
                ("Findings",
                 ["Ageing plant drives avoidable energy use",
                  "Preventive maintenance improves efficiency",
                  "Energy use converts to Scope 1 and 2 emissions"]),
                ("Note",
                 "Sits between facilities maintenance and sustainability reporting; confirm the "
                 "owning programme."),
            ]),
    ))

    return files


# --- Category 4: Wrong-project matches (>=8) -------------------------------
def _wrong_downloads() -> list[TestFile]:
    files: list[TestFile] = []

    files.append(TestFile(
        filename="Aurora_Analytics_Dashboard.pdf", fmt="pdf",
        category="wrong", scope="download", expected_project="Northstar-Analytics",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason='Filename says "Aurora" but content is governed BI dashboards — Northstar Analytics.',
        misleading_filename=True, semantic_required=True,
        semantic_evidence="Semantic model, certified dashboards, row-level security, month-end reporting cycle.",
        blocks=_report(
            "Analytics Dashboard Design",
            "Ref: ADD-2026  |  2026-05-22",
            [
                ("Overview",
                 "This document specifies certified analytics dashboards built on a governed "
                 "semantic model, replacing manual spreadsheet reports for a retail group. "
                 "Despite the codename in the filename, the subject is business intelligence, "
                 "not charging infrastructure."),
                ("Dashboards",
                 ["Sales and inventory performance by store",
                  "Customer segmentation from certified metrics",
                  "Row-level security by business unit"]),
                ("Governance",
                 "Metrics are certified only through the semantic model, and the month-end "
                 "reporting cycle is cut from days to hours."),
            ]),
    ))

    files.append(TestFile(
        filename="Northstar_Charging_Network_Plan.pdf", fmt="pdf",
        category="wrong", scope="download", expected_project="Aurora-Mobility",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason='Filename says "Northstar" but content is an EV charging network — Aurora Mobility.',
        misleading_filename=True, semantic_required=True,
        semantic_evidence="Charging stations, OCPP, depot charging, off-peak tariff, grid connection.",
        blocks=_report(
            "Charging Network Deployment Plan",
            "Ref: CNP-2026  |  2026-05-23",
            [
                ("Overview",
                 "This plan sequences the deployment of public and depot charging stations, "
                 "with OCPP controllers and off-peak scheduling to respect grid connection "
                 "limits. The filename's codename is misleading; the content is charging "
                 "infrastructure."),
                ("Phases",
                 ["Zone 1 depot charging and energy-management core",
                  "Zone 2 public charging expansion",
                  "Zone 3 completion and demand analytics"]),
                ("Constraints",
                 "Aggregate depot load is capped below the grid connection limit through "
                 "dynamic load balancing."),
            ]),
    ))

    files.append(TestFile(
        filename="Polaris_Warehouse_Slotting_Notes.docx", fmt="docx",
        category="wrong", scope="download", expected_project="Horizon-Logistics",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason='Filename says "Polaris" but content is warehouse slotting — Horizon Logistics.',
        misleading_filename=True, semantic_required=True,
        semantic_evidence="Slotting, picking travel, replenishment, dock scheduling, throughput.",
        blocks=_report(
            "Warehouse Slotting Notes",
            "Ref: WSN-2026  |  2026-05-24",
            [
                ("Notes",
                 "Working notes on velocity-based slotting to reduce picking travel and dock "
                 "congestion across three warehouses. The sustainability codename in the "
                 "filename does not match the operational content."),
                ("Actions",
                 ["Re-slot fast movers near dispatch",
                  "Backtest demand forecasts for replenishment",
                  "Trial dock scheduling to cut yard congestion"]),
            ]),
    ))

    files.append(TestFile(
        filename="Meridian_Room_Booking_Overview.pdf", fmt="pdf",
        category="wrong", scope="download", expected_project="Atlas-Workplace",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason='Filename says "Meridian" but content is desk/room booking — Atlas Workplace.',
        misleading_filename=True, semantic_required=True,
        semantic_evidence="Desk booking, meeting-room panels, occupancy analytics, hybrid working.",
        blocks=_report(
            "Room and Desk Booking Overview",
            "Ref: RDB-2026  |  2026-05-25",
            [
                ("Overview",
                 "This overview covers desk and meeting-room booking with door panels and "
                 "occupancy analytics for hybrid working across three buildings. The travel "
                 "codename in the filename is misleading."),
                ("Features",
                 ["Book desks and rooms from one app",
                  "Real-time availability on door panels",
                  "Occupancy analytics by floor and building"]),
            ]),
    ))

    files.append(TestFile(
        filename="Horizon_Carbon_Disclosure_Draft.pdf", fmt="pdf",
        category="wrong", scope="download", expected_project="Polaris-Sustainability",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason='Filename says "Horizon" but content is carbon disclosure — Polaris Sustainability.',
        misleading_filename=True, semantic_required=True,
        semantic_evidence="Scope 3 emissions, emission factors, supplier data, audit trail, disclosure.",
        blocks=_report(
            "Annual Carbon Disclosure (Draft)",
            "Ref: ACD-2026  |  2026-05-26",
            [
                ("Draft",
                 "This draft disclosure consolidates Scope 1, 2, and 3 emissions with versioned "
                 "emission factors and an audit trail per figure. The logistics codename in the "
                 "filename does not reflect the sustainability content."),
                ("Sections",
                 ["Scope 1 and 2 by site",
                  "Scope 3 purchased-goods supplier emissions",
                  "Methodology and estimation notes"]),
            ]),
    ))

    files.append(TestFile(
        filename="Atlas_Traveller_Duty_Of_Care.docx", fmt="docx",
        category="wrong", scope="download", expected_project="Meridian-Travel",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason='Filename says "Atlas" but content is traveller duty of care — Meridian Travel.',
        misleading_filename=True, semantic_required=True,
        semantic_evidence="Traveller tracking, duty of care, pre-trip approval, negotiated rates.",
        blocks=_report(
            "Traveller Duty of Care Procedures",
            "Ref: TDC-2026  |  2026-05-27",
            [
                ("Procedures",
                 "Procedures for tracking travellers and issuing safety alerts under a managed "
                 "corporate-travel programme, alongside pre-trip approval and negotiated rates. "
                 "The workplace codename in the filename is misleading."),
                ("Playbook",
                 ["Pre-trip risk briefing for high-risk destinations",
                  "Disruption alerts to affected travellers",
                  "SOS escalation to the traveller care team"]),
            ]),
    ))

    files.append(TestFile(
        filename="Cedar_Preventive_Maintenance_Overview.pdf", fmt="pdf",
        category="wrong", scope="download", expected_project="Redwood-Facilities",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason='Filename says "Cedar" but content is preventive maintenance — Redwood Facilities.',
        misleading_filename=True, semantic_required=True,
        semantic_evidence="CMMS, asset register, preventive maintenance, work orders, downtime.",
        blocks=_report(
            "Preventive Maintenance Overview",
            "Ref: PMO-2026  |  2026-05-28",
            [
                ("Overview",
                 "An overview of moving from reactive repairs to preventive maintenance using a "
                 "CMMS, an asset register, and scheduled tasks per asset. The events codename in "
                 "the filename does not match the facilities content."),
                ("Elements",
                 ["Asset register with criticality",
                  "Preventive schedules per asset and interval",
                  "Mobile work orders and contractor compliance"]),
            ]),
    ))

    files.append(TestFile(
        filename="Redwood_Conference_Sponsorship_Deck.pptx", fmt="pptx",
        category="wrong", scope="download", expected_project="Cedar-Events",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason='Filename says "Redwood" but slides are conference sponsorship — Cedar Events.',
        misleading_filename=True, semantic_required=True,
        semantic_evidence="Sponsorship tiers, registration, attendee app, venue and on-site logistics.",
        slides=(
            "Conference Sponsorship", "Packages and deliverables",
            [
                SlideSpec(title="Why Sponsor",
                          subtitle="Reach 1,200 attendees at the flagship conference (facilities codename in filename is misleading)."),
                SlideSpec(title="Packages",
                          bullets=["Platinum: keynote and booth",
                                   "Gold: session and booth",
                                   "Silver: booth and app listing"]),
                SlideSpec(title="Deliverables",
                          bullets=["Logo on registration and app",
                                   "On-site branding and staffing slots"]),
            ]),
    ))

    return files


# --- Category 5: Completely unrelated (>=6) --------------------------------
def _unrelated_downloads() -> list[TestFile]:
    files: list[TestFile] = []

    files.append(TestFile(
        filename="Family_Travel_Insurance_Policy.pdf", fmt="pdf",
        category="unrelated", scope="download", expected_project=None,
        expected_action=NO_REC, confidence="None",
        reason="Personal insurance document; unrelated to any programme (note: not corporate travel).",
        blocks=_report(
            "Family Travel Insurance — Policy Summary",
            "Personal Document  |  Policy No. SYN-000-DEMO  |  2026-04-01",
            [
                ("Cover",
                 "This personal travel insurance policy covers medical expenses, trip "
                 "cancellation, and lost baggage for a family holiday. It is a personal "
                 "document with no connection to any work programme."),
                ("Sections",
                 ["Medical and repatriation cover",
                  "Cancellation and curtailment",
                  "Baggage and personal effects"]),
            ]),
    ))

    files.append(TestFile(
        filename="Weeknight_Recipe_Collection.docx", fmt="docx",
        category="unrelated", scope="download", expected_project=None,
        expected_action=NO_REC, confidence="None",
        reason="Personal recipe collection; no programme relevance.",
        blocks=_report(
            "Weeknight Recipe Collection",
            "Personal Notes",
            [
                ("Favourites",
                 "A collection of quick weeknight recipes gathered over time, from one-pan "
                 "pasta to sheet-pan vegetables. Purely personal."),
                ("Recipes",
                 ["One-pan tomato pasta",
                  "Sheet-pan roasted vegetables",
                  "Weeknight chicken curry",
                  "Simple lentil soup"]),
            ]),
    ))

    files.append(TestFile(
        filename="Beginner_Photography_Guide.pdf", fmt="pdf",
        category="unrelated", scope="download", expected_project=None,
        expected_action=NO_REC, confidence="None",
        reason="Hobby photography guide; unrelated to any programme.",
        blocks=_report(
            "A Beginner's Guide to Photography",
            "Personal Hobby Notes",
            [
                ("Basics",
                 "An introduction to exposure, aperture, shutter speed, and composition for "
                 "someone starting out with a camera. A personal hobby guide."),
                ("Topics",
                 ["Understanding the exposure triangle",
                  "Rule of thirds and composition",
                  "Working with natural light"]),
            ]),
    ))

    files.append(TestFile(
        filename="Kitchen_Renovation_Estimate.xlsx", fmt="xlsx",
        category="unrelated", scope="download", expected_project=None,
        expected_action=NO_REC, confidence="None",
        reason="Personal home renovation budget; not a work programme.",
        sheets=[
            SheetSpec(
                title="Estimate",
                intro=["Kitchen Renovation — Personal Estimate", "Household budget"],
                header=["Item", "Estimate"],
                rows=[
                    ["Cabinets", "EUR 6,500"],
                    ["Worktops", "EUR 2,800"],
                    ["Appliances", "EUR 3,200"],
                    ["Labour", "EUR 4,500"],
                ]),
        ],
    ))

    files.append(TestFile(
        filename="Personal_Tax_Return_Notes.pdf", fmt="pdf",
        category="unrelated", scope="download", expected_project=None,
        expected_action=NO_REC, confidence="None",
        reason="Personal tax document; unrelated to any programme.",
        blocks=_report(
            "Personal Tax Return — Preparation Notes",
            "Personal Document  |  Tax Year 2025",
            [
                ("Checklist",
                 "Notes for preparing a personal annual tax return, including income sources, "
                 "deductions, and filing dates. Entirely personal."),
                ("Items",
                 ["Employment income summary",
                  "Allowable personal deductions",
                  "Filing deadline reminders"]),
            ]),
    ))

    files.append(TestFile(
        filename="Movie_Night_Planning.xlsx", fmt="xlsx",
        category="unrelated", scope="download", expected_project=None,
        expected_action=NO_REC, confidence="None",
        reason="Personal movie-night planning spreadsheet; no programme relevance.",
        sheets=[
            SheetSpec(
                title="Movie Nights",
                intro=["Movie Night Planning", "Personal / social"],
                header=["Date", "Film", "Host"],
                rows=[
                    ["2026-04-10", "Classic sci-fi", "Alex"],
                    ["2026-04-17", "Comedy night", "Sam"],
                    ["2026-04-24", "Documentary pick", "Jo"],
                ]),
        ],
    ))

    return files


# --- Category 6: Duplicate / updated versions (>=8) ------------------------
def _duplicate_downloads() -> list[TestFile]:
    files: list[TestFile] = []

    am = _p("Aurora-Mobility")
    files.append(TestFile(
        filename="Aurora_Technical_Architecture_v2.pdf", fmt="pdf",
        category="duplicate", scope="download", expected_project=am.key,
        expected_action=UPDATED_VERSION, confidence="High",
        reason="Revised architecture: adds a component and a requirement; content substantially overlaps v1.",
        existing_file="Aurora-Mobility/Technical_Architecture.pdf", relationship=REL_UPDATED,
        blocks=_report(
            "Aurora Mobility — Technical Architecture",
            "Document ID: AM-DOC-003  |  Version: 2.0 (supersedes 1.3)  |  Date: 2026-06-02",
            [
                ("Change Log (v2.0)",
                 ["Added Vehicle-to-Grid (V2G) Interface component",
                  "New requirement REQ-AM-031: support bidirectional V2G discharge in Zone 1",
                  "Revised depot load cap wording to reference dynamic headroom"]),
                ("Overview",
                 am.summary + " Version 2.0 keeps the same component structure and design "
                 "decisions as version 1.3 but introduces a V2G interface and clarifies the "
                 "depot load-cap behaviour."),
                ("Components",
                 ("table", (["Component", "Description"],
                            [[n, d] for n, d in am.components] +
                            [["Vehicle-to-Grid Interface", "Bidirectional discharge control for Zone 1 depot fleets (new in v2.0)."]]))),
                ("Key Design Decisions",
                 ("table", (["ID", "Decision", "Rationale"],
                            [[i, dec, r] for i, dec, r in am.decisions]))),
            ]),
    ))

    ns = _p("Northstar-Analytics")
    files.append(TestFile(
        filename="Northstar_Requirements_Update.docx", fmt="docx",
        category="duplicate", scope="download", expected_project=ns.key,
        expected_action=UPDATED_VERSION, confidence="High",
        reason="Revised requirements spec: adds a requirement and updates the date; overlaps existing spec.",
        existing_file="Northstar-Analytics/Requirements_Specification.docx", relationship=REL_UPDATED,
        blocks=_report(
            "Northstar Analytics — Requirements Specification",
            "Document ID: NS-DOC-002  |  Version: 2.0 (supersedes 1.4)  |  Date: 2026-06-04",
            [
                ("Change Log (v2.0)",
                 ["Added REQ-NS-031: support near-real-time sales streaming for flagship stores",
                  "Raised history retention target to three years",
                  "Clarified certified-metric governance ownership"]),
                ("Functional Requirements",
                 ("table", (["ID", "Requirement", "Priority"],
                            [[rid, t, pr] for rid, t, pr in ns.requirements] +
                            [["REQ-NS-031", "The platform shall support near-real-time sales streaming for flagship stores.", "Should"]]))),
                ("Note",
                 "All other requirements are unchanged from version 1.4. This update should be "
                 "recognised as a newer version of the existing Requirements Specification."),
            ]),
    ))

    hl = _p("Horizon-Logistics")
    files.append(TestFile(
        filename="Horizon_Budget_Revised.xlsx", fmt="xlsx",
        category="duplicate", scope="download", expected_project=hl.key,
        expected_action=UPDATED_VERSION, confidence="High",
        reason="Revised budget: one line item changed and contingency recalculated; mirrors existing budget.",
        existing_file="Horizon-Logistics/Budget_and_Cost_Forecast.xlsx", relationship=REL_REVISED,
        sheets=[
            SheetSpec(
                title="Budget",
                intro=["Horizon Logistics — Budget and Cost Forecast (HL-DOC-009)",
                       "Version 2.0 (supersedes 1.2)  |  Change: WMS line increased; contingency recalculated"],
                header=["Cost Category", "Budget"],
                rows=[
                    ["WMS and control system", "EUR 1,080,000"],  # was 980,000
                    ["Forecasting analytics", "EUR 350,000"],
                    ["Dock-scheduling platform", "EUR 240,000"],
                    ["Integration and data cleanse", "EUR 620,000"],
                    ["Training and change", "EUR 210,000"],
                    ["Programme management", "EUR 300,000"],
                    ["Contingency (10%)", "EUR 280,000"],
                ]),
        ],
    ))

    at = _p("Atlas-Workplace")
    files.append(TestFile(
        filename="Atlas_Deployment_Plan_Final.pdf", fmt="pdf",
        category="duplicate", scope="download", expected_project=at.key,
        expected_action=UPDATED_VERSION, confidence="High",
        reason="Final deployment plan: adds a risk-driven parallel run; overlaps existing deployment plan.",
        existing_file="Atlas-Workplace/Deployment_Plan.pdf", relationship=REL_UPDATED,
        blocks=_report(
            "Atlas Workplace — Deployment Plan",
            "Document ID: AT-DOC-005  |  Version: 2.0 (Final, supersedes 1.2)  |  Date: 2026-06-06",
            [
                ("Change Log (v2.0)",
                 ["Added a two-week parallel run before Building 2 cutover",
                  "Updated Building 3 target date by two weeks",
                  "Added rollback checkpoint after room-technology standardisation"]),
                ("Phase Plan",
                 ("table", (["Phase", "Target Date", "Deliverable"],
                            [[ph, dt, dl] for ph, dt, dl in at.milestones]))),
                ("Note",
                 "This final version supersedes the earlier Deployment Plan and should be "
                 "matched to it as an updated version, not filed as a new document."),
            ]),
    ))

    ps = _p("Polaris-Sustainability")
    files.append(TestFile(
        filename="Polaris_Risk_Assessment_Rev.pdf", fmt="pdf",
        category="duplicate", scope="download", expected_project=ps.key,
        expected_action=UPDATED_VERSION, confidence="High",
        reason="Revised risk assessment: adds a new risk row; otherwise overlaps existing register.",
        existing_file="Polaris-Sustainability/Risk_Assessment.pdf", relationship=REL_REVISED,
        blocks=_report(
            "Polaris Sustainability — Risk Assessment",
            "Document ID: PS-DOC-007  |  Version: 2.0 (supersedes 1.1)  |  Date: 2026-06-08",
            [
                ("Change Log (v2.0)",
                 ["Added RSK-PS-06: regulatory reporting standard changes mid-cycle",
                  "Re-scored RSK-PS-01 likelihood down after supplier onboarding progress"]),
                ("Risk Register",
                 ("table", (["ID", "Risk", "Likelihood", "Impact", "Mitigation"],
                            [[rid, d, l, i, m] for rid, d, l, i, m in ps.risks] +
                            [["RSK-PS-06", "Reporting standard changes mid-cycle.", "Medium", "High", "Configurable templates; standards watch."]]))),
            ]),
    ))

    mt = _p("Meridian-Travel")
    files.append(TestFile(
        filename="Meridian_Overview_Copy.pdf", fmt="pdf",
        category="duplicate", scope="download", expected_project=mt.key,
        expected_action=POSSIBLE_DUP, confidence="High",
        reason="Near-identical copy of the Meridian project overview with no substantive changes.",
        existing_file="Meridian-Travel/Project_Overview.pdf", relationship=REL_DUPLICATE,
        blocks=_report(
            "Meridian Travel — Project Overview",
            "Document ID: MT-DOC-001  |  Version: 1.2  |  Date: 2026-03-04  |  Owner: Camille Laurent",
            [
                ("Executive Summary",
                 mt.summary + " This overview summarises the objectives, scope, stakeholders, "
                 "and delivery approach for the programme."),
                ("Objectives", mt.objectives),
                ("Scope",
                 ["In scope: " + mt.scope_in, "Out of scope: " + mt.scope_out]),
                ("Note",
                 "This file is an unchanged copy of the existing Project Overview and should be "
                 "flagged as a likely duplicate."),
            ]),
    ))

    rf = _p("Redwood-Facilities")
    files.append(TestFile(
        filename="Redwood_Asset_Register_v3.xlsx", fmt="xlsx",
        category="duplicate", scope="download", expected_project=rf.key,
        expected_action=UPDATED_VERSION, confidence="High",
        reason="Updated asset register with additional assets; overlaps the existing register content.",
        existing_file="Redwood-Facilities/Preventive_Maintenance_Schedule (asset data)", relationship=REL_UPDATED,
        sheets=[
            SheetSpec(
                title="Asset Register",
                intro=["Redwood Facilities — Asset Register (RF asset data)",
                       "Version 3.0  |  Change: added two critical assets in Quayside Annex"],
                header=["Asset", "Building", "Criticality", "Added"],
                rows=[
                    ["Chiller CH-01", "Harbor House", "Critical", "v1"],
                    ["Passenger lift LF-03", "Harbor House", "Critical", "v1"],
                    ["AHU-12", "Dockside Tower", "High", "v2"],
                    ["Fire pump FP-02", "Dockside Tower", "Critical", "v2"],
                    ["Standby generator GN-02", "Quayside Annex", "Critical", "v3 (new)"],
                    ["Booster pump BP-05", "Quayside Annex", "High", "v3 (new)"],
                ]),
        ],
    ))

    ce = _p("Cedar-Events")
    files.append(TestFile(
        filename="Cedar_Status_Report_Latest.pdf", fmt="pdf",
        category="duplicate", scope="download", expected_project=ce.key,
        expected_action=UPDATED_VERSION, confidence="Medium",
        reason="Later status report for the same programme; supersedes the March status report.",
        existing_file="Cedar-Events/Status_Report.pdf", relationship=REL_UPDATED,
        blocks=_report(
            "Cedar Events — Status Report",
            "Document ID: CE-DOC-008  |  Reporting Period: May 2026 (supersedes March 2026)  |  Owner: Isabel Moreno",
            [
                ("Overall Status",
                 "Status remains GREEN. Registration is open and sponsorship packages are "
                 "selling ahead of plan; venue and AV contracts are confirmed."),
                ("Progress This Period",
                 ["Registration and sponsorship live",
                  "Venue contract and catering confirmed",
                  "Agenda drafting under way"]),
                ("Note",
                 "This is a newer status report for the same programme and should be matched to "
                 "the earlier Status Report as an updated version."),
            ]),
    ))

    return files


# ===========================================================================
# FLOATING FILES (generated directly in the OneDrive root)
# ===========================================================================
def _floating_files() -> list[TestFile]:
    files: list[TestFile] = []

    # 1. Obvious floating (~6)
    am = _p("Aurora-Mobility")
    files.append(TestFile(
        filename="Aurora_Charging_Deployment_Notes.pdf", fmt="pdf",
        category="obvious", scope="floating", expected_project=am.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Names Aurora and its charging deployment explicitly.",
        blocks=_report(
            "Aurora Mobility — Charging Deployment Notes",
            "Working notes  |  2026-04-15",
            [
                ("Notes",
                 "Field notes from the Aurora Mobility Zone 1 charging deployment: controller "
                 "commissioning, depot load caps, and off-peak scheduling checks."),
                ("Checklist",
                 ["Verify OCPP controller connectivity",
                  "Confirm depot load cap enforcement",
                  "Validate off-peak charging windows"]),
            ]),
    ))
    ns = _p("Northstar-Analytics")
    files.append(TestFile(
        filename="Northstar_Dashboard_Feedback.docx", fmt="docx",
        category="obvious", scope="floating", expected_project=ns.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Names Northstar and its certified dashboards.",
        blocks=_report(
            "Northstar Analytics — Dashboard Feedback",
            "Business-user feedback  |  2026-05-01",
            [
                ("Feedback",
                 "Consolidated feedback on the Northstar Analytics certified dashboards from "
                 "business units, covering sales and inventory views and self-service needs."),
                ("Requests",
                 ["Add store-level drill-down to the sales dashboard",
                  "Expose stock-out risk earlier",
                  "Enable analyst self-service datasets"]),
            ]),
    ))
    hl = _p("Horizon-Logistics")
    files.append(TestFile(
        filename="Horizon_Warehouse_B_Notes.docx", fmt="docx",
        category="obvious", scope="floating", expected_project=hl.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Names Horizon and its Warehouse B pilot.",
        blocks=_report(
            "Horizon Logistics — Warehouse B Notes",
            "Pilot notes  |  2026-05-03",
            [
                ("Notes",
                 "Observations from the Horizon Logistics Warehouse B slotting pilot: picking "
                 "travel, dock congestion, and replenishment exceptions."),
                ("Follow-ups",
                 ["Re-slot two aisles of fast movers",
                  "Review replenishment exception list",
                  "Baseline dock congestion for scheduling"]),
            ]),
    ))
    ps = _p("Polaris-Sustainability")
    files.append(TestFile(
        filename="Polaris_Emissions_Data_Notes.pdf", fmt="pdf",
        category="obvious", scope="floating", expected_project=ps.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Names Polaris and its emissions data work.",
        blocks=_report(
            "Polaris Sustainability — Emissions Data Notes",
            "Working notes  |  2026-05-05",
            [
                ("Notes",
                 "Notes on Polaris Sustainability activity-data collection and emission-factor "
                 "versioning for Scope 1 and 2, with Scope 3 supplier gaps flagged."),
                ("Actions",
                 ["Close Scope 1 data gaps at two sites",
                  "Confirm factor library version",
                  "Chase Tier 1 supplier responses"]),
            ]),
    ))
    ce = _p("Cedar-Events")
    files.append(TestFile(
        filename="Cedar_Sponsorship_Tracker.xlsx", fmt="xlsx",
        category="obvious", scope="floating", expected_project=ce.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Names Cedar and tracks its conference sponsorship.",
        sheets=[
            SheetSpec(
                title="Sponsors",
                intro=["Cedar Events — Sponsorship Tracker", "Flagship conference"],
                header=["Sponsor", "Tier", "Status"],
                rows=[
                    ["Northwind Corp", "Platinum", "Confirmed"],
                    ["BluePeak", "Gold", "In discussion"],
                    ["Vertex Labs", "Silver", "Confirmed"],
                ]),
        ],
    ))
    rf = _p("Redwood-Facilities")
    files.append(TestFile(
        filename="Redwood_Work_Order_Backlog.xlsx", fmt="xlsx",
        category="obvious", scope="floating", expected_project=rf.key,
        expected_action=SUGGEST_MOVE, confidence="High",
        reason="Names Redwood and lists its maintenance work orders.",
        sheets=[
            SheetSpec(
                title="Work Orders",
                intro=["Redwood Facilities — Work Order Backlog", "CMMS export"],
                header=["WO", "Asset", "Type", "Status"],
                rows=[
                    ["WO-1042", "Chiller CH-01", "Preventive", "Open"],
                    ["WO-1043", "Lift LF-03", "Reactive", "In progress"],
                    ["WO-1044", "AHU-12", "Preventive", "Scheduled"],
                ]),
        ],
    ))

    # 2. Semantic floating (~6)
    files.append(TestFile(
        filename="Fleet_Energy_Load_Study.pdf", fmt="pdf",
        category="semantic", scope="floating", expected_project="Aurora-Mobility",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="Content is EV fleet charging and energy demand without naming Aurora.",
        semantic_required=True,
        semantic_evidence="Fleet charging, charging schedules, energy demand, off-peak windows.",
        blocks=_report(
            "Fleet Energy Load Study",
            "Analysis  |  2026-05-06",
            [
                ("Study",
                 "This study models fleet charging demand and schedules across depots, sizing "
                 "off-peak windows so aggregate load stays within the connection limit."),
                ("Findings",
                 ["Off-peak scheduling flattens demand peaks",
                  "Load balancing prevents connection-limit breaches",
                  "Reservation-based charging stabilises depot load"]),
            ]),
    ))
    files.append(TestFile(
        filename="Month_End_Reporting_Bottlenecks.docx", fmt="docx",
        category="semantic", scope="floating", expected_project="Northstar-Analytics",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="Content is governed BI and certified metrics without naming Northstar.",
        semantic_required=True,
        semantic_evidence="Semantic model, certified metrics, month-end cycle, self-service analytics.",
        blocks=_report(
            "Fixing Month-End Reporting Bottlenecks",
            "Analysis  |  2026-05-08",
            [
                ("Problem",
                 "Month-end reporting drags because metrics live in scattered spreadsheets with "
                 "no single certified definition."),
                ("Fix",
                 ["Certify metrics through one semantic model",
                  "Automate feeds into the warehouse",
                  "Offer governed self-service analytics"]),
            ]),
    ))
    files.append(TestFile(
        filename="Reducing_Picking_Travel.pdf", fmt="pdf",
        category="semantic", scope="floating", expected_project="Horizon-Logistics",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="Content is warehouse slotting and picking travel without naming Horizon.",
        semantic_required=True,
        semantic_evidence="Slotting, picking travel distance, throughput, dock scheduling.",
        blocks=_report(
            "Reducing Picking Travel in the Warehouse",
            "Analysis  |  2026-05-10",
            [
                ("Approach",
                 "Velocity-based slotting places fast movers near dispatch, cutting picking "
                 "travel and improving outbound throughput."),
                ("Levers",
                 ["Re-slot by SKU velocity and volume",
                  "Schedule docks to smooth outbound waves",
                  "Forecast demand to size replenishment"]),
            ]),
    ))
    files.append(TestFile(
        filename="Meeting_Room_Utilisation_Analysis.pptx", fmt="pptx",
        category="semantic", scope="floating", expected_project="Atlas-Workplace",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="Content is room booking and occupancy analytics without naming Atlas.",
        semantic_required=True,
        semantic_evidence="Meeting-room booking, occupancy analytics, hybrid working, door panels.",
        slides=(
            "Meeting Room Utilisation", "Occupancy analysis",
            [
                SlideSpec(title="Finding",
                          subtitle="Rooms are overbooked while desks sit empty."),
                SlideSpec(title="Actions",
                          bullets=["Enable room booking with check-in",
                                   "Show availability on door panels",
                                   "Use occupancy analytics to right-size space"]),
            ]),
    ))
    files.append(TestFile(
        filename="Supplier_Emissions_Collection.pdf", fmt="pdf",
        category="semantic", scope="floating", expected_project="Polaris-Sustainability",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="Content is Scope 3 supplier emissions without naming Polaris.",
        semantic_required=True,
        semantic_evidence="Scope 3, supplier emissions, emission factors, audit trail.",
        blocks=_report(
            "Collecting Supplier Emissions Data",
            "Analysis  |  2026-05-12",
            [
                ("Method",
                 "Tiered engagement collects Scope 3 supplier emissions, with spend-based "
                 "estimation where primary data is missing, all under an audit trail."),
                ("Steps",
                 ["Prioritise purchased-goods suppliers",
                  "Issue questionnaires to Tier 1 and 2",
                  "Estimate Tier 3 from emission factors"]),
            ]),
    ))
    files.append(TestFile(
        filename="Negotiated_Airfare_Savings.xlsx", fmt="xlsx",
        category="semantic", scope="floating", expected_project="Meridian-Travel",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason="Content is corporate travel negotiated rates and policy without naming Meridian.",
        semantic_required=True,
        semantic_evidence="Negotiated rates, online booking tool, travel policy, trip cost.",
        sheets=[
            SheetSpec(
                title="Savings",
                intro=["Negotiated Airfare Savings Model", "Managed corporate travel"],
                header=["Route", "Market Fare", "Negotiated", "Saving"],
                rows=[
                    ["City A-B", "EUR 420", "EUR 360", "14%"],
                    ["City A-C", "EUR 540", "EUR 470", "13%"],
                    ["City B-D", "EUR 380", "EUR 330", "13%"],
                ]),
        ],
    ))

    # 3. Ambiguous floating (~5)
    files.append(TestFile(
        filename="Environmental_Data_Analysis.pdf", fmt="pdf",
        category="ambiguous", scope="floating", expected_project=None,
        expected_action=ASK_USER, confidence="Low",
        reason="Environmental data analytics fits both Northstar (analytics) and Polaris (sustainability).",
        candidates=["Northstar-Analytics", "Polaris-Sustainability"],
        semantic_required=True,
        blocks=_report(
            "Environmental Data Analysis",
            "Cross-domain  |  2026-05-14",
            [
                ("Scope",
                 "Analyses environmental datasets and presents them in dashboards, combining "
                 "analytics tooling with sustainability subject matter."),
                ("Note",
                 "Could belong to the analytics platform or the sustainability programme; "
                 "confirm ownership."),
            ]),
    ))
    files.append(TestFile(
        filename="Space_And_Travel_Cost_Review.xlsx", fmt="xlsx",
        category="ambiguous", scope="floating", expected_project=None,
        expected_action=ASK_USER, confidence="Low",
        reason="Blends workplace space cost (Atlas) and travel cost (Meridian).",
        candidates=["Atlas-Workplace", "Meridian-Travel"],
        semantic_required=True,
        sheets=[
            SheetSpec(
                title="Cost Review",
                intro=["Space and Travel Cost Review", "Confirm owning programme"],
                header=["Category", "Driver", "Trend"],
                rows=[
                    ["Office space", "Desk utilisation", "Down"],
                    ["Business travel", "Trip volume", "Flat"],
                    ["Meeting rooms", "Booking demand", "Up"],
                ]),
        ],
    ))
    files.append(TestFile(
        filename="Contractor_And_Vendor_Compliance.docx", fmt="docx",
        category="ambiguous", scope="floating", expected_project=None,
        expected_action=ASK_USER, confidence="Low",
        reason="Compliance for contractors/vendors fits Redwood (contractors) and any procurement-heavy programme.",
        candidates=["Redwood-Facilities", "Horizon-Logistics"],
        semantic_required=True,
        blocks=_report(
            "Contractor and Vendor Compliance",
            "Reusable asset  |  2026-05-15",
            [
                ("Purpose",
                 "Defines compliance documents and checks for contractors and vendors, "
                 "applicable to facilities contractors and logistics vendors alike."),
                ("Note", "Confirm the owning programme before filing."),
            ]),
    ))
    files.append(TestFile(
        filename="Analytics_Platform_Data_Quality.pdf", fmt="pdf",
        category="ambiguous", scope="floating", expected_project=None,
        expected_action=ASK_USER, confidence="Low",
        reason="Data-quality governance fits Northstar (analytics) and Polaris (ESG data).",
        candidates=["Northstar-Analytics", "Polaris-Sustainability"],
        semantic_required=True,
        blocks=_report(
            "Data Quality for Reporting Platforms",
            "Reference  |  2026-05-16",
            [
                ("Purpose",
                 "Sets data-quality rules and ownership for platforms that feed certified "
                 "reporting or assured disclosure."),
                ("Note", "Ownership genuinely spans analytics and sustainability."),
            ]),
    ))
    files.append(TestFile(
        filename="Event_Or_Workplace_AV_Standard.docx", fmt="docx",
        category="ambiguous", scope="floating", expected_project=None,
        expected_action=ASK_USER, confidence="Low",
        reason="AV standards fit Cedar (event staging) and Atlas (meeting-room AV).",
        candidates=["Cedar-Events", "Atlas-Workplace"],
        semantic_required=True,
        blocks=_report(
            "Audio-Visual Standard",
            "Reference  |  2026-05-17",
            [
                ("Purpose",
                 "Defines an audio-visual standard for staged events and for meeting rooms, "
                 "covering displays, audio, and control."),
                ("Note", "Confirm whether this is for the event or the workplace programme."),
            ]),
    ))

    # 4. Wrong-project floating (~4)
    files.append(TestFile(
        filename="Aurora_Data_Report.pdf", fmt="pdf",
        category="wrong", scope="floating", expected_project="Northstar-Analytics",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason='Filename says "Aurora" but content is BI analytics — Northstar.',
        misleading_filename=True, semantic_required=True,
        semantic_evidence="Semantic model, certified metrics, dashboards, row-level security.",
        blocks=_report(
            "Data Report",
            "2026-05-18",
            [
                ("Content",
                 "This report covers certified analytics metrics and dashboards on a governed "
                 "semantic model for a retail group. The charging codename in the filename is "
                 "misleading; the subject is business intelligence."),
                ("Sections",
                 ["Sales and inventory metrics",
                  "Row-level security by business unit",
                  "Self-service analytics adoption"]),
            ]),
    ))
    files.append(TestFile(
        filename="Northstar_Site_Charging_Notes.docx", fmt="docx",
        category="wrong", scope="floating", expected_project="Aurora-Mobility",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason='Filename says "Northstar" but content is EV charging — Aurora.',
        misleading_filename=True, semantic_required=True,
        semantic_evidence="Charging stations, depot charging, OCPP, off-peak tariff.",
        blocks=_report(
            "Site Charging Notes",
            "2026-05-19",
            [
                ("Notes",
                 "Notes on commissioning depot charging stations and OCPP controllers with "
                 "off-peak scheduling. The analytics codename in the filename does not match "
                 "the charging content."),
                ("Checks",
                 ["Controller connectivity", "Load cap enforcement", "Off-peak windows"]),
            ]),
    ))
    files.append(TestFile(
        filename="Polaris_Room_Booking_Notes.pdf", fmt="pdf",
        category="wrong", scope="floating", expected_project="Atlas-Workplace",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason='Filename says "Polaris" but content is desk/room booking — Atlas.',
        misleading_filename=True, semantic_required=True,
        semantic_evidence="Desk booking, room panels, occupancy analytics, hybrid working.",
        blocks=_report(
            "Room Booking Notes",
            "2026-05-20",
            [
                ("Notes",
                 "Notes on desk and meeting-room booking with door panels and occupancy "
                 "analytics for hybrid working. The sustainability codename in the filename is "
                 "misleading."),
                ("Items",
                 ["App-based booking", "Door-panel availability", "Occupancy analytics"]),
            ]),
    ))
    files.append(TestFile(
        filename="Horizon_Travel_Policy_Notes.docx", fmt="docx",
        category="wrong", scope="floating", expected_project="Meridian-Travel",
        expected_action=SUGGEST_MOVE, confidence="Medium",
        reason='Filename says "Horizon" but content is corporate travel policy — Meridian.',
        misleading_filename=True, semantic_required=True,
        semantic_evidence="Travel policy, pre-trip approval, negotiated rates, duty of care.",
        blocks=_report(
            "Travel Policy Notes",
            "2026-05-21",
            [
                ("Notes",
                 "Notes on corporate travel policy: pre-trip approval, negotiated rates, and "
                 "duty-of-care tracking. The logistics codename in the filename is misleading."),
                ("Rules",
                 ["Book through the managed tool", "Approve out-of-policy trips", "Track travellers"]),
            ]),
    ))

    # 5. Unrelated floating (~4)
    files.append(TestFile(
        filename="Personal_Travel_Plans.pdf", fmt="pdf",
        category="unrelated", scope="floating", expected_project=None,
        expected_action=NO_REC, confidence="None",
        reason="Personal holiday plans; unrelated to any programme (not corporate travel).",
        blocks=_report(
            "Personal Travel Plans",
            "Personal",
            [
                ("Itinerary",
                 "A personal holiday itinerary with flights, a hotel, and sightseeing notes. "
                 "Purely personal and unrelated to any work programme."),
                ("Notes", ["Book museum tickets", "Pack for warm weather", "Airport transfer"]),
            ]),
    ))
    files.append(TestFile(
        filename="Home_Renovation_Budget.xlsx", fmt="xlsx",
        category="unrelated", scope="floating", expected_project=None,
        expected_action=NO_REC, confidence="None",
        reason="Personal home renovation budget; no programme relevance.",
        sheets=[
            SheetSpec(
                title="Budget",
                intro=["Home Renovation Budget", "Personal"],
                header=["Room", "Estimate"],
                rows=[["Bathroom", "EUR 5,200"], ["Bedroom", "EUR 1,800"], ["Garden", "EUR 2,400"]]),
        ],
    ))
    files.append(TestFile(
        filename="Photography_Gear_Guide.pdf", fmt="pdf",
        category="unrelated", scope="floating", expected_project=None,
        expected_action=NO_REC, confidence="None",
        reason="Hobby photography gear guide; unrelated to any programme.",
        blocks=_report(
            "Photography Gear Guide",
            "Personal hobby",
            [
                ("Gear",
                 "A personal guide to choosing a first camera, lenses, and a tripod for hobby "
                 "photography."),
                ("Picks", ["Entry mirrorless body", "50mm prime lens", "Lightweight tripod"]),
            ]),
    ))
    files.append(TestFile(
        filename="Personal_Insurance_Information.pdf", fmt="pdf",
        category="unrelated", scope="floating", expected_project=None,
        expected_action=NO_REC, confidence="None",
        reason="Personal insurance information; unrelated to any programme.",
        blocks=_report(
            "Personal Insurance Information",
            "Personal  |  Policy No. SYN-000-DEMO",
            [
                ("Summary",
                 "A summary of personal home and contents insurance cover, excesses, and "
                 "renewal date. Entirely personal."),
                ("Cover", ["Buildings", "Contents", "Accidental damage"]),
            ]),
    ))

    # 6. Duplicate / updated floating (~5)
    am = _p("Aurora-Mobility")
    files.append(TestFile(
        filename="Technical_Architecture_Final.pdf", fmt="pdf",
        category="duplicate", scope="floating", expected_project=am.key,
        expected_action=UPDATED_VERSION, confidence="High",
        reason="Final Aurora architecture: overlaps v1 with an added component and requirement.",
        existing_file="Aurora-Mobility/Technical_Architecture.pdf", relationship=REL_UPDATED,
        semantic_required=True,
        blocks=_report(
            "Aurora Mobility — Technical Architecture",
            "Document ID: AM-DOC-003  |  Version: 2.1 (Final, supersedes 1.3)  |  Date: 2026-06-10",
            [
                ("Change Log",
                 ["Added Vehicle-to-Grid interface (as in v2.0)",
                  "Finalised REQ-AM-031 for bidirectional discharge",
                  "Locked component interfaces for build"]),
                ("Components",
                 ("table", (["Component", "Description"],
                            [[n, d] for n, d in am.components]))),
                ("Note",
                 "Final version of the Aurora Mobility architecture; match to the existing "
                 "Technical Architecture as an updated version."),
            ]),
    ))
    ns = _p("Northstar-Analytics")
    files.append(TestFile(
        filename="Data_Platform_Architecture_Draft.pdf", fmt="pdf",
        category="duplicate", scope="floating", expected_project=ns.key,
        expected_action=POSSIBLE_DUP, confidence="Medium",
        reason="Draft of the Northstar data-platform architecture; overlaps the existing architecture.",
        existing_file="Northstar-Analytics/Data_Platform_Architecture.pdf", relationship=REL_POSSIBLE,
        semantic_required=True,
        blocks=_report(
            "Northstar Analytics — Data Platform Architecture (Draft)",
            "Document ID: NS-DOC-003  |  Version: 0.9 draft  |  Date: 2026-02-20",
            [
                ("Overview",
                 ns.summary + " This earlier draft largely matches the baselined architecture "
                 "and should be recognised as a possible duplicate/earlier version."),
                ("Components",
                 ("table", (["Component", "Description"],
                            [[n, d] for n, d in ns.components]))),
            ]),
    ))
    hl = _p("Horizon-Logistics")
    files.append(TestFile(
        filename="Operations_Blueprint_v2.pdf", fmt="pdf",
        category="duplicate", scope="floating", expected_project=hl.key,
        expected_action=UPDATED_VERSION, confidence="High",
        reason="Updated Horizon operations blueprint; overlaps the existing blueprint with a new phase note.",
        existing_file="Horizon-Logistics/Operations_Blueprint.pdf", relationship=REL_UPDATED,
        semantic_required=True,
        blocks=_report(
            "Horizon Logistics — Operations Blueprint",
            "Document ID: HL-DOC-003  |  Version: 2.0 (supersedes 1.3)  |  Date: 2026-06-12",
            [
                ("Change Log",
                 ["Added a peak-season change freeze",
                  "Clarified slotting-before-automation decision"]),
                ("Components",
                 ("table", (["Component", "Description"],
                            [[n, d] for n, d in hl.components]))),
                ("Note", "Updated version of the existing Operations Blueprint."),
            ]),
    ))
    ce = _p("Cedar-Events")
    files.append(TestFile(
        filename="Event_Operating_Plan_Copy.pdf", fmt="pdf",
        category="duplicate", scope="floating", expected_project=ce.key,
        expected_action=POSSIBLE_DUP, confidence="High",
        reason="Unchanged copy of the Cedar event operating plan.",
        existing_file="Cedar-Events/Event_Operating_Plan.pdf", relationship=REL_DUPLICATE,
        semantic_required=True,
        blocks=_report(
            "Cedar Events — Event Operating Plan",
            "Document ID: CE-DOC-003  |  Version: 1.3  |  Date: 2026-03-31",
            [
                ("Overview",
                 ce.summary + " This is an unchanged copy of the operating plan and should be "
                 "flagged as a likely duplicate."),
                ("Components",
                 ("table", (["Component", "Description"],
                            [[n, d] for n, d in ce.components]))),
            ]),
    ))
    ps = _p("Polaris-Sustainability")
    files.append(TestFile(
        filename="Reporting_Methodology_Updated.docx", fmt="docx",
        category="duplicate", scope="floating", expected_project=ps.key,
        expected_action=UPDATED_VERSION, confidence="High",
        reason="Updated Polaris reporting methodology; overlaps the existing methodology with a factor-version change.",
        existing_file="Polaris-Sustainability/Reporting_Methodology.pdf", relationship=REL_UPDATED,
        semantic_required=True,
        blocks=_report(
            "Polaris Sustainability — Reporting Methodology",
            "Document ID: PS-DOC-003  |  Version: 2.0 (supersedes 1.3)  |  Date: 2026-06-14",
            [
                ("Change Log",
                 ["Updated emission-factor library version",
                  "Added restatement policy note"]),
                ("Components",
                 ("table", (["Component", "Description"],
                            [[n, d] for n, d in ps.components]))),
                ("Note", "Updated version of the existing Reporting Methodology."),
            ]),
    ))

    return files


# --- Public accessors -------------------------------------------------------
def all_downloads() -> list[TestFile]:
    return (
        _obvious_downloads()
        + _semantic_downloads()
        + _ambiguous_downloads()
        + _wrong_downloads()
        + _unrelated_downloads()
        + _duplicate_downloads()
    )


def all_floating() -> list[TestFile]:
    return _floating_files()


CATEGORY_LABELS = {
    "obvious": "Obvious Matches",
    "semantic": "Semantic Matches",
    "ambiguous": "Ambiguous Matches",
    "wrong": "Wrong-Project Matches",
    "unrelated": "Completely Unrelated",
    "duplicate": "Duplicate / Updated Versions",
}
