"""Horizon Logistics project corpus — warehouse and logistics optimization.

Domain terminology: warehouse operations, inventory, routing, delivery planning,
fleet scheduling, logistics, optimization, distribution.
"""

from __future__ import annotations

import os

from .common import SheetSpec, write_docx, write_pdf, write_xlsx

PROJECT = "Horizon-Logistics"

# Reusable warehouse-requirements prose (consumed by the Updated download).
WH_PURPOSE = (
    "This specification defines requirements for the Horizon Logistics warehouse "
    "operations and distribution programme, covering inventory management, picking "
    "and putaway, delivery routing, and fleet scheduling. Requirements are realised "
    "by the Logistics Architecture (HL-DOC-003)."
)
WH_ROUTING = (
    "Delivery routing shall generate daily route plans that minimise distance and "
    "respect vehicle capacity and delivery windows. Route plans shall be recomputed "
    "when orders change before dispatch (REQ-HL-011)."
)


def generate(root: str) -> list[str]:
    project_dir = os.path.join(root, PROJECT)
    written: list[str] = []

    path = os.path.join(project_dir, "Project_Overview.pdf")
    write_pdf(
        path,
        [
            ("title", "Horizon Logistics — Project Overview"),
            ("para", "Document ID: HL-DOC-001  |  Version: 1.0  |  Date: 2026-02-11  |  Owner: Aisha Rahman (Operations Director)"),
            ("heading", "Executive Summary"),
            ("para",
             "Horizon Logistics is a programme to modernise warehouse operations and distribution across "
             "three regional distribution centres. It delivers inventory planning, optimised delivery "
             "routing, and coordinated fleet scheduling under one logistics platform to reduce cost per "
             "delivery and improve on-time performance."),
            ("heading", "Objectives"),
            ("bullets", [
                "Increase warehouse picking throughput by 20% through layout and slotting changes.",
                "Reduce delivery distance per route through route optimisation.",
                "Improve inventory accuracy to 99% through cycle counting.",
                "Coordinate fleet scheduling across three distribution centres.",
            ]),
            ("heading", "Scope"),
            ("para",
             "In scope: warehouse operations, inventory planning, route optimisation, and fleet "
             "scheduling. Out of scope: carrier contract negotiation, handled by procurement."),
            ("heading", "Stakeholders"),
            ("table", (
                ["Name", "Role", "Interest"],
                [
                    ["Aisha Rahman", "Operations Director", "Distribution performance"],
                    ["Karl Svensson", "Warehouse Lead", "Picking and inventory"],
                    ["Nadia Costa", "Routing Analyst", "Delivery optimisation"],
                    ["Peter Lindqvist", "Fleet Coordinator", "Vehicle scheduling"],
                ],
            )),
            ("heading", "Related Documents"),
            ("bullets", [
                "Warehouse Requirements (HL-DOC-002)",
                "Logistics Architecture (HL-DOC-003)",
                "Route Optimization Proposal (HL-DOC-004)",
                "Inventory Planning (HL-DOC-005)",
            ]),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Warehouse_Requirements.pdf")
    write_pdf(
        path,
        [
            ("title", "Horizon Logistics — Warehouse Requirements"),
            ("para", "Document ID: HL-DOC-002  |  Version: 1.2  |  Date: 2026-02-25  |  Author: Karl Svensson"),
            ("heading", "Purpose"),
            ("para", WH_PURPOSE),
            ("heading", "Functional Requirements"),
            ("table", (
                ["ID", "Requirement", "Priority"],
                [
                    ["REQ-HL-001", "The system shall track inventory by location and lot.", "Must"],
                    ["REQ-HL-004", "The system shall direct putaway using slotting rules.", "Must"],
                    ["REQ-HL-008", "The system shall generate optimised picking waves.", "Must"],
                    ["REQ-HL-011", "The system shall recompute delivery routes before dispatch.", "Must"],
                    ["REQ-HL-015", "The system shall schedule fleet vehicles across distribution centres.", "Should"],
                ],
            )),
            ("heading", "Routing Requirements"),
            ("para", WH_ROUTING),
            ("heading", "Non-Functional Requirements"),
            ("bullets", [
                "REQ-HL-030: Inventory accuracy shall reach 99% via cycle counting.",
                "REQ-HL-032: Route plans shall be produced within the pre-dispatch window.",
                "REQ-HL-034: Warehouse operations shall continue during network outages using local mode.",
            ]),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Logistics_Architecture.pdf")
    write_pdf(
        path,
        [
            ("title", "Horizon Logistics — Logistics Architecture"),
            ("para", "Document ID: HL-DOC-003  |  Version: 1.1  |  Date: 2026-03-10  |  Author: Nadia Costa"),
            ("heading", "Overview"),
            ("para",
             "The logistics architecture realises the Warehouse Requirements (HL-DOC-002) through four "
             "services: Inventory, Warehouse Execution, Route Optimisation, and Fleet Scheduling, "
             "integrated over a distribution event bus."),
            ("heading", "Services"),
            ("table", (
                ["Service", "Responsibility", "Related Requirement"],
                [
                    ["Inventory", "Track stock by location and lot", "REQ-HL-001"],
                    ["Warehouse Execution", "Putaway and picking waves", "REQ-HL-004, REQ-HL-008"],
                    ["Route Optimisation", "Daily delivery route plans", "REQ-HL-011"],
                    ["Fleet Scheduling", "Vehicle assignment", "REQ-HL-015"],
                ],
            )),
            ("heading", "Route Optimisation"),
            ("para",
             "The Route Optimisation service consumes confirmed orders and vehicle capacity to produce "
             "distance-minimising routes, detailed further in the Route Optimization Proposal (HL-DOC-004)."),
            ("heading", "Cross-References"),
            ("para", "Tooling is assessed in the Vendor Proposal (HL-DOC-007)."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Route_Optimization_Proposal.docx")
    write_docx(
        path,
        [
            ("title", "Horizon Logistics — Route Optimization Proposal"),
            ("para", "Document ID: HL-DOC-004  |  Version: 1.0  |  Date: 2026-03-17  |  Author: Nadia Costa"),
            ("heading", "Purpose"),
            ("para",
             "This proposal details the route optimisation approach realising REQ-HL-011 within the "
             "Logistics Architecture (HL-DOC-003)."),
            ("heading", "Approach"),
            ("bullets", [
                "Cluster deliveries by service area and time window.",
                "Solve capacitated routing per cluster with distance minimisation.",
                "Recompute routes on order changes before dispatch.",
            ]),
            ("heading", "Expected Benefits"),
            ("table", (
                ["Metric", "Baseline", "Target"],
                [
                    ["Distance per route", "142 km", "118 km"],
                    ["On-time delivery", "91%", "96%"],
                    ["Vehicles per day", "38", "34"],
                ],
            )),
            ("heading", "Dependencies"),
            ("para",
             "Requires accurate inventory availability from the Inventory service and fleet capacity "
             "from Fleet Scheduling; costs feed the Budget (HL-DOC-008)."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Inventory_Planning.xlsx")
    write_xlsx(
        path,
        [
            SheetSpec(
                title="Inventory Plan",
                intro=["Horizon Logistics — Inventory Planning (HL-DOC-005)", "Version 1.0  |  2026-03-24"],
                header=["SKU", "DC", "Avg Daily Demand", "Safety Stock", "Reorder Point"],
                rows=[
                    ["SKU-1001", "DC North", 320, 640, 1280],
                    ["SKU-1002", "DC North", 145, 290, 580],
                    ["SKU-2003", "DC Central", 512, 1024, 2048],
                    ["SKU-3007", "DC South", 88, 176, 352],
                    ["SKU-3011", "DC South", 205, 410, 820],
                ],
            ),
            SheetSpec(
                title="Cycle Counts",
                header=["DC", "Zone", "Accuracy", "Target"],
                rows=[
                    ["DC North", "Fast movers", "98.4%", "99%"],
                    ["DC Central", "Bulk", "97.9%", "99%"],
                    ["DC South", "Returns", "96.5%", "99%"],
                ],
            ),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Operations_Report.pdf")
    write_pdf(
        path,
        [
            ("title", "Horizon Logistics — Operations Report"),
            ("para", "Document ID: HL-DOC-006  |  Version: Q1 2026  |  Date: 2026-04-05  |  Author: Aisha Rahman"),
            ("heading", "Summary"),
            ("para",
             "This quarterly operations report reviews warehouse throughput, inventory accuracy, and "
             "delivery performance against the objectives in the Project Overview (HL-DOC-001)."),
            ("heading", "Key Metrics"),
            ("table", (
                ["Metric", "Q4 2025", "Q1 2026", "Target"],
                [
                    ["Picking throughput (lines/hr)", "148", "162", "178"],
                    ["Inventory accuracy", "97.1%", "98.0%", "99%"],
                    ["On-time delivery", "90%", "92%", "96%"],
                    ["Distance per route", "146 km", "138 km", "118 km"],
                ],
            )),
            ("heading", "Observations"),
            ("para",
             "Route optimisation pilots in DC North reduced distance per route; broader rollout follows "
             "the Route Optimization Proposal (HL-DOC-004). Inventory accuracy improves with cycle "
             "counting per the Inventory Planning workbook (HL-DOC-005)."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Vendor_Proposal.docx")
    write_docx(
        path,
        [
            ("title", "Horizon Logistics — Vendor Proposal"),
            ("para", "Document ID: HL-DOC-007  |  Version: 1.0  |  Date: 2026-04-09  |  Author: Peter Lindqvist"),
            ("heading", "Purpose"),
            ("para",
             "This proposal evaluates warehouse and routing platform vendors for the services in the "
             "Logistics Architecture (HL-DOC-003)."),
            ("heading", "Candidate Vendors"),
            ("table", (
                ["Vendor", "Component", "Score (/100)", "Notes"],
                [
                    ["StowLogic", "Warehouse execution", "87", "Strong slotting engine"],
                    ["RouteWise", "Route optimisation", "86", "Capacitated routing"],
                    ["StockSense", "Inventory management", "82", "Good cycle counting"],
                    ["FleetGrid", "Fleet scheduling", "80", "Multi-DC support"],
                ],
            )),
            ("heading", "Recommendation"),
            ("para",
             "Adopt StowLogic for warehouse execution and RouteWise for route optimisation; costs feed "
             "the Budget (HL-DOC-008)."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Budget.xlsx")
    write_xlsx(
        path,
        [
            SheetSpec(
                title="Costs",
                intro=["Horizon Logistics — Budget (HL-DOC-008)", "Version 1.0  |  2026-04-12  |  Currency: EUR (fictional)"],
                header=["Item", "Vendor", "Basis", "Annual Cost"],
                rows=[
                    ["Warehouse execution", "StowLogic", "Per DC", 132000],
                    ["Route optimisation", "RouteWise", "Managed service", 78000],
                    ["Inventory management", "StockSense", "Per DC", 66000],
                    ["Fleet scheduling", "FleetGrid", "Per vehicle", 54000],
                ],
            )
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Meeting_Notes.docx")
    write_docx(
        path,
        [
            ("title", "Horizon Logistics — Meeting Notes"),
            ("para", "Document ID: HL-DOC-009  |  Version: rolling  |  Last updated: 2026-04-14"),
            ("heading", "2026-03-11 — Architecture Review"),
            ("para",
             "Approved the Logistics Architecture (HL-DOC-003) with four services over a distribution "
             "event bus. Action: Nadia to finalise the Route Optimization Proposal."),
            ("heading", "2026-04-06 — Operations Review"),
            ("para",
             "Reviewed the Q1 Operations Report (HL-DOC-006). Route optimisation pilot in DC North "
             "reduced distance per route; agreed to expand to DC Central next quarter."),
            ("heading", "2026-04-13 — Vendor Decision"),
            ("para",
             "Accepted the Vendor Proposal (HL-DOC-007) recommendation for StowLogic and RouteWise. "
             "Budget to be updated in HL-DOC-008."),
        ],
    )
    written.append(path)

    return written
