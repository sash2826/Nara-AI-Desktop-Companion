"""Content builders that render each project's document set.

Every builder consumes a :class:`~scripts.eac_benchmark.data.Project` and returns
declarative blocks (or sheet/slide specs) for the ``common`` renderers. Documents
cross-reference each other by document ID and requirement ID to form a realistic
knowledge network.
"""

from __future__ import annotations

import os

from scripts.benchmark_corpus.common import (
    SheetSpec,
    SlideSpec,
    write_docx,
    write_pdf,
    write_pptx,
    write_xlsx,
)

from .data import Project


def _doc_id(p: Project, n: int) -> str:
    return f"{p.code}-DOC-{n:03d}"


def _people_rows(p: Project) -> list[list[str]]:
    return [[name, role] for name, role in p.people]


# --- 1. Project Overview (PDF) ----------------------------------------------
def overview_blocks(p: Project) -> list:
    arch_name = os.path.splitext(p.arch_doc[0])[0].replace("_", " ")
    return [
        ("title", f"{p.display} — Project Overview"),
        ("para", f"Document ID: {_doc_id(p, 1)}  |  Version: 1.2  |  Date: 2026-03-04  |  Owner: {p.director[0]} ({p.director[1]})"),
        ("heading", "Executive Summary"),
        ("para", p.summary + " This overview summarises the objectives, scope, "
         "stakeholders, and delivery approach that the remaining project documents "
         "expand upon. It is the entry point for anyone new to the programme and is "
         "referenced by the Requirements Specification and the " + arch_name + "."),
        ("heading", "Background"),
        ("para", p.background),
        ("para", f"The programme is sponsored by {p.sponsor}. It operates as a governed "
         "programme with a defined stakeholder group, a phased delivery plan, and a "
         "controlled budget. Decisions taken during initiation are recorded in the "
         "Meeting Notes and carried into the design and planning documents so that the "
         "rationale behind the solution remains traceable."),
        ("heading", "Objectives"),
        ("bullets", p.objectives),
        ("heading", "Scope"),
        ("para", "In scope: " + p.scope_in),
        ("para", "Out of scope: " + p.scope_out),
        ("heading", "Stakeholders"),
        ("table", (["Name", "Role"], _people_rows(p))),
        ("heading", "Delivery Approach"),
        ("para", "Delivery is organised into sequential phases, each ending in a "
         "measurable milestone. Early phases establish the foundation and a pilot; later "
         "phases expand coverage and optimise performance. The Deployment Plan describes "
         "the sequencing in detail, while the Budget and Cost Forecast and Project "
         "Timeline track cost and schedule against these phases."),
        ("heading", "Key Milestones"),
        ("table", (["Phase", "Target Date", "Deliverable"],
                   [[ph, dt, dl] for ph, dt, dl in p.milestones])),
        ("heading", "Related Documents"),
        ("bullets", [
            f"Requirements Specification ({_doc_id(p, 2)})",
            f"{arch_name} ({_doc_id(p, 3)})",
            f"Vendor Evaluation ({_doc_id(p, 4)})",
            f"Deployment Plan ({_doc_id(p, 5)})",
            f"Risk Assessment ({_doc_id(p, 7)})",
            f"Budget and Cost Forecast ({_doc_id(p, 9)})",
        ]),
    ]


