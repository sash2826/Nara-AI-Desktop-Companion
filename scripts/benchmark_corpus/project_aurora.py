"""Aurora Mobility project corpus — EV charging infrastructure.

Domain terminology: EV charging, charging stations, fleet charging, energy
management, charging network, deployment, load balancing.
"""

from __future__ import annotations

import os

from .common import SheetSpec, SlideSpec, write_docx, write_pdf, write_pptx, write_xlsx

PROJECT = "Aurora-Mobility"

# Reusable prose blocks (also consumed by the duplicate/updated download file).
ARCH_INTRO = (
    "This Technical Architecture defines the reference design for the Aurora "
    "Mobility electric-vehicle charging platform. It realises the capabilities "
    "captured in the Requirements Specification (REQ-AM series) and provides the "
    "component baseline referenced by the Vendor Evaluation and the Charging "
    "Network Deployment Plan."
)
ARCH_LAYERS = (
    "The platform is organised into four layers: the Charging Edge (station "
    "controllers and OCPP gateways), the Energy Management core (load balancing "
    "and tariff optimisation), the Fleet Services layer (reservations, session "
    "orchestration, billing), and the Analytics layer (utilisation and demand "
    "reporting). Layers communicate through versioned internal APIs so that a "
    "hardware vendor change does not ripple into fleet business logic."
)
ARCH_GATEWAY = (
    "Each charging station connects to the Aurora core through an OCPP 2.0.1 "
    "charging gateway. The gateway buffers session telemetry, applies local load "
    "limits when connectivity is degraded, and reconciles meter values once the "
    "link is restored. This satisfies REQ-AM-014 (resilient offline charging)."
)


