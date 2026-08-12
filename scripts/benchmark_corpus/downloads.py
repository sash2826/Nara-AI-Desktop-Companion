"""Download-recommendation corpus — simulated newly downloaded files.

Twenty-seven files across six categories: obvious, semantic, ambiguous,
wrong-project, unrelated, and duplicate/updated versions. Duplicate files reuse
prose exported by the project modules so a version detector can match them to the
existing project documents.
"""

from __future__ import annotations

import os

from .common import SheetSpec, write_docx, write_pdf, write_xlsx
from . import project_aurora as aurora
from . import project_atlas as atlas
from . import project_horizon as horizon
from . import project_northstar as northstar
from . import project_polaris as polaris


def generate(root: str) -> list[str]:
    written: list[str] = []

    def pdf(name, blocks):
        p = os.path.join(root, name)
        write_pdf(p, blocks)
        written.append(p)

    def docx(name, blocks):
        p = os.path.join(root, name)
        write_docx(p, blocks)
        written.append(p)

    def xlsx(name, sheets):
        p = os.path.join(root, name)
        write_xlsx(p, sheets)
        written.append(p)

    # --- Category 1: Obvious matches ----------------------------------------
    pdf(
        "Aurora_Mobility_Charging_Deployment_Proposal.pdf",
        [
            ("title", "Aurora Mobility — Charging Deployment Proposal"),
            ("para", "Prepared for: Meridian Transit Cooperative  |  Date: 2026-05-20"),
            ("heading", "Overview"),
            ("para",
             "This proposal outlines the deployment of additional Aurora Mobility charging stations "
             "across two new service areas, extending the existing charging network. It covers station "
             "siting, fleet charging schedules, and energy management integration."),
            ("heading", "Deployment Scope"),
            ("bullets", [
                "Install 35 public charging stations and 12 depot chargers.",
                "Integrate with the existing energy management load-balancing core.",
                "Commission fleet charging schedules for depot vehicles.",
            ]),
            ("heading", "Alignment"),
            ("para",
             "The proposal follows the Aurora Mobility Charging Network Deployment Plan and reuses the "
             "OCPP 2.0.1 charging gateway design from the Technical Architecture."),
        ],
    )
    docx(
        "Northstar_Dashboard_Requirements_Update.docx",
        [
            ("title", "Northstar Analytics — Dashboard Requirements Update"),
            ("para", "Date: 2026-05-18  |  Author: Hannah Boateng"),
            ("heading", "Purpose"),
            ("para",
             "This update revises dashboard requirements for the Northstar Analytics platform, adding "
             "two certified dashboards and refining data-quality indicators shown to business users."),
            ("heading", "New Requirements"),
            ("bullets", [
                "Add a Supply Chain dashboard sourced from conformed warehouse marts.",
                "Show freshness and completeness indicators on every certified dashboard.",
                "Support export of dashboard data for offline reporting.",
            ]),
            ("heading", "Alignment"),
            ("para",
             "This update extends the Northstar Analytics Dashboard Specification and depends on the "
             "data-quality service in the Analytics Architecture."),
        ],
    )
    pdf(
        "Horizon_Warehouse_Optimization_Proposal.pdf",
        [
            ("title", "Horizon Logistics — Warehouse Optimization Proposal"),
            ("para", "Date: 2026-05-14  |  Author: Karl Svensson"),
            ("heading", "Overview"),
            ("para",
             "This proposal recommends warehouse slotting and picking-wave optimisation across the "
             "three Horizon Logistics distribution centres to increase picking throughput and reduce "
             "travel distance within the warehouse."),
            ("heading", "Recommendations"),
            ("bullets", [
                "Re-slot fast movers closer to dispatch to cut picker travel.",
                "Introduce dynamic picking waves aligned to route dispatch times.",
                "Extend cycle counting to sustain 99% inventory accuracy.",
            ]),
            ("heading", "Alignment"),
            ("para",
             "The proposal builds on the Horizon Logistics Warehouse Requirements and the Route "
             "Optimization Proposal."),
        ],
    )
    pdf(
        "Atlas_Meeting_Room_Technology_Proposal.pdf",
        [
            ("title", "Atlas Workplace — Meeting Room Technology Proposal"),
            ("para", "Date: 2026-05-12  |  Author: Diego Herrera"),
            ("heading", "Overview"),
            ("para",
             "This proposal specifies meeting room technology upgrades for the Atlas Workplace "
             "programme, including room booking panels, video conferencing, and floor availability "
             "displays across the redesigned office."),
            ("heading", "Scope"),
            ("bullets", [
                "Deploy booking panels to all 28 meeting rooms.",
                "Install video bars in standard and boardroom tiers.",
                "Show real-time room availability on floor displays.",
            ]),
            ("heading", "Alignment"),
            ("para", "This proposal extends the Atlas Workplace Meeting Room Strategy."),
        ],
    )
    pdf(
        "Polaris_Carbon_Reporting_Guidelines.pdf",
        [
            ("title", "Polaris Sustainability — Carbon Reporting Guidelines"),
            ("para", "Date: 2026-05-09  |  Author: Elena Marković"),
            ("heading", "Purpose"),
            ("para",
             "These guidelines describe how teams should prepare carbon emissions data for the Polaris "
             "Sustainability reporting programme, covering Scope 1, 2, and 3 activity data and emission "
             "factors."),
            ("heading", "Guidelines"),
            ("bullets", [
                "Submit activity data with units and reporting period.",
                "Use the versioned emission factor register for calculations.",
                "Provide measured supplier emissions where available.",
            ]),
            ("heading", "Alignment"),
            ("para", "These guidelines support the Polaris Sustainability Carbon Reporting Framework."),
        ],
    )

    # --- Category 2: Semantic matches (no project name in filename) ---------
    pdf(
        "Smart_Energy_Load_Management_Study.pdf",
        [
            ("title", "Smart Energy Load Management Study"),
            ("para", "Independent study  |  Date: 2026-05-06"),
            ("heading", "Introduction"),
            ("para",
             "This study examines load balancing for high-power vehicle charging sites. It analyses how "
             "charging station utilisation, energy demand, and charging schedules interact when many "
             "vehicles charge simultaneously at a shared grid connection."),
            ("heading", "Findings"),
            ("bullets", [
                "Coordinated charging schedules cut peak energy demand at depot sites.",
                "Fleet charging benefits from shifting sessions into off-peak windows.",
                "Dynamic load balancing across charging stations avoids grid overload.",
            ]),
            ("heading", "Recommendation"),
            ("para",
             "Operators of charging networks should adopt an energy management core that curtails "
             "non-priority charging sessions before fleet-critical charging is affected."),
        ],
    )
    docx(
        "Data_Quality_Monitoring_Framework.docx",
        [
            ("title", "Data Quality Monitoring Framework"),
            ("para", "Reference framework  |  Date: 2026-05-04"),
            ("heading", "Purpose"),
            ("para",
             "This framework describes how to monitor data quality across ingestion pipelines feeding a "
             "central data warehouse, and how to surface quality indicators on reporting dashboards so "
             "business intelligence stays trustworthy."),
            ("heading", "Quality Dimensions"),
            ("bullets", [
                "Completeness and validity checked per pipeline load.",
                "Freshness measured against the overnight batch window.",
                "Dashboard accuracy traced back to conformed warehouse tables.",
            ]),
            ("heading", "Reporting"),
            ("para",
             "Certified dashboards should display data-quality indicators so analysts can trust "
             "reported metrics."),
        ],
    )
    xlsx(
        "Warehouse_Demand_Forecasting_Model.xlsx",
        [
            SheetSpec(
                title="Demand Forecast",
                intro=["Warehouse Demand Forecasting Model", "Date: 2026-05-02"],
                header=["SKU", "DC", "Forecast Daily Demand", "Safety Stock", "Delivery Lead (days)"],
                rows=[
                    ["SKU-1001", "DC North", 331, 662, 2],
                    ["SKU-2003", "DC Central", 528, 1056, 3],
                    ["SKU-3007", "DC South", 92, 184, 2],
                    ["SKU-3011", "DC South", 214, 428, 3],
                ],
            ),
            SheetSpec(
                title="Routing Impact",
                header=["Route", "Deliveries", "Avg Distance (km)", "Vehicles"],
                rows=[
                    ["North-1", 42, 116, 3],
                    ["Central-2", 55, 129, 4],
                    ["South-3", 31, 108, 2],
                ],
            ),
        ],
    )
    pdf(
        "Workspace_Access_Experience_Study.pdf",
        [
            ("title", "Workspace Access & Experience Study"),
            ("para", "Independent study  |  Date: 2026-04-30"),
            ("heading", "Introduction"),
            ("para",
             "This study evaluates how office access, meeting room availability, and workplace "
             "technology affect employee experience in an activity-based office. It considers building "
             "entry, floor access, and room booking convenience."),
            ("heading", "Findings"),
            ("bullets", [
                "Employees rate meeting room availability as the biggest experience factor.",
                "Streamlined building access improves perceived convenience.",
                "Room booking that grants temporary access reduces friction.",
            ]),
            ("heading", "Recommendation"),
            ("para",
             "Workplace programmes should integrate room booking with access control to improve the "
             "employee experience in the redesigned office."),
        ],
    )
    docx(
        "Supplier_Emissions_Data_Framework.docx",
        [
            ("title", "Supplier Emissions Data Framework"),
            ("para", "Reference framework  |  Date: 2026-04-28"),
            ("heading", "Purpose"),
            ("para",
             "This framework standardises how supplier emissions are collected and consolidated for "
             "environmental reporting. It covers Scope 3 carbon accounting, data quality of supplier "
             "figures, and sustainability metrics for disclosure."),
            ("heading", "Data Collection"),
            ("bullets", [
                "Collect measured supplier emissions where available; estimate otherwise.",
                "Apply versioned emission factors to compute CO2-equivalent.",
                "Consolidate supplier emissions into a central environmental data model.",
            ]),
            ("heading", "Reporting"),
            ("para",
             "Consolidated supplier emissions feed quarterly and annual sustainability reporting."),
        ],
    )

    # --- Category 3: Ambiguous matches --------------------------------------
    pdf(
        "Enterprise_Data_Governance_Guide.pdf",
        [
            ("title", "Enterprise Data Governance Guide"),
            ("para", "General guide  |  Date: 2026-04-25"),
            ("heading", "Overview"),
            ("para",
             "This guide describes data governance practices: ownership, stewardship, data quality "
             "standards, and audit trails. These practices apply to analytics data warehouses and to "
             "environmental reporting data alike, where governed, auditable data is essential."),
            ("heading", "Governance Practices"),
            ("bullets", [
                "Assign owners and stewards to every data domain.",
                "Define data quality thresholds and monitor them.",
                "Maintain auditable trails for reported figures.",
            ]),
            ("heading", "Applicability"),
            ("para",
             "The practices apply to business-intelligence reporting and to sustainability disclosure "
             "data, both of which depend on strong governance."),
        ],
    )
    xlsx(
        "Energy_Consumption_Analytics_Report.xlsx",
        [
            SheetSpec(
                title="Energy Consumption",
                intro=["Energy Consumption Analytics Report", "Date: 2026-04-22"],
                header=["Site", "Period", "Electricity (MWh)", "CO2e (t)", "Notes"],
                rows=[
                    ["Depot North", "Q1 2026", 412, 96, "Includes vehicle charging load"],
                    ["Office A", "Q1 2026", 188, 44, "Building consumption"],
                    ["DC Central", "Q1 2026", 265, 62, "Warehouse operations"],
                ],
            ),
            SheetSpec(
                title="Analysis",
                header=["Dimension", "Observation"],
                rows=[
                    ["Charging load", "Vehicle charging drives depot peaks"],
                    ["Emissions", "Electricity converts to CO2e for reporting"],
                    ["Analytics", "Consumption trends feed dashboards"],
                ],
            ),
        ],
    )
    pdf(
        "Operations_Performance_Review.pdf",
        [
            ("title", "Operations Performance Review"),
            ("para", "Quarterly review  |  Date: 2026-04-20"),
            ("heading", "Summary"),
            ("para",
             "This review analyses operational performance metrics. It reports throughput, backlog, and "
             "on-time performance, and discusses how these are tracked on analytics dashboards and used "
             "to manage warehouse and distribution operations."),
            ("heading", "Metrics"),
            ("table", (
                ["Metric", "Value", "Trend"],
                [
                    ["Throughput", "162 lines/hr", "Up"],
                    ["On-time delivery", "92%", "Up"],
                    ["Backlog", "1.4 days", "Flat"],
                ],
            )),
            ("heading", "Discussion"),
            ("para",
             "The metrics are relevant both to logistics operations and to the analytics reporting that "
             "monitors operational performance."),
        ],
    )
    pdf(
        "Access_Security_Architecture.pdf",
        [
            ("title", "Access & Security Architecture"),
            ("para", "Reference architecture  |  Date: 2026-04-18"),
            ("heading", "Overview"),
            ("para",
             "This architecture describes role-based access control, credential management, and event "
             "logging. It applies to physical building and meeting room access as well as to securing "
             "networked charging endpoints and their control APIs."),
            ("heading", "Controls"),
            ("bullets", [
                "Role-based credentials for entry and resource access.",
                "Authenticated channels for control commands.",
                "Access and command event logging with retention.",
            ]),
            ("heading", "Applicability"),
            ("para",
             "The approach suits workplace access control and the security of charging network control "
             "endpoints."),
        ],
    )
    docx(
        "Vendor_Performance_Framework.docx",
        [
            ("title", "Vendor Performance Framework"),
            ("para", "General framework  |  Date: 2026-04-15"),
            ("heading", "Purpose"),
            ("para",
             "This framework defines how to evaluate and score vendors across scope, cost, quality, and "
             "support. It is generic and can be applied to any of the programmes that run vendor "
             "evaluations for platform tooling, hardware, or services."),
            ("heading", "Scoring Dimensions"),
            ("bullets", [
                "Capability fit against requirements.",
                "Total cost of ownership.",
                "Support and delivery track record.",
            ]),
            ("heading", "Applicability"),
            ("para",
             "The framework is not specific to any one programme and could support several vendor "
             "evaluations."),
        ],
    )

    # --- Category 4: Wrong-project matches (misleading filename) ------------
    pdf(
        "Aurora_Analytics_Dashboard.pdf",
        [
            ("title", "Analytics Dashboard Specification"),
            ("para", "Date: 2026-04-12  |  Author: Ibrahim Osei"),
            ("heading", "Purpose"),
            ("para",
             "Despite the codename in the filename, this document specifies dashboards for the business "
             "analytics data platform. It defines certified dashboards, data warehouse marts, and "
             "data-quality indicators for business intelligence users."),
            ("heading", "Dashboards"),
            ("bullets", [
                "Revenue and operations dashboards from conformed marts.",
                "Data-quality indicators for completeness and freshness.",
                "Self-service reporting over the data warehouse.",
            ]),
            ("heading", "Note"),
            ("para",
             "This is an analytics data-platform document; it concerns dashboards, pipelines, and the "
             "data warehouse, not vehicle charging."),
        ],
    )
    pdf(
        "Horizon_Employee_Workplace_Report.pdf",
        [
            ("title", "Employee Workplace Experience Report"),
            ("para", "Date: 2026-04-10  |  Author: Grace Fields"),
            ("heading", "Summary"),
            ("para",
             "Although the filename carries a logistics codename, this report is about the office "
             "workplace. It covers meeting room availability, office space usage, building access, and "
             "employee experience in the activity-based office."),
            ("heading", "Findings"),
            ("bullets", [
                "Meeting room availability drives workplace satisfaction.",
                "Activity-based zones improve focus and collaboration.",
                "Streamlined access control improves convenience.",
            ]),
            ("heading", "Note"),
            ("para",
             "This report concerns office modernisation, meeting rooms, and workplace access — not "
             "warehouses or delivery routing."),
        ],
    )
    pdf(
        "Polaris_Logistics_Data_Report.pdf",
        [
            ("title", "Logistics & Distribution Data Report"),
            ("para", "Date: 2026-04-08  |  Author: Nadia Costa"),
            ("heading", "Summary"),
            ("para",
             "The filename mentions a sustainability codename, but this report is about warehouse and "
             "distribution operations. It analyses inventory levels, delivery routing, and fleet "
             "scheduling across distribution centres."),
            ("heading", "Contents"),
            ("bullets", [
                "Inventory accuracy and cycle counting by distribution centre.",
                "Delivery route distance and on-time performance.",
                "Fleet vehicle scheduling and utilisation.",
            ]),
            ("heading", "Note"),
            ("para",
             "This is a logistics operations document about warehousing and routing, not carbon "
             "emissions or environmental reporting."),
        ],
    )
    pdf(
        "Atlas_Sustainability_Review.pdf",
        [
            ("title", "Sustainability & Emissions Review"),
            ("para", "Date: 2026-04-06  |  Author: Elena Marković"),
            ("heading", "Summary"),
            ("para",
             "Despite the workplace codename in the filename, this review is about environmental "
             "reporting. It covers carbon emissions accounting, supplier emissions, energy consumption, "
             "and sustainability metrics for disclosure."),
            ("heading", "Contents"),
            ("bullets", [
                "Scope 1, 2, and 3 carbon accounting summary.",
                "Supplier emissions data quality.",
                "Energy consumption and emission factor register.",
            ]),
            ("heading", "Note"),
            ("para",
             "This is a sustainability document about carbon reporting — not office space or meeting "
             "rooms."),
        ],
    )

    # --- Category 5: Completely unrelated files -----------------------------
    pdf(
        "Personal_Travel_Insurance.pdf",
        [
            ("title", "Personal Travel Insurance — Policy Summary"),
            ("para", "Policyholder: (sample)  |  Date: 2026-03-30"),
            ("heading", "Coverage"),
            ("para",
             "This personal travel insurance policy summary describes cover for trip cancellation, "
             "medical expenses abroad, lost baggage, and travel delay for a family holiday."),
            ("heading", "Key Benefits"),
            ("bullets", [
                "Medical expenses cover up to a stated limit.",
                "Baggage and personal belongings cover.",
                "Trip cancellation and curtailment cover.",
            ]),
            ("heading", "Notes"),
            ("para", "This is a personal document unrelated to any work project."),
        ],
    )
    xlsx(
        "Home_Garden_Improvement_Budget.xlsx",
        [
            SheetSpec(
                title="Garden Budget",
                intro=["Home & Garden Improvement Budget", "Personal  |  Date: 2026-03-28"],
                header=["Item", "Category", "Estimated Cost", "Status"],
                rows=[
                    ["Raised flower beds", "Garden", 320, "Planned"],
                    ["Patio repaving", "Outdoor", 1450, "Quote received"],
                    ["Shed repaint", "Maintenance", 90, "Done"],
                    ["New lawnmower", "Tools", 280, "Planned"],
                ],
            )
        ],
    )
    pdf(
        "Photography_Equipment_Guide.pdf",
        [
            ("title", "Photography Equipment Guide"),
            ("para", "Hobby guide  |  Date: 2026-03-26"),
            ("heading", "Introduction"),
            ("para",
             "This guide introduces camera equipment for enthusiast photographers, covering camera "
             "bodies, lenses, tripods, and accessories for landscape and portrait photography."),
            ("heading", "Recommendations"),
            ("bullets", [
                "Choose a lens based on subject distance and light.",
                "Use a tripod for low-light landscape shots.",
                "Carry spare batteries and memory cards.",
            ]),
            ("heading", "Notes"),
            ("para", "This is a personal hobby document unrelated to any work project."),
        ],
    )

    # --- Category 6: Duplicate / updated versions ---------------------------
    # 6a. Aurora Technical Architecture v2 (updates AM-DOC-003)
    pdf(
        "Aurora_Technical_Architecture_v2.pdf",
        [
            ("title", "Aurora Mobility — Technical Architecture"),
            ("para", "Document ID: AM-DOC-003  |  Version: 2.0  |  Date: 2026-05-22  |  Author: Tomas Ek"),
            ("heading", "Overview"),
            ("para", aurora.ARCH_INTRO),
            ("heading", "Layered Architecture"),
            ("para", aurora.ARCH_LAYERS),
            ("heading", "Charging Gateway"),
            ("para", aurora.ARCH_GATEWAY),
            ("heading", "Authentication (New in v2)"),
            ("para",
             "Version 2.0 adds a dedicated authentication section: charging stations, gateways, and "
             "energy management APIs authenticate through a central identity service issuing short-lived "
             "mutual-TLS certificates with automated rotation, closing the finding raised in the "
             "Security Assessment (AM-DOC-005)."),
            ("heading", "Updated Architecture Diagram Description"),
            ("para",
             "The updated diagram now shows the identity service between the Charging Edge and the "
             "Energy Management core, and adds a rate-limiting gateway in front of the public energy "
             "management APIs. Requirement REQ-AM-034 is revised to mandate automated certificate "
             "rotation, and REQ-AM-021 is revised to include per-zone utilisation export."),
            ("heading", "Energy Management Core"),
            ("para",
             "The Energy Management core evaluates active charging sessions against grid limits and "
             "tariff windows every 30 seconds, lowering non-priority session power before curtailing "
             "fleet-critical charging."),
        ],
    )
    # 6b. Northstar Data Platform Requirements RevB (updates NA-DOC-002)
    docx(
        "Data_Platform_Requirements_RevB.docx",
        [
            ("title", "Northstar Analytics — Data Platform Requirements"),
            ("para", "Document ID: NA-DOC-002  |  Version: Rev B  |  Date: 2026-05-19  |  Author: Ibrahim Osei"),
            ("heading", "Purpose"),
            ("para", northstar.REQ_PURPOSE),
            ("heading", "Functional Requirements"),
            ("table", (
                ["ID", "Requirement", "Priority"],
                [
                    ["REQ-NA-001", "The platform shall ingest data from 16 registered source systems.", "Must"],
                    ["REQ-NA-006", "Pipelines shall record row counts and data-quality outcomes per load.", "Must"],
                    ["REQ-NA-009", "The warehouse shall expose conformed reporting tables per domain.", "Must"],
                    ["REQ-NA-012", "Dashboards shall display certified data-quality indicators.", "Must"],
                    ["REQ-NA-015", "Governance shall assign an owner to every reporting domain.", "Must"],
                    ["REQ-NA-018", "The platform shall support near-real-time pipelines for two domains.", "Should"],
                ],
            )),
            ("heading", "Data Pipeline Requirements"),
            ("para", northstar.REQ_PIPELINE),
            ("heading", "Revision Notes (Rev B)"),
            ("para",
             "Rev B raises the source-system count from 14 to 16, promotes REQ-NA-012 from Should to "
             "Must, and adds REQ-NA-018 for near-real-time pipelines. All other requirements are "
             "unchanged from version 1.3."),
        ],
    )
    # 6c. Horizon Warehouse Requirements Updated (updates HL-DOC-002)
    pdf(
        "Warehouse_Requirements_Updated.pdf",
        [
            ("title", "Horizon Logistics — Warehouse Requirements"),
            ("para", "Document ID: HL-DOC-002  |  Version: 1.3 (Updated)  |  Date: 2026-05-16  |  Author: Karl Svensson"),
            ("heading", "Purpose"),
            ("para", horizon.WH_PURPOSE),
            ("heading", "Functional Requirements"),
            ("table", (
                ["ID", "Requirement", "Priority"],
                [
                    ["REQ-HL-001", "The system shall track inventory by location and lot.", "Must"],
                    ["REQ-HL-004", "The system shall direct putaway using slotting rules.", "Must"],
                    ["REQ-HL-008", "The system shall generate optimised picking waves.", "Must"],
                    ["REQ-HL-011", "The system shall recompute delivery routes before dispatch.", "Must"],
                    ["REQ-HL-015", "The system shall schedule fleet vehicles across distribution centres.", "Must"],
                    ["REQ-HL-018", "The system shall support returns processing at each distribution centre.", "Should"],
                ],
            )),
            ("heading", "Routing Requirements"),
            ("para", horizon.WH_ROUTING),
            ("heading", "Update Notes"),
            ("para",
             "This update promotes REQ-HL-015 (fleet scheduling) from Should to Must and adds REQ-HL-018 "
             "for returns processing. Inventory accuracy target remains 99%. All other requirements are "
             "unchanged from version 1.2."),
        ],
    )
    # 6d. Atlas Access Control Plan v2 (updates AW-DOC-004)
    pdf(
        "Access_Control_Plan_v2.pdf",
        [
            ("title", "Atlas Workplace — Access Control Plan"),
            ("para", "Document ID: AW-DOC-004  |  Version: 2.0  |  Date: 2026-05-13  |  Author: Sara Lindholm"),
            ("heading", "Purpose"),
            ("para", atlas.ACCESS_PURPOSE),
            ("heading", "Access Model"),
            ("para", atlas.ACCESS_MODEL),
            ("heading", "Access Groups"),
            ("table", (
                ["Group", "Scope", "Credential"],
                [
                    ["Employee", "Building + assigned floors", "Mobile or badge"],
                    ["Visitor", "Reception + booked room", "Temporary QR"],
                    ["Facilities", "All floors + support areas", "Badge"],
                    ["Contractor", "Specific floor + hours", "Time-boxed badge"],
                    ["Event Guest", "Ground floor event space", "Event QR"],
                ],
            )),
            ("heading", "Update Notes (v2)"),
            ("para",
             "Version 2.0 adds an Event Guest access group for ground-floor events and extends access "
             "log retention from 90 to 180 days, revising REQ-AW-034. The role-based model and room "
             "booking integration are unchanged from version 1.1."),
        ],
    )
    # 6e. Polaris Carbon Reporting Framework 2026 Update (updates PS-DOC-003)
    pdf(
        "Carbon_Reporting_Framework_2026_Update.pdf",
        [
            ("title", "Polaris Sustainability — Carbon Reporting Framework"),
            ("para", "Document ID: PS-DOC-003  |  Version: 2.0 (2026 Update)  |  Date: 2026-05-10  |  Author: Elena Marković"),
            ("heading", "Purpose"),
            ("para", polaris.CARBON_PURPOSE),
            ("heading", "Accounting Method"),
            ("para", polaris.CARBON_METHOD),
            ("heading", "Emission Scopes"),
            ("table", (
                ["Scope", "Source", "Example"],
                [
                    ["Scope 1", "Direct emissions", "On-site fuel combustion"],
                    ["Scope 2", "Purchased energy", "Electricity consumption"],
                    ["Scope 3", "Value chain", "Supplier emissions, logistics"],
                ],
            )),
            ("heading", "2026 Update Notes"),
            ("para",
             "The 2026 update adds a market-based Scope 2 method alongside the location-based method, "
             "introduces a quarterly supplier data-quality target of 70% measured emissions, and updates "
             "the emission factor register to the 2026 factor set. The reporting cadence is unchanged."),
        ],
    )

    return written