# --- 2. Requirements Specification (DOCX) -----------------------------------
def requirements_blocks(p: Project) -> list:
    arch_name = os.path.splitext(p.arch_doc[0])[0].replace("_", " ")
    return [
        ("title", f"{p.display} — Requirements Specification"),
        ("para", f"Document ID: {_doc_id(p, 2)}  |  Version: 1.4  |  Date: 2026-03-18  |  Author: {p.people[2][0]}"),
        ("heading", "Purpose"),
        ("para", f"This specification defines the functional and non-functional "
         f"requirements for {p.display}. Requirements are traced into the {arch_name} "
         f"({_doc_id(p, 3)}) and validated against the Deployment Plan ({_doc_id(p, 5)}). "
         "It builds on the objectives and scope established in the Project Overview "
         f"({_doc_id(p, 1)})."),
        ("heading", "Context"),
        ("para", p.background),
        ("heading", "Functional Requirements"),
        ("para", "The following requirements are prioritised using MoSCoW. Must-have "
         "requirements define the minimum viable capability for the first release; "
         "should-have requirements are targeted for later phases."),
        ("table", (["ID", "Requirement", "Priority"],
                   [[rid, text, prio] for rid, text, prio in p.requirements])),
        ("heading", "Non-Functional Requirements"),
        ("bullets", [
            "Availability: the service shall meet the availability target defined for its phase.",
            "Security: access shall follow least privilege and be auditable.",
            "Performance: user-facing operations shall respond within agreed service levels.",
            "Maintainability: components shall be independently deployable and monitored.",
            "Data protection: only synthetic, non-personal data is used in this programme corpus.",
        ]),
        ("heading", "Constraints and Dependencies"),
        ("bullets", [
            f"Solution design must align with the component baseline in the {arch_name}.",
            f"Delivery depends on {p.vendors[0][0]} and {p.vendors[1][0]} availability.",
            "Phasing must respect the milestones recorded in the Project Overview.",
        ]),
        ("heading", "Acceptance Criteria"),
        ("para", "Each requirement is accepted when its corresponding capability passes "
         "the test cases defined during the relevant phase and is demonstrated against "
         "the objectives in the Project Overview. Traceability from requirement to design "
         "to test is maintained throughout delivery."),
    ]


# --- 3. Architecture / Operating Model (PDF) --------------------------------
def architecture_blocks(p: Project) -> list:
    _, title, kind = p.arch_doc
    intro_word = "Technical Architecture" if kind == "technical" else "Operating Model"
    return [
        ("title", title),
        ("para", f"Document ID: {_doc_id(p, 3)}  |  Version: 1.3  |  Date: 2026-03-31  |  Author: {p.people[1][0]}"),
        ("heading", "Purpose"),
        ("para", f"This {intro_word} defines the reference design for {p.display}. It "
         f"realises the capabilities captured in the Requirements Specification "
         f"({_doc_id(p, 2)}) and provides the component baseline referenced by the Vendor "
         f"Evaluation ({_doc_id(p, 4)}) and the Deployment Plan ({_doc_id(p, 5)})."),
        ("heading", "Overview"),
        ("para", p.summary + " The design separates concerns into distinct components so "
         "that a change in one vendor or subsystem does not ripple across the whole "
         "solution. Components communicate through defined interfaces and are deployed "
         "and monitored independently."),
        ("heading", "Components"),
        ("table", (["Component", "Description"],
                   [[name, desc] for name, desc in p.components])),
        ("heading", "Requirements Traceability"),
        ("para", "The components above collectively satisfy the requirements below. Each "
         "must-have requirement maps to at least one component, ensuring the design is "
         "complete against the specification."),
        ("table", (["Requirement", "Realised by"],
                   [[rid, p.components[i % len(p.components)][0]]
                    for i, (rid, _t, _pr) in enumerate(p.requirements)])),
        ("heading", "Key Design Decisions"),
        ("table", (["ID", "Decision", "Rationale"],
                   [[did, dec, rat] for did, dec, rat in p.decisions])),
        ("heading", "Integration and Interfaces"),
        ("para", f"External integration is provided by {p.vendors[2][0]} and internal "
         "interfaces are versioned so that vendor components can be replaced without "
         "changing downstream logic. The Vendor Evaluation assesses candidate products "
         "against these components, and the Deployment Plan sequences their rollout."),
        ("heading", "Non-Functional Considerations"),
        ("bullets", [
            "Resilience: components degrade gracefully and recover without data loss.",
            "Security: interfaces are authenticated, authorised, and logged.",
            "Observability: each component emits health and performance telemetry.",
            "Scalability: components scale independently to meet phase-level demand.",
        ]),
    ]