def generate(root: str) -> list[str]:
    project_dir = os.path.join(root, PROJECT)
    written: list[str] = []

    # 1. Project Overview (PDF)
    path = os.path.join(project_dir, "Project_Overview.pdf")
    write_pdf(
        path,
        [
            ("title", "Aurora Mobility — Project Overview"),
            ("para", "Document ID: AM-DOC-001  |  Version: 1.2  |  Date: 2026-03-04  |  Owner: Priya Nandakumar (Programme Director)"),
            ("heading", "Executive Summary"),
            ("para",
             "Aurora Mobility is a programme to design, deploy, and operate a metropolitan "
             "electric-vehicle (EV) charging network serving both public drivers and managed "
             "commercial fleets. The programme delivers charging stations, an energy management "
             "platform, and fleet charging services under a single operating model. This overview "
             "summarises the objectives, scope, stakeholders, and delivery approach that the "
             "remaining Aurora Mobility documents expand upon."),
            ("heading", "Background"),
            ("para",
             "Regional fleet operators face rising demand for reliable depot and on-route charging. "
             "Aurora Mobility consolidates fragmented charging pilots into one managed charging "
             "network with predictable energy costs and centralised monitoring. The programme is "
             "sponsored by the fictional operator Meridian Transit Cooperative."),
            ("heading", "Objectives"),
            ("bullets", [
                "Deploy 120 public and 40 depot charging stations across three service zones.",
                "Provide fleet charging scheduling that respects grid load limits and energy tariffs.",
                "Achieve 99.2% charging station availability measured monthly.",
                "Establish an energy management capability that shifts charging to off-peak windows.",
            ]),
            ("heading", "Scope"),
            ("para",
             "In scope: charging station hardware selection, the charging network control platform, "
             "fleet charging services, and energy management. Out of scope: vehicle procurement and "
             "on-vehicle telematics, which remain with individual fleet owners."),
            ("heading", "Stakeholders"),
            ("table", (
                ["Name", "Role", "Interest"],
                [
                    ["Priya Nandakumar", "Programme Director", "Overall delivery and budget"],
                    ["Tomas Ek", "Energy Management Lead", "Load balancing and tariffs"],
                    ["Rosa Marín", "Fleet Services Lead", "Depot charging scheduling"],
                    ["Devon Clarke", "Security Officer", "Charging network security"],
                ],
            )),
            ("heading", "Delivery Approach"),
            ("para",
             "Delivery follows three releases: Foundation (energy management core and first zone), "
             "Expansion (remaining zones and depot charging), and Optimisation (advanced load "
             "balancing). The Requirements Specification, Technical Architecture, and Charging "
             "Network Deployment Plan detail each release."),
            ("heading", "Related Documents"),
            ("bullets", [
                "Requirements Specification (AM-DOC-002)",
                "Technical Architecture (AM-DOC-003)",
                "Charging Network Deployment Plan (AM-DOC-004)",
                "Budget and Cost Forecast (AM-DOC-007)",
            ]),
        ],
    )
    written.append(path)

    # 2. Requirements Specification (DOCX)
    path = os.path.join(project_dir, "Requirements_Specification.docx")
    write_docx(
        path,
        [
            ("title", "Aurora Mobility — Requirements Specification"),
            ("para", "Document ID: AM-DOC-002  |  Version: 1.4  |  Date: 2026-03-18  |  Author: Rosa Marín"),
            ("heading", "Purpose"),
            ("para",
             "This specification defines functional and non-functional requirements for the Aurora "
             "Mobility charging network. Requirements are traced into the Technical Architecture "
             "(AM-DOC-003) and validated against the Charging Network Deployment Plan (AM-DOC-004)."),
            ("heading", "Functional Requirements"),
            ("table", (
                ["ID", "Requirement", "Priority"],
                [
                    ["REQ-AM-001", "The system shall register and monitor each charging station in real time.", "Must"],
                    ["REQ-AM-005", "The system shall support fleet charging reservations per depot.", "Must"],
                    ["REQ-AM-009", "Energy management shall shift charging sessions to off-peak tariff windows.", "Must"],
                    ["REQ-AM-012", "The system shall balance load across stations sharing a grid connection.", "Must"],
                    ["REQ-AM-014", "Stations shall continue charging within local limits during connectivity loss.", "Should"],
                    ["REQ-AM-021", "The system shall report charging station utilisation per zone.", "Should"],
                ],
            )),
            ("heading", "Non-Functional Requirements"),
            ("bullets", [
                "REQ-AM-030: Charging station availability shall meet 99.2% measured monthly.",
                "REQ-AM-031: Session telemetry shall be persisted within five seconds of a meter reading.",
                "REQ-AM-034: All charging network APIs shall require mutual TLS authentication.",
            ]),
            ("heading", "Assumptions and Dependencies"),
            ("para",
             "Requirements assume OCPP 2.0.1 capable hardware and a metered grid connection per site. "
             "Energy management depends on tariff schedules supplied by the regional distribution "
             "operator. Security requirements are elaborated in the Security Assessment (AM-DOC-005)."),
        ],
    )
    written.append(path)

    # 3. Technical Architecture (PDF)  -- has a v2 duplicate in downloads
    path = os.path.join(project_dir, "Technical_Architecture.pdf")
    write_pdf(
        path,
        [
            ("title", "Aurora Mobility — Technical Architecture"),
            ("para", "Document ID: AM-DOC-003  |  Version: 1.1  |  Date: 2026-04-02  |  Author: Tomas Ek"),
            ("heading", "Overview"),
            ("para", ARCH_INTRO),
            ("heading", "Layered Architecture"),
            ("para", ARCH_LAYERS),
            ("heading", "Charging Gateway"),
            ("para", ARCH_GATEWAY),
            ("heading", "Energy Management Core"),
            ("para",
             "The Energy Management core evaluates active charging sessions against grid limits and "
             "tariff windows every 30 seconds. It implements REQ-AM-009 and REQ-AM-012 by lowering "
             "delivered power on non-priority sessions before curtailing fleet-critical charging."),
            ("heading", "Data and Integration"),
            ("table", (
                ["Component", "Responsibility", "Related Requirement"],
                [
                    ["Station Registry", "Track station state and firmware", "REQ-AM-001"],
                    ["Session Orchestrator", "Manage fleet reservations", "REQ-AM-005"],
                    ["Load Balancer", "Distribute grid capacity", "REQ-AM-012"],
                    ["Telemetry Store", "Persist meter values", "REQ-AM-031"],
                ],
            )),
            ("heading", "Cross-References"),
            ("para",
             "Component selection for the Charging Edge and Energy Management core is assessed in the "
             "Vendor Evaluation (AM-DOC-006). Rollout sequencing is defined in the Charging Network "
             "Deployment Plan (AM-DOC-004)."),
        ],
    )
    written.append(path)

    # 4. Charging Network Deployment Plan (PDF)
    path = os.path.join(project_dir, "Charging_Network_Deployment_Plan.pdf")
    write_pdf(
        path,
        [
            ("title", "Aurora Mobility — Charging Network Deployment Plan"),
            ("para", "Document ID: AM-DOC-004  |  Version: 1.0  |  Date: 2026-04-15  |  Owner: Rosa Marín"),
            ("heading", "Purpose"),
            ("para",
             "This plan sequences the physical and logical rollout of the Aurora Mobility charging "
             "network across three service zones, realising the architecture in AM-DOC-003 and the "
             "requirements in AM-DOC-002."),
            ("heading", "Deployment Phases"),
            ("table", (
                ["Phase", "Zone", "Stations", "Target Window"],
                [
                    ["Foundation", "Zone North", "40 public + 15 depot", "Q2 2026"],
                    ["Expansion", "Zone Central", "50 public + 15 depot", "Q3 2026"],
                    ["Optimisation", "Zone South", "30 public + 10 depot", "Q4 2026"],
                ],
            )),
            ("heading", "Site Readiness"),
            ("bullets", [
                "Confirm metered grid connection and capacity per site.",
                "Install OCPP 2.0.1 charging gateways and validate load balancing.",
                "Commission depot fleet charging schedules with each fleet owner.",
            ]),
            ("heading", "Risks"),
            ("para",
             "Grid connection lead times are the primary schedule risk. Energy management commissioning "
             "depends on tariff data availability. Mitigations are tracked in the Meeting Notes (AM-DOC-008)."),
        ],
    )
    written.append(path)

    # 5. Security Assessment (PDF)
    path = os.path.join(project_dir, "Security_Assessment.pdf")
    write_pdf(
        path,
        [
            ("title", "Aurora Mobility — Security Assessment"),
            ("para", "Document ID: AM-DOC-005  |  Version: 1.0  |  Date: 2026-04-22  |  Author: Devon Clarke"),
            ("heading", "Scope"),
            ("para",
             "This assessment evaluates the security posture of the Aurora Mobility charging network, "
             "covering charging station endpoints, the OCPP gateway, and the energy management APIs "
             "defined in the Technical Architecture (AM-DOC-003)."),
            ("heading", "Threats and Controls"),
            ("table", (
                ["Threat", "Impact", "Control"],
                [
                    ["Rogue station firmware", "Unauthorised charging", "Signed firmware, station registry attestation"],
                    ["API abuse", "Session hijack", "Mutual TLS per REQ-AM-034"],
                    ["Telemetry tampering", "Billing fraud", "Meter value signing and reconciliation"],
                    ["Load command spoofing", "Grid overload", "Authenticated load-balancer channel"],
                ],
            )),
            ("heading", "Findings"),
            ("bullets", [
                "Charging gateway authentication meets requirements; certificate rotation to be automated.",
                "Energy management APIs require rate limiting before public zone launch.",
                "Depot fleet charging endpoints need per-fleet access scopes.",
            ]),
            ("heading", "Recommendation"),
            ("para",
             "Proceed to Foundation deployment with automated certificate rotation and API rate limiting "
             "treated as launch-blocking items."),
        ],
    )
    written.append(path)

    # 6. Vendor Evaluation (DOCX)
    path = os.path.join(project_dir, "Vendor_Evaluation.docx")
    write_docx(
        path,
        [
            ("title", "Aurora Mobility — Vendor Evaluation"),
            ("para", "Document ID: AM-DOC-006  |  Version: 1.1  |  Date: 2026-04-28  |  Author: Tomas Ek"),
            ("heading", "Purpose"),
            ("para",
             "This evaluation selects hardware and platform vendors for the charging network components "
             "defined in the Technical Architecture (AM-DOC-003). Costs feed the Budget and Cost "
             "Forecast (AM-DOC-007)."),
            ("heading", "Candidate Vendors"),
            ("table", (
                ["Vendor", "Component", "Score (/100)", "Notes"],
                [
                    ["VoltEdge Systems", "Charging stations + gateway", "88", "Strong OCPP 2.0.1 support"],
                    ["GridHarmony", "Energy management core", "84", "Good tariff optimisation"],
                    ["ChargePoint Nordic (fictional)", "Charging stations", "79", "Higher unit cost"],
                    ["MeterLink", "Telemetry metering", "82", "Signed meter values"],
                ],
            )),
            ("heading", "Recommendation"),
            ("para",
             "Award charging stations and gateways to VoltEdge Systems and the energy management core to "
             "GridHarmony. MeterLink is recommended for signed telemetry metering to support the Security "
             "Assessment (AM-DOC-005) controls."),
        ],
    )
    written.append(path)

    # 7. Budget and Cost Forecast (XLSX)
    path = os.path.join(project_dir, "Budget_and_Cost_Forecast.xlsx")
    write_xlsx(
        path,
        [
            SheetSpec(
                title="Capex",
                intro=["Aurora Mobility — Budget and Cost Forecast (AM-DOC-007)", "Version 1.0  |  2026-05-02  |  Currency: EUR (fictional)"],
                header=["Item", "Vendor", "Qty", "Unit Cost", "Total"],
                rows=[
                    ["Public charging station", "VoltEdge Systems", 120, 8200, 984000],
                    ["Depot charging station", "VoltEdge Systems", 40, 11500, 460000],
                    ["OCPP charging gateway", "VoltEdge Systems", 160, 640, 102400],
                    ["Energy management core", "GridHarmony", 1, 145000, 145000],
                    ["Telemetry metering kit", "MeterLink", 160, 310, 49600],
                ],
            ),
            SheetSpec(
                title="Opex",
                header=["Item", "Basis", "Annual Cost"],
                rows=[
                    ["Charging network operations", "Managed service", 210000],
                    ["Energy management support", "GridHarmony support", 38000],
                    ["Grid connection charges", "Per depot", 96000],
                    ["Charging station maintenance", "Per station/year", 72000],
                ],
            ),
        ],
    )
    written.append(path)

    # 8. Meeting Notes (DOCX)
    path = os.path.join(project_dir, "Meeting_Notes.docx")
    write_docx(
        path,
        [
            ("title", "Aurora Mobility — Sprint & Meeting Notes"),
            ("para", "Document ID: AM-DOC-008  |  Version: rolling  |  Last updated: 2026-05-06"),
            ("heading", "2026-04-03 — Architecture Review"),
            ("para",
             "Following the architecture review described in the Technical Architecture document "
             "(AM-DOC-003), the team approved the revised charging gateway design and confirmed OCPP "
             "2.0.1 as the station protocol. Action: Tomas to finalise energy management load-balancing "
             "thresholds."),
            ("heading", "2026-04-24 — Vendor Down-Select"),
            ("para",
             "The team accepted the Vendor Evaluation (AM-DOC-006) recommendation to award charging "
             "stations to VoltEdge Systems and the energy management core to GridHarmony. Budget impact "
             "to be reflected in AM-DOC-007."),
            ("heading", "2026-05-05 — Deployment Readiness"),
            ("para",
             "Zone North grid connections confirmed. Depot fleet charging schedules under negotiation "
             "with Meridian Transit Cooperative. Risk: tariff data delivery for energy management "
             "remains the critical path per the Deployment Plan (AM-DOC-004)."),
        ],
    )
    written.append(path)

    # 9. Project Timeline (XLSX)
    path = os.path.join(project_dir, "Project_Timeline.xlsx")
    write_xlsx(
        path,
        [
            SheetSpec(
                title="Timeline",
                intro=["Aurora Mobility — Project Timeline (AM-DOC-009)", "Version 1.0  |  2026-05-08"],
                header=["Milestone", "Release", "Start", "End", "Status"],
                rows=[
                    ["Energy management core live", "Foundation", "2026-05-15", "2026-06-30", "Planned"],
                    ["Zone North public charging", "Foundation", "2026-06-01", "2026-07-15", "Planned"],
                    ["Depot fleet charging (North)", "Foundation", "2026-06-20", "2026-07-30", "Planned"],
                    ["Zone Central expansion", "Expansion", "2026-08-01", "2026-09-30", "Planned"],
                    ["Advanced load balancing", "Optimisation", "2026-10-01", "2026-11-30", "Planned"],
                ],
            )
        ],
    )
    written.append(path)

    return written