# --- 4. Vendor Evaluation (DOCX) --------------------------------------------
def vendor_blocks(p: Project) -> list:
    arch_name = os.path.splitext(p.arch_doc[0])[0].replace("_", " ")
    scored = []
    base = [86, 79, 73]
    for i, (name, offering) in enumerate(p.vendors):
        scored.append([name, offering, str(base[i % len(base)]),
                       "Selected" if i == 0 else "Shortlisted" if i == 1 else "Not selected"])
    return [
        ("title", f"{p.display} — Vendor Evaluation"),
        ("para", f"Document ID: {_doc_id(p, 4)}  |  Version: 1.1  |  Date: 2026-04-04  |  Author: {p.people[1][0]}"),
        ("heading", "Purpose"),
        ("para", f"This evaluation assesses candidate vendors for {p.display} against the "
         f"component baseline defined in the {arch_name} ({_doc_id(p, 3)}) and the "
         f"requirements in the Requirements Specification ({_doc_id(p, 2)})."),
        ("heading", "Evaluation Criteria"),
        ("bullets", [
            "Fit against the required components and interfaces.",
            "Total cost of ownership across the programme lifecycle.",
            "Delivery capability, references, and support model.",
            "Security posture and compliance with programme controls.",
            "Roadmap alignment and interoperability.",
        ]),
        ("heading", "Candidate Assessment"),
        ("table", (["Vendor", "Offering", "Score", "Outcome"], scored)),
        ("heading", "Recommendation"),
        ("para", f"{p.vendors[0][0]} is recommended as the primary vendor based on the "
         "strongest fit against the component baseline and the most credible delivery "
         f"capability. {p.vendors[1][0]} is retained as a shortlisted alternative to "
         "preserve competitive tension and reduce single-vendor risk, consistent with the "
         "mitigation recorded in the Risk Assessment."),
        ("heading", "Next Steps"),
        ("bullets", [
            "Confirm commercial terms with the recommended vendor.",
            "Align the contract to the phase milestones in the Deployment Plan.",
            "Feed selected products into the component baseline for design finalisation.",
        ]),
    ]


# --- 5. Deployment Plan (PDF) -----------------------------------------------
def deployment_blocks(p: Project) -> list:
    arch_name = os.path.splitext(p.arch_doc[0])[0].replace("_", " ")
    phase_rows = []
    for ph, dt, dl in p.milestones:
        phase_rows.append([ph, dt, dl])
    return [
        ("title", f"{p.display} — Deployment Plan"),
        ("para", f"Document ID: {_doc_id(p, 5)}  |  Version: 1.2  |  Date: 2026-04-09  |  Owner: {p.director[0]}"),
        ("heading", "Purpose"),
        ("para", f"This Deployment Plan sequences the rollout of {p.display}. It builds "
         f"directly on the {arch_name} ({_doc_id(p, 3)}) component baseline and the "
         f"selected vendor from the Vendor Evaluation ({_doc_id(p, 4)}), and delivers the "
         f"requirements in the Requirements Specification ({_doc_id(p, 2)})."),
        ("heading", "Deployment Strategy"),
        ("para", "Rollout is phased to limit risk and to capture value early. Each phase "
         "delivers a coherent, usable increment, is validated against acceptance "
         "criteria, and informs the next phase. A pilot precedes wider rollout so that "
         "issues are found at small scale."),
        ("heading", "Phase Plan"),
        ("table", (["Phase", "Target Date", "Deliverable"], phase_rows)),
        ("heading", "Cutover and Rollback"),
        ("para", "Each phase defines entry and exit criteria. Cutover occurs only when "
         "exit criteria are met, and every phase has a documented rollback path that "
         "restores the previous stable state without data loss. High-risk phases include "
         "a parallel-run period."),
        ("heading", "Dependencies"),
        ("bullets", [
            f"Availability of {p.vendors[0][0]} components per the contract schedule.",
            "Completion of the preceding phase's exit criteria.",
            "Readiness of integration interfaces defined in the architecture.",
            "Stakeholder sign-off recorded against each milestone.",
        ]),
        ("heading", "Operational Readiness"),
        ("para", "Before each go-live, operational readiness is confirmed: monitoring is "
         "in place, support processes are defined, and users are trained. The Status "
         f"Report ({_doc_id(p, 8)}) tracks readiness and progress against this plan."),
    ]


# --- 6. Meeting Notes (DOCX) ------------------------------------------------
def meeting_blocks(p: Project) -> list:
    m = p.meeting
    return [
        ("title", f"{p.display} — Programme Meeting Notes"),
        ("para", f"Document ID: {_doc_id(p, 6)}  |  Date: {m['date']}  |  Chair: {p.director[0]}"),
        ("heading", "Attendees"),
        ("bullets", list(m["attendees"])),
        ("heading", "Purpose"),
        ("para", f"This meeting reviewed decisions arising from the Project Overview "
         f"({_doc_id(p, 1)}) and Requirements Specification ({_doc_id(p, 2)}) and "
         "confirmed the direction for design, vendor selection, and deployment."),
        ("heading", "Decisions"),
        ("bullets", list(m["decisions"])),
        ("heading", "Actions"),
        ("table", (["Owner", "Action", "Due"],
                   [[owner, action, due] for owner, action, due in m["actions"]])),
        ("heading", "Notes"),
        ("para", "The decisions above are reflected in the Design Decisions section of "
         f"the architecture document ({_doc_id(p, 3)}) and the vendor recommendation "
         f"({_doc_id(p, 4)}). Open actions will be reviewed at the next programme meeting."),
    ]


# --- 7. Risk Assessment (PDF) -----------------------------------------------
def risk_blocks(p: Project) -> list:
    return [
        ("title", f"{p.display} — Risk Assessment"),
        ("para", f"Document ID: {_doc_id(p, 7)}  |  Version: 1.1  |  Date: 2026-04-02  |  Owner: {p.director[0]}"),
        ("heading", "Purpose"),
        ("para", f"This assessment identifies the principal risks to {p.display} and the "
         "mitigations in place. Risks reference the scope and dependencies in the Project "
         f"Overview ({_doc_id(p, 1)}) and the delivery sequencing in the Deployment Plan "
         f"({_doc_id(p, 5)})."),
        ("heading", "Risk Register"),
        ("table", (["ID", "Risk", "Likelihood", "Impact", "Mitigation"],
                   [[rid, desc, lik, imp, mit] for rid, desc, lik, imp, mit in p.risks])),
        ("heading", "Risk Management Approach"),
        ("para", "Risks are reviewed at each programme meeting and re-scored as "
         "mitigations take effect. High-likelihood, high-impact risks drive phasing "
         "decisions and contingency allocation in the Budget and Cost Forecast "
         f"({_doc_id(p, 9)}). New risks identified during delivery are added to this "
         "register and tracked to closure."),
        ("heading", "Contingency"),
        ("para", "A contingency reserve is held at programme level, sized against the "
         "residual risk exposure after mitigation. Drawdown requires programme-director "
         "approval and is reported in the Status Report."),
    ]


# --- 8. Status Report (PDF) -------------------------------------------------
def status_blocks(p: Project) -> list:
    return [
        ("title", f"{p.display} — Status Report"),
        ("para", f"Document ID: {_doc_id(p, 8)}  |  Reporting Period: March 2026  |  Owner: {p.director[0]}"),
        ("heading", "Overall Status"),
        ("para", "Programme status is GREEN. Initiation is complete, the requirements and "
         "architecture are baselined, and the recommended vendor has been selected. The "
         "first delivery phase is on track against the milestones in the Project Overview."),
        ("heading", "Progress This Period"),
        ("bullets", [
            f"Baselined the Requirements Specification ({_doc_id(p, 2)}).",
            f"Approved the architecture and component baseline ({_doc_id(p, 3)}).",
            f"Completed the Vendor Evaluation and selected {p.vendors[0][0]}.",
            "Confirmed the phased deployment approach and readiness criteria.",
        ]),
        ("heading", "Milestone Tracking"),
        ("table", (["Phase", "Target Date", "Status"],
                   [[ph, dt, "On track"] for ph, dt, _dl in p.milestones])),
        ("heading", "Key Risks and Issues"),
        ("table", (["ID", "Risk", "Status"],
                   [[rid, desc, "Mitigation in progress"] for rid, desc, _l, _i, _m in p.risks[:3]])),
        ("heading", "Next Period"),
        ("bullets", [
            "Finalise vendor commercial terms.",
            "Complete design finalisation against the component baseline.",
            "Begin the Foundation phase per the Deployment Plan.",
        ]),
    ]


# --- 9. Budget and Cost Forecast (XLSX) -------------------------------------
def budget_sheets(p: Project) -> list[SheetSpec]:
    rows = [[item, amount] for item, amount in p.budget]
    total = 0
    for _item, amount in p.budget:
        digits = amount.replace("EUR", "").replace(",", "").strip()
        try:
            total += int(digits)
        except ValueError:
            pass
    rows.append(["TOTAL", f"EUR {total:,}"])
    phasing = []
    for ph, dt, _dl in p.milestones:
        phasing.append([ph, dt, "See phase allocation"])
    return [
        SheetSpec(
            title="Budget",
            intro=[f"{p.display} — Budget and Cost Forecast ({_doc_id(p, 9)})",
                   f"Owner: {p.director[0]}  |  Version 1.2  |  Currency: EUR"],
            header=["Cost Category", "Budget"],
            rows=rows,
        ),
        SheetSpec(
            title="Phasing",
            intro=["Indicative spend phasing aligned to programme milestones."],
            header=["Phase", "Target Date", "Notes"],
            rows=phasing,
        ),
    ]


# --- 10. Project Timeline (XLSX) --------------------------------------------
def timeline_sheets(p: Project) -> list[SheetSpec]:
    rows = []
    for ph, dt, dl in p.milestones:
        rows.append([ph, dt, dl, "Planned"])
    return [
        SheetSpec(
            title="Timeline",
            intro=[f"{p.display} — Project Timeline ({_doc_id(p, 10)})",
                   f"Owner: {p.director[0]}  |  Version 1.1"],
            header=["Phase", "Target Date", "Deliverable", "Status"],
            rows=rows,
        ),
    ]


# --- 11. Overview Presentation (PPTX) ---------------------------------------
def presentation(p: Project) -> tuple[str, str, list[SlideSpec]]:
    slides = [
        SlideSpec(title="Programme Summary", subtitle=p.summary),
        SlideSpec(title="Objectives", bullets=p.objectives),
        SlideSpec(title="Scope",
                  bullets=["In scope: " + p.scope_in, "Out of scope: " + p.scope_out]),
        SlideSpec(title="Solution Components",
                  bullets=[f"{name}: {desc}" for name, desc in p.components]),
        SlideSpec(title="Milestones",
                  bullets=[f"{ph} — {dt}: {dl}" for ph, dt, dl in p.milestones]),
        SlideSpec(title="Top Risks",
                  bullets=[f"{rid}: {desc} (mitigation in place)" for rid, desc, _l, _i, _m in p.risks[:4]]),
        SlideSpec(title="Recommended Vendor",
                  bullets=[f"Primary: {p.vendors[0][0]} — {p.vendors[0][1]}",
                           f"Alternative: {p.vendors[1][0]} — {p.vendors[1][1]}"]),
    ]
    return (f"{p.display}", f"Programme Overview  |  Owner: {p.director[0]}", slides)


# --- Orchestration ----------------------------------------------------------
def generate_project(project: Project, projects_root: str) -> list[str]:
    """Generate the full document set for one project. Returns written paths."""
    d = os.path.join(projects_root, project.key)
    written: list[str] = []

    def pdf(name: str, blocks: list) -> None:
        path = os.path.join(d, name)
        write_pdf(path, blocks)
        written.append(path)

    def docx(name: str, blocks: list) -> None:
        path = os.path.join(d, name)
        write_docx(path, blocks)
        written.append(path)

    def xlsx(name: str, sheets: list[SheetSpec]) -> None:
        path = os.path.join(d, name)
        write_xlsx(path, sheets)
        written.append(path)

    pdf("Project_Overview.pdf", overview_blocks(project))
    docx("Requirements_Specification.docx", requirements_blocks(project))
    pdf(project.arch_doc[0], architecture_blocks(project))
    docx("Vendor_Evaluation.docx", vendor_blocks(project))
    pdf("Deployment_Plan.pdf", deployment_blocks(project))
    docx("Meeting_Notes.docx", meeting_blocks(project))
    pdf("Risk_Assessment.pdf", risk_blocks(project))
    pdf("Status_Report.pdf", status_blocks(project))
    xlsx("Budget_and_Cost_Forecast.xlsx", budget_sheets(project))
    xlsx("Project_Timeline.xlsx", timeline_sheets(project))

    ppt_path = os.path.join(d, "Overview_Presentation.pptx")
    title, subtitle, slides = presentation(project)
    write_pptx(ppt_path, title, subtitle, slides)
    written.append(ppt_path)

    return written
