"""Declarative identity data for the eight synthetic benchmark projects.

Each :class:`Project` carries enough structured data for the content builders in
:mod:`scripts.eac_benchmark.builders` to render elaborate, cross-referenced
documents in multiple formats. All names, vendors, and figures are fictional.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Project:
    key: str                       # folder name, e.g. "Aurora-Mobility"
    code: str                      # document-id prefix, e.g. "AM"
    display: str                   # human name, e.g. "Aurora Mobility"
    domain: str                    # one-line domain description
    sponsor: str                   # fictional sponsoring organisation
    summary: str                   # one-paragraph programme summary
    background: str                # background narrative paragraph
    director: tuple[str, str]      # (name, role)
    people: list[tuple[str, str]]  # [(name, role), ...]
    vendors: list[tuple[str, str]]
    objectives: list[str]
    scope_in: str
    scope_out: str
    requirements: list[tuple[str, str, str]]     # (id, text, priority)
    components: list[tuple[str, str]]            # (component, description)
    decisions: list[tuple[str, str, str]]        # (id, decision, rationale)
    risks: list[tuple[str, str, str, str, str]]  # (id, risk, likelihood, impact, mitigation)
    milestones: list[tuple[str, str, str]]       # (phase, date, deliverable)
    budget: list[tuple[str, str]]                # (line item, amount)
    vocab: list[str]                             # domain keywords for semantic tests
    arch_doc: tuple[str, str, str]               # (filename, title, kind: "technical"|"operational")
    meeting: dict = field(default_factory=dict)


AURORA = Project(
    key="Aurora-Mobility",
    code="AM",
    display="Aurora Mobility",
    domain="electric-vehicle charging infrastructure",
    sponsor="Meridian Transit Cooperative",
    summary=(
        "Aurora Mobility is a programme to design, deploy, and operate a metropolitan "
        "electric-vehicle (EV) charging network serving both public drivers and managed "
        "commercial fleets. It delivers charging stations, an energy-management platform, "
        "and fleet charging services under one operating model."
    ),
    background=(
        "Regional fleet operators face rising demand for reliable depot and on-route "
        "charging while grid connection capacity remains constrained. Aurora Mobility "
        "consolidates several fragmented charging pilots into a single managed network "
        "with predictable energy costs, centralised monitoring, and demand-aware load "
        "balancing. The programme is sponsored by the fictional Meridian Transit "
        "Cooperative and coordinated with three municipal distribution operators."
    ),
    director=("Priya Nandakumar", "Programme Director"),
    people=[
        ("Priya Nandakumar", "Programme Director"),
        ("Tomas Ek", "Energy Management Lead"),
        ("Rosa Marin", "Fleet Services Lead"),
        ("Devon Clarke", "Security Officer"),
        ("Helena Vogt", "Grid Interconnection Engineer"),
    ],
    vendors=[
        ("VoltGrid Systems", "OCPP charging station hardware and controllers"),
        ("EnerBalance AB", "load-balancing and tariff-optimisation software"),
        ("NordConnect Utilities", "grid interconnection and metering services"),
    ],
    objectives=[
        "Deploy 120 public and 40 depot charging stations across three service zones.",
        "Provide fleet charging scheduling that respects grid load limits and tariffs.",
        "Achieve 99.2% charging-station availability measured monthly.",
        "Shift at least 60% of depot charging into off-peak tariff windows.",
    ],
    scope_in=(
        "charging-station hardware selection, the charging-network control platform, "
        "fleet charging services, energy management, and grid interconnection."
    ),
    scope_out=(
        "vehicle procurement and on-vehicle telematics, which remain with individual "
        "fleet owners, and retail electricity billing to public drivers."
    ),
    requirements=[
        ("REQ-AM-001", "The system shall register and monitor each charging station in real time.", "Must"),
        ("REQ-AM-005", "The system shall support fleet charging reservations per depot.", "Must"),
        ("REQ-AM-009", "The system shall optimise charging schedules against time-of-use tariffs.", "Must"),
        ("REQ-AM-014", "The system shall continue local charging when connectivity is degraded.", "Must"),
        ("REQ-AM-018", "The system shall cap aggregate depot load below the grid connection limit.", "Must"),
        ("REQ-AM-022", "The system should provide utilisation and demand analytics per zone.", "Should"),
        ("REQ-AM-027", "The system should expose an open API for third-party fleet apps.", "Should"),
    ],
    components=[
        ("Charging Edge", "Station controllers and OCPP 2.0.1 gateways that buffer telemetry and enforce local load limits."),
        ("Energy Management Core", "Load-balancing and tariff-optimisation engine that allocates power across depots."),
        ("Fleet Services", "Reservations, session orchestration, and depot scheduling for managed fleets."),
        ("Analytics Layer", "Utilisation, availability, and demand reporting across all zones."),
        ("Grid Interface", "Metering reconciliation and interconnection with distribution operators."),
    ],
    decisions=[
        ("DEC-AM-01", "Adopt OCPP 2.0.1 as the station protocol baseline.", "Vendor-neutral interoperability and offline resilience."),
        ("DEC-AM-02", "Centralise load balancing in the Energy Management Core.", "Enforces grid limits consistently across depots."),
        ("DEC-AM-03", "Phase deployment by service zone.", "Limits grid-interconnection risk and spreads capital cost."),
    ],
    risks=[
        ("RSK-AM-01", "Grid connection upgrade delayed by distribution operator.", "High", "High", "Stage deployment by zone; pre-book interconnection studies."),
        ("RSK-AM-02", "Charging hardware supply lead times exceed plan.", "Medium", "High", "Dual-source controllers; hold buffer stock for Zone 1."),
        ("RSK-AM-03", "Fleet charging demand exceeds off-peak capacity.", "Medium", "Medium", "Dynamic load balancing and reservation caps."),
        ("RSK-AM-04", "Charging-network security incident.", "Low", "High", "Segmented OCPP network, signed firmware, SOC monitoring."),
        ("RSK-AM-05", "Tariff structure changes mid-programme.", "Medium", "Medium", "Configurable tariff engine; quarterly re-optimisation."),
    ],
    milestones=[
        ("Foundation", "2026-05-15", "Energy Management Core and Zone 1 (40 stations) live."),
        ("Expansion A", "2026-08-30", "Zone 2 public charging and first depot online."),
        ("Expansion B", "2026-11-15", "Zone 3 and remaining depot charging online."),
        ("Optimisation", "2027-02-28", "Advanced load balancing and demand analytics released."),
        ("Steady State", "2027-04-30", "99.2% availability sustained for one quarter."),
    ],
    budget=[
        ("Charging station hardware", "EUR 4,200,000"),
        ("Grid interconnection works", "EUR 1,850,000"),
        ("Control platform licensing", "EUR 640,000"),
        ("Software integration", "EUR 920,000"),
        ("Installation and civil works", "EUR 1,300,000"),
        ("Programme management", "EUR 480,000"),
        ("Contingency (10%)", "EUR 989,000"),
    ],
    vocab=[
        "EV charging", "charging station", "fleet charging", "depot charging",
        "energy management", "load balancing", "off-peak tariff", "OCPP",
        "grid connection", "charging schedule", "energy demand", "charging network",
    ],
    arch_doc=("Technical_Architecture.pdf", "Aurora Mobility — Technical Architecture", "technical"),
    meeting={
        "date": "2026-03-26",
        "attendees": ["Priya Nandakumar", "Tomas Ek", "Rosa Marin", "Devon Clarke"],
        "decisions": [
            "Confirmed OCPP 2.0.1 baseline (DEC-AM-01) after vendor demonstrations.",
            "Approved Zone 1 hardware order from VoltGrid Systems.",
            "Agreed depot load cap of 1.2 MW per site pending grid studies.",
        ],
        "actions": [
            ("Tomas Ek", "Finalise tariff-optimisation parameters with EnerBalance AB", "2026-04-10"),
            ("Helena Vogt", "Submit interconnection study requests for Zones 1-2", "2026-04-05"),
            ("Devon Clarke", "Complete charging-network threat model", "2026-04-18"),
        ],
    },
)

NORTHSTAR = Project(
    key="Northstar-Analytics",
    code="NS",
    display="Northstar Analytics",
    domain="business intelligence and data analytics",
    sponsor="Lakeside Retail Group",
    summary=(
        "Northstar Analytics builds an enterprise business-intelligence platform that "
        "consolidates sales, inventory, and customer data into governed dashboards and "
        "self-service analytics for the Lakeside Retail Group."
    ),
    background=(
        "Reporting today is scattered across spreadsheets and disconnected departmental "
        "tools, producing conflicting numbers and slow decisions. Northstar Analytics "
        "establishes a single governed data platform with a semantic model, curated "
        "dashboards, and self-service analytics so that business users trust one version "
        "of the truth."
    ),
    director=("Marcus Feld", "Analytics Programme Lead"),
    people=[
        ("Marcus Feld", "Analytics Programme Lead"),
        ("Aisha Rahman", "Data Platform Architect"),
        ("Lena Kowalski", "BI Reporting Lead"),
        ("Ibrahim Osei", "Data Governance Manager"),
        ("Grace Tan", "Analytics Engineer"),
    ],
    vendors=[
        ("Quanta Data Cloud", "cloud data warehouse and compute"),
        ("Prismview BI", "dashboarding and self-service analytics tooling"),
        ("Catalog9", "data catalogue and governance platform"),
    ],
    objectives=[
        "Deliver one governed semantic model covering sales, inventory, and customers.",
        "Publish 25 certified dashboards replacing manual spreadsheet reports.",
        "Reduce month-end reporting cycle time from 9 days to 2 days.",
        "Establish data-quality monitoring with owner-level accountability.",
    ],
    scope_in=(
        "the cloud data warehouse, ETL/ELT pipelines, the semantic model, certified "
        "dashboards, self-service analytics, and data-governance controls."
    ),
    scope_out=(
        "point-of-sale system replacement and operational transaction processing, which "
        "remain owned by the retail operations programme."
    ),
    requirements=[
        ("REQ-NS-002", "The platform shall ingest daily sales and inventory feeds from all stores.", "Must"),
        ("REQ-NS-006", "The platform shall provide a governed semantic model with certified metrics.", "Must"),
        ("REQ-NS-011", "The platform shall enforce row-level security by business unit.", "Must"),
        ("REQ-NS-015", "The platform shall monitor data quality and alert data owners.", "Must"),
        ("REQ-NS-019", "The platform should support self-service dataset creation for analysts.", "Should"),
        ("REQ-NS-024", "The platform should retain two years of history for trend analysis.", "Should"),
        ("REQ-NS-028", "The platform should expose curated datasets through a governed API.", "Should"),
    ],
    components=[
        ("Ingestion Layer", "Batch and streaming pipelines landing raw store data into the warehouse."),
        ("Warehouse & Modelling", "Curated and semantic layers exposing certified business metrics."),
        ("Governance Layer", "Data catalogue, lineage, ownership, and row-level security controls."),
        ("Dashboarding Layer", "Certified dashboards and self-service analytics workspaces."),
        ("Data Quality Service", "Rule-based monitoring, anomaly detection, and owner alerting."),
    ],
    decisions=[
        ("DEC-NS-01", "Adopt an ELT pattern on the cloud warehouse.", "Simplifies pipelines and centralises transformation logic."),
        ("DEC-NS-02", "Certify metrics through the semantic model only.", "Prevents conflicting metric definitions across dashboards."),
        ("DEC-NS-03", "Enforce row-level security at the model layer.", "Consistent access control regardless of client tool."),
    ],
    risks=[
        ("RSK-NS-01", "Source data quality worse than expected.", "High", "High", "Early profiling; data-quality gates before certification."),
        ("RSK-NS-02", "Conflicting metric definitions across departments.", "High", "Medium", "Single semantic model; metric governance board."),
        ("RSK-NS-03", "Self-service usage bypasses governance.", "Medium", "Medium", "Certified vs sandbox workspaces; usage auditing."),
        ("RSK-NS-04", "Warehouse cost overruns from heavy queries.", "Medium", "Medium", "Query monitoring, materialised aggregates, cost alerts."),
        ("RSK-NS-05", "Slow adoption by business users.", "Medium", "High", "Embedded analysts, training, and dashboard sunset plan."),
    ],
    milestones=[
        ("Foundation", "2026-05-20", "Warehouse, ingestion for pilot stores, and catalogue live."),
        ("Semantic Model", "2026-08-10", "Certified metrics for sales and inventory published."),
        ("Dashboards", "2026-10-30", "First 15 certified dashboards released to business units."),
        ("Self-Service", "2026-12-15", "Governed self-service analytics enabled for analysts."),
        ("Cutover", "2027-02-20", "Legacy spreadsheet reports retired."),
    ],
    budget=[
        ("Cloud warehouse and compute", "EUR 720,000"),
        ("BI tooling licensing", "EUR 410,000"),
        ("Data catalogue and governance", "EUR 260,000"),
        ("Data engineering services", "EUR 1,050,000"),
        ("Change management and training", "EUR 320,000"),
        ("Programme management", "EUR 380,000"),
        ("Contingency (10%)", "EUR 314,000"),
    ],
    vocab=[
        "business intelligence", "data warehouse", "semantic model", "dashboard",
        "self-service analytics", "data governance", "data quality", "ETL",
        "certified metric", "row-level security", "data catalogue", "reporting",
    ],
    arch_doc=("Data_Platform_Architecture.pdf", "Northstar Analytics — Data Platform Architecture", "technical"),
    meeting={
        "date": "2026-03-24",
        "attendees": ["Marcus Feld", "Aisha Rahman", "Lena Kowalski", "Ibrahim Osei"],
        "decisions": [
            "Confirmed ELT-on-warehouse pattern (DEC-NS-01).",
            "Agreed sales and inventory as the first certified subject areas.",
            "Approved Catalog9 for the data catalogue and lineage.",
        ],
        "actions": [
            ("Aisha Rahman", "Complete warehouse landing-zone design", "2026-04-08"),
            ("Ibrahim Osei", "Draft metric-certification governance process", "2026-04-12"),
            ("Grace Tan", "Profile pilot-store sales feeds for data quality", "2026-04-06"),
        ],
    },
)

HORIZON = Project(
    key="Horizon-Logistics",
    code="HL",
    display="Horizon Logistics",
    domain="warehouse and logistics optimization",
    sponsor="Continental Distribution Partners",
    summary=(
        "Horizon Logistics modernises warehouse operations and outbound logistics for a "
        "regional distribution network, introducing slotting optimisation, demand "
        "forecasting, and a warehouse control layer to raise throughput and on-time "
        "dispatch."
    ),
    background=(
        "The distribution network runs three warehouses with manual slotting, reactive "
        "replenishment, and limited visibility of outbound performance. Horizon Logistics "
        "introduces data-driven slotting, demand forecasting, and a warehouse control "
        "system so that picking travel, dock congestion, and late dispatches are reduced."
    ),
    director=("Elena Rossi", "Operations Programme Manager"),
    people=[
        ("Elena Rossi", "Operations Programme Manager"),
        ("Paul Nquyen", "Warehouse Systems Lead"),
        ("Sofia Berg", "Demand Planning Lead"),
        ("Ravi Menon", "Transport & Dispatch Lead"),
        ("Klara Novak", "Continuous Improvement Analyst"),
    ],
    vendors=[
        ("PalletPath WMS", "warehouse management and control system"),
        ("ForecastIQ", "demand-forecasting and replenishment analytics"),
        ("DockFlow", "yard and dock-scheduling platform"),
    ],
    objectives=[
        "Reduce average picking travel distance by 20% through slotting optimisation.",
        "Improve outbound on-time dispatch from 88% to 97%.",
        "Cut safety-stock holding by 12% using improved demand forecasting.",
        "Provide real-time visibility of dock and yard congestion.",
    ],
    scope_in=(
        "slotting optimisation, demand forecasting and replenishment, the warehouse "
        "control layer, and dock/yard scheduling across three warehouses."
    ),
    scope_out=(
        "long-haul carrier contracts and last-mile delivery, which are managed by the "
        "transport procurement team."
    ),
    requirements=[
        ("REQ-HL-003", "The system shall recommend slot assignments based on velocity and volume.", "Must"),
        ("REQ-HL-007", "The system shall forecast demand per SKU and location weekly.", "Must"),
        ("REQ-HL-012", "The system shall generate replenishment orders against safety-stock targets.", "Must"),
        ("REQ-HL-016", "The system shall schedule inbound and outbound dock appointments.", "Must"),
        ("REQ-HL-020", "The system should surface real-time yard congestion to supervisors.", "Should"),
        ("REQ-HL-025", "The system should measure picking travel distance per order.", "Should"),
        ("REQ-HL-029", "The system should integrate with the transport dispatch schedule.", "Should"),
    ],
    components=[
        ("Slotting Engine", "Velocity- and volume-based slot recommendation for each SKU."),
        ("Forecasting Service", "SKU-location demand forecasting and safety-stock calculation."),
        ("Replenishment Planner", "Order generation against forecast and safety-stock targets."),
        ("Warehouse Control Layer", "Task orchestration for picking, putaway, and replenishment."),
        ("Dock & Yard Scheduler", "Appointment scheduling and congestion visibility."),
    ],
    decisions=[
        ("DEC-HL-01", "Deploy slotting optimisation before automation investment.", "Captures throughput gains at lower cost and risk."),
        ("DEC-HL-02", "Forecast at SKU-location granularity.", "Enables location-specific safety stock and replenishment."),
        ("DEC-HL-03", "Pilot at Warehouse B first.", "Highest congestion; best measurable improvement."),
    ],
    risks=[
        ("RSK-HL-01", "Inaccurate master data undermines slotting.", "High", "High", "Master-data cleanse before go-live; ongoing audits."),
        ("RSK-HL-02", "Forecast accuracy insufficient for replenishment.", "Medium", "High", "Backtest models; human review of exceptions."),
        ("RSK-HL-03", "Dock scheduling not adopted by carriers.", "Medium", "Medium", "Carrier onboarding; booking incentives."),
        ("RSK-HL-04", "Change resistance from warehouse staff.", "Medium", "Medium", "Supervisor involvement; phased rollout; training."),
        ("RSK-HL-05", "Peak-season disruption during cutover.", "Medium", "High", "Freeze changes during peak; parallel run."),
    ],
    milestones=[
        ("Data Foundation", "2026-05-25", "Master-data cleanse and WMS control layer at Warehouse B."),
        ("Slotting Pilot", "2026-08-05", "Slotting optimisation live at Warehouse B."),
        ("Forecasting", "2026-10-20", "Demand forecasting and replenishment across all sites."),
        ("Dock Scheduling", "2026-12-10", "Dock and yard scheduling live at all warehouses."),
        ("Optimisation", "2027-02-25", "Throughput and on-time dispatch targets sustained."),
    ],
    budget=[
        ("WMS and control system", "EUR 980,000"),
        ("Forecasting analytics", "EUR 350,000"),
        ("Dock-scheduling platform", "EUR 240,000"),
        ("Integration and data cleanse", "EUR 620,000"),
        ("Training and change", "EUR 210,000"),
        ("Programme management", "EUR 300,000"),
        ("Contingency (10%)", "EUR 270,000"),
    ],
    vocab=[
        "warehouse", "slotting", "picking", "demand forecasting", "replenishment",
        "safety stock", "dock scheduling", "yard congestion", "throughput",
        "on-time dispatch", "logistics", "distribution",
    ],
    arch_doc=("Operations_Blueprint.pdf", "Horizon Logistics — Operations Blueprint", "operational"),
    meeting={
        "date": "2026-03-27",
        "attendees": ["Elena Rossi", "Paul Nquyen", "Sofia Berg", "Ravi Menon"],
        "decisions": [
            "Confirmed Warehouse B as the pilot site (DEC-HL-03).",
            "Agreed master-data cleanse as a go-live prerequisite.",
            "Selected ForecastIQ for demand forecasting.",
        ],
        "actions": [
            ("Paul Nquyen", "Define WMS control-layer integration scope", "2026-04-09"),
            ("Sofia Berg", "Backtest ForecastIQ on 12 months of history", "2026-04-14"),
            ("Klara Novak", "Baseline picking travel distance at Warehouse B", "2026-04-07"),
        ],
    },
)

ATLAS = Project(
    key="Atlas-Workplace",
    code="AT",
    display="Atlas Workplace",
    domain="office and workplace modernization",
    sponsor="Beacon Corporate Services",
    summary=(
        "Atlas Workplace modernises the corporate office estate with flexible desk "
        "booking, upgraded meeting-room technology, and a workplace experience app to "
        "support hybrid working across three buildings."
    ),
    background=(
        "Hybrid working has left meeting rooms overbooked, desks under-utilised, and "
        "employees frustrated by inconsistent technology. Atlas Workplace introduces "
        "desk and room booking, standardised meeting-room technology, and a workplace "
        "experience app so that space is used efficiently and the on-site experience "
        "improves."
    ),
    director=("Nadia Haddad", "Workplace Programme Lead"),
    people=[
        ("Nadia Haddad", "Workplace Programme Lead"),
        ("Oliver Grant", "Workplace Technology Lead"),
        ("Mira Solberg", "Facilities Experience Manager"),
        ("Chen Wei", "IT Integration Lead"),
        ("Fatima Zahra", "Change and Adoption Lead"),
    ],
    vendors=[
        ("RoomSync", "meeting-room booking panels and AV control"),
        ("DeskFlex Cloud", "desk booking and occupancy analytics"),
        ("Beacon AV", "meeting-room audio-visual integration"),
    ],
    objectives=[
        "Deploy desk booking across three buildings with occupancy analytics.",
        "Standardise meeting-room technology in 60 rooms.",
        "Launch a workplace experience app for booking, wayfinding, and support.",
        "Raise measured employee workplace-experience score by 20 points.",
    ],
    scope_in=(
        "desk booking, meeting-room technology, the workplace experience app, and "
        "occupancy analytics across three buildings."
    ),
    scope_out=(
        "building HVAC and structural works, which are handled by the facilities "
        "capital-works programme."
    ),
    requirements=[
        ("REQ-AT-002", "The system shall allow employees to book desks and rooms from the app.", "Must"),
        ("REQ-AT-006", "The system shall display real-time room availability on door panels.", "Must"),
        ("REQ-AT-010", "The system shall provide occupancy analytics by floor and building.", "Must"),
        ("REQ-AT-013", "The system shall provide single sign-on with the corporate identity provider.", "Must"),
        ("REQ-AT-017", "The system should offer indoor wayfinding to booked spaces.", "Should"),
        ("REQ-AT-021", "The system should raise facilities tickets from the app.", "Should"),
        ("REQ-AT-026", "The system should integrate AV control into room booking.", "Should"),
    ],
    components=[
        ("Booking Service", "Desk and room reservations with conflict handling and check-in."),
        ("Room Technology", "Standardised AV, door panels, and occupancy sensors."),
        ("Experience App", "Booking, wayfinding, and facilities-support front end."),
        ("Analytics Layer", "Occupancy and utilisation reporting by floor and building."),
        ("Identity Integration", "Single sign-on and profile services via the corporate IdP."),
    ],
    decisions=[
        ("DEC-AT-01", "Standardise a single room-technology stack.", "Consistent experience and simpler support."),
        ("DEC-AT-02", "Use corporate SSO for all workplace services.", "Security and a seamless employee experience."),
        ("DEC-AT-03", "Roll out building by building.", "Limits disruption and captures lessons early."),
    ],
    risks=[
        ("RSK-AT-01", "Employee adoption of booking is low.", "Medium", "High", "Change campaign; check-in enforcement; leadership example."),
        ("RSK-AT-02", "AV standardisation delayed by procurement.", "Medium", "Medium", "Framework agreement; early room pilots."),
        ("RSK-AT-03", "Occupancy sensors raise privacy concerns.", "Medium", "Medium", "Aggregate-only analytics; privacy notice; works-council review."),
        ("RSK-AT-04", "SSO integration issues at launch.", "Low", "High", "Early identity integration; fallback access path."),
        ("RSK-AT-05", "Room technology reliability below expectations.", "Medium", "Medium", "Vendor SLAs; proactive monitoring; spare kit."),
    ],
    milestones=[
        ("Foundation", "2026-05-18", "Booking service and SSO live; Building 1 pilot floor."),
        ("Building 1", "2026-08-08", "Desk and room booking across Building 1; 20 rooms upgraded."),
        ("Building 2", "2026-10-25", "Building 2 rollout; app wayfinding released."),
        ("Building 3", "2026-12-12", "Building 3 rollout; 60 rooms standardised."),
        ("Optimisation", "2027-02-22", "Experience score target achieved and sustained."),
    ],
    budget=[
        ("Meeting-room AV and panels", "EUR 1,120,000"),
        ("Desk-booking and sensors", "EUR 460,000"),
        ("Workplace experience app", "EUR 540,000"),
        ("Integration and SSO", "EUR 300,000"),
        ("Change and adoption", "EUR 240,000"),
        ("Programme management", "EUR 280,000"),
        ("Contingency (10%)", "EUR 298,000"),
    ],
    vocab=[
        "workplace", "desk booking", "meeting room", "room booking", "hybrid working",
        "occupancy analytics", "wayfinding", "workplace experience", "audio-visual",
        "single sign-on", "office modernization", "space utilisation",
    ],
    arch_doc=("Solution_Architecture.pdf", "Atlas Workplace — Solution Architecture", "technical"),
    meeting={
        "date": "2026-03-25",
        "attendees": ["Nadia Haddad", "Oliver Grant", "Mira Solberg", "Chen Wei"],
        "decisions": [
            "Standardised on a single AV stack (DEC-AT-01).",
            "Confirmed corporate SSO for all workplace services.",
            "Selected Building 1 pilot floor for the first release.",
        ],
        "actions": [
            ("Oliver Grant", "Finalise room-technology standard specification", "2026-04-11"),
            ("Chen Wei", "Complete SSO integration design with IT security", "2026-04-09"),
            ("Fatima Zahra", "Draft workplace adoption and change plan", "2026-04-13"),
        ],
    },
)

POLARIS = Project(
    key="Polaris-Sustainability",
    code="PS",
    display="Polaris Sustainability",
    domain="environmental and sustainability reporting",
    sponsor="Evergreen Holdings",
    summary=(
        "Polaris Sustainability establishes a corporate carbon-accounting and "
        "sustainability-reporting capability, consolidating emissions data across scopes "
        "and suppliers to meet regulatory disclosure requirements."
    ),
    background=(
        "Sustainability reporting is currently assembled manually each year from "
        "inconsistent sources, making assurance difficult and disclosure slow. Polaris "
        "Sustainability builds a governed carbon-accounting platform that collects "
        "activity data, applies emission factors, and produces auditable Scope 1, 2, and "
        "3 reporting aligned to recognised standards."
    ),
    director=("Johan Lindqvist", "Sustainability Programme Lead"),
    people=[
        ("Johan Lindqvist", "Sustainability Programme Lead"),
        ("Amara Diallo", "Carbon Accounting Lead"),
        ("Victor Hensley", "Supplier Engagement Manager"),
        ("Priti Shah", "ESG Data Analyst"),
        ("Noah Fischer", "Assurance and Controls Lead"),
    ],
    vendors=[
        ("CarbonLedger", "carbon-accounting and emission-factor platform"),
        ("SupplyTrace", "supplier emissions data collection"),
        ("AssureIQ", "ESG assurance workflow tooling"),
    ],
    objectives=[
        "Consolidate Scope 1, 2, and 3 emissions into one governed platform.",
        "Collect supplier emissions data covering 80% of purchased-goods spend.",
        "Produce auditable annual disclosure aligned to recognised standards.",
        "Reduce reporting preparation time from 10 weeks to 3 weeks.",
    ],
    scope_in=(
        "carbon-accounting methodology, activity-data collection, emission-factor "
        "management, supplier emissions engagement, and assured disclosure reporting."
    ),
    scope_out=(
        "operational decarbonisation projects and energy-efficiency capital works, which "
        "are tracked by site sustainability teams."
    ),
    requirements=[
        ("REQ-PS-001", "The platform shall record activity data for Scope 1 and 2 sources.", "Must"),
        ("REQ-PS-005", "The platform shall apply versioned emission factors to activity data.", "Must"),
        ("REQ-PS-009", "The platform shall collect Scope 3 supplier emissions data.", "Must"),
        ("REQ-PS-013", "The platform shall maintain an audit trail for every reported figure.", "Must"),
        ("REQ-PS-017", "The platform should support standard-aligned disclosure templates.", "Should"),
        ("REQ-PS-022", "The platform should flag data gaps and estimation methods.", "Should"),
        ("REQ-PS-026", "The platform should track reduction targets against a baseline.", "Should"),
    ],
    components=[
        ("Activity Data Layer", "Collection of energy, fuel, travel, and purchased-goods activity data."),
        ("Emission Factor Service", "Versioned factor library with methodology traceability."),
        ("Supplier Engagement", "Scope 3 questionnaires, data collection, and validation."),
        ("Reporting & Disclosure", "Standard-aligned templates and auditable disclosures."),
        ("Assurance & Controls", "Audit trail, data-gap flagging, and estimation records."),
    ],
    decisions=[
        ("DEC-PS-01", "Adopt a versioned emission-factor library.", "Reproducible restatement and audit support."),
        ("DEC-PS-02", "Prioritise Scope 3 purchased goods for supplier engagement.", "Largest share of the footprint."),
        ("DEC-PS-03", "Maintain a full audit trail per reported figure.", "Enables external assurance."),
    ],
    risks=[
        ("RSK-PS-01", "Supplier response rate too low for Scope 3.", "High", "High", "Tiered engagement; estimation fallback; procurement leverage."),
        ("RSK-PS-02", "Emission-factor changes cause restatements.", "Medium", "Medium", "Versioned factors; documented restatement policy."),
        ("RSK-PS-03", "Activity data incomplete across sites.", "Medium", "High", "Data-gap flagging; site data owners; phased coverage."),
        ("RSK-PS-04", "Disclosure standard changes mid-cycle.", "Medium", "Medium", "Configurable templates; standards-tracking watch."),
        ("RSK-PS-05", "Assurance findings delay disclosure.", "Low", "High", "Early controls review; internal pre-assurance."),
    ],
    milestones=[
        ("Foundation", "2026-05-22", "Scope 1 and 2 activity data and factor library live."),
        ("Supplier Onboarding", "2026-08-15", "Scope 3 engagement launched for top suppliers."),
        ("Reporting", "2026-10-28", "Standard-aligned disclosure templates operational."),
        ("Assurance", "2026-12-18", "Audit trail and pre-assurance controls in place."),
        ("Disclosure", "2027-03-05", "First assured annual disclosure produced."),
    ],
    budget=[
        ("Carbon-accounting platform", "EUR 540,000"),
        ("Supplier data collection", "EUR 380,000"),
        ("Assurance tooling", "EUR 190,000"),
        ("Methodology and integration", "EUR 460,000"),
        ("Training and engagement", "EUR 220,000"),
        ("Programme management", "EUR 260,000"),
        ("Contingency (10%)", "EUR 205,000"),
    ],
    vocab=[
        "carbon accounting", "emissions", "Scope 3", "emission factor", "sustainability",
        "ESG", "supplier emissions", "carbon footprint", "disclosure", "greenhouse gas",
        "decarbonisation", "environmental reporting",
    ],
    arch_doc=("Reporting_Methodology.pdf", "Polaris Sustainability — Reporting Methodology", "operational"),
    meeting={
        "date": "2026-03-23",
        "attendees": ["Johan Lindqvist", "Amara Diallo", "Victor Hensley", "Noah Fischer"],
        "decisions": [
            "Adopted a versioned emission-factor library (DEC-PS-01).",
            "Prioritised purchased-goods suppliers for Scope 3 engagement.",
            "Agreed a full audit trail for each reported figure.",
        ],
        "actions": [
            ("Amara Diallo", "Finalise Scope 1 and 2 activity-data model", "2026-04-10"),
            ("Victor Hensley", "Draft supplier engagement questionnaire", "2026-04-12"),
            ("Priti Shah", "Assess activity-data gaps across sites", "2026-04-08"),
        ],
    },
)

MERIDIAN = Project(
    key="Meridian-Travel",
    code="MT",
    display="Meridian Travel",
    domain="corporate travel planning",
    sponsor="Crestline Advisory Group",
    summary=(
        "Meridian Travel implements a managed corporate-travel programme with an online "
        "booking tool, policy compliance, duty-of-care tracking, and consolidated "
        "reporting to control travel spend and traveller safety."
    ),
    background=(
        "Business travel is booked through multiple channels with limited policy control "
        "and poor visibility of where travellers are. Meridian Travel introduces a "
        "managed programme with an online booking tool, pre-trip approval, negotiated "
        "supplier rates, and duty-of-care tracking so that travel spend is controlled and "
        "travellers are supported."
    ),
    director=("Camille Laurent", "Travel Programme Manager"),
    people=[
        ("Camille Laurent", "Travel Programme Manager"),
        ("Daniel Brooks", "Travel Technology Lead"),
        ("Yuki Tanaka", "Supplier Relations Manager"),
        ("Sara Molina", "Traveller Care Lead"),
        ("Tobias Roth", "Travel Finance Analyst"),
    ],
    vendors=[
        ("Voyanta OBT", "online booking tool and travel management platform"),
        ("SafeTrip", "traveller tracking and duty-of-care alerts"),
        ("GlobalStay Partners", "negotiated hotel and airfare programme"),
    ],
    objectives=[
        "Channel 85% of bookings through the managed online booking tool.",
        "Enforce pre-trip approval and travel-policy compliance.",
        "Provide duty-of-care tracking and traveller alerts.",
        "Reduce average trip cost by 12% through negotiated rates.",
    ],
    scope_in=(
        "the online booking tool, travel policy and approval workflow, negotiated "
        "supplier rates, duty-of-care tracking, and travel reporting."
    ),
    scope_out=(
        "expense reimbursement processing and corporate-card administration, which "
        "remain with the finance shared-service centre."
    ),
    requirements=[
        ("REQ-MT-002", "The system shall provide an online booking tool for flights, hotels, and rail.", "Must"),
        ("REQ-MT-006", "The system shall enforce pre-trip approval based on travel policy.", "Must"),
        ("REQ-MT-010", "The system shall apply negotiated supplier rates automatically.", "Must"),
        ("REQ-MT-014", "The system shall track traveller location for duty of care.", "Must"),
        ("REQ-MT-018", "The system should send safety alerts to affected travellers.", "Should"),
        ("REQ-MT-023", "The system should consolidate travel spend reporting by department.", "Should"),
        ("REQ-MT-027", "The system should support sustainable-travel options and CO2 reporting.", "Should"),
    ],
    components=[
        ("Booking Tool", "Self-service booking for flights, hotels, and rail with policy checks."),
        ("Approval Workflow", "Pre-trip approval routing based on policy and budget."),
        ("Supplier Rates", "Negotiated fares and rates applied during booking."),
        ("Duty of Care", "Traveller tracking, risk alerts, and assistance."),
        ("Travel Reporting", "Consolidated spend, compliance, and CO2 reporting."),
    ],
    decisions=[
        ("DEC-MT-01", "Mandate the online booking tool for standard trips.", "Drives compliance and supplier savings."),
        ("DEC-MT-02", "Integrate duty-of-care tracking from launch.", "Traveller safety is a programme priority."),
        ("DEC-MT-03", "Route approvals by policy and budget thresholds.", "Balances control with traveller convenience."),
    ],
    risks=[
        ("RSK-MT-01", "Travellers book outside the managed channel.", "High", "Medium", "Policy mandate; leadership support; leakage reporting."),
        ("RSK-MT-02", "Duty-of-care data raises privacy concerns.", "Medium", "High", "Purpose limitation; consent; works-council review."),
        ("RSK-MT-03", "Negotiated rates underperform expectations.", "Medium", "Medium", "Benchmark rates; competitive supplier review."),
        ("RSK-MT-04", "Approval workflow slows urgent travel.", "Medium", "Medium", "Fast-track rules; delegated approvals."),
        ("RSK-MT-05", "Booking-tool adoption is slow.", "Medium", "Medium", "Training; intuitive UX; support desk."),
    ],
    milestones=[
        ("Foundation", "2026-05-16", "Online booking tool live for pilot department."),
        ("Policy & Approval", "2026-08-06", "Pre-trip approval and policy compliance enabled."),
        ("Duty of Care", "2026-10-22", "Traveller tracking and alerts operational."),
        ("Supplier Programme", "2026-12-08", "Negotiated rates fully integrated."),
        ("Optimisation", "2027-02-24", "Booking-channel and savings targets achieved."),
    ],
    budget=[
        ("Booking-tool platform", "EUR 420,000"),
        ("Duty-of-care tracking", "EUR 210,000"),
        ("Supplier programme setup", "EUR 160,000"),
        ("Integration and configuration", "EUR 380,000"),
        ("Training and adoption", "EUR 180,000"),
        ("Programme management", "EUR 240,000"),
        ("Contingency (10%)", "EUR 159,000"),
    ],
    vocab=[
        "corporate travel", "online booking tool", "travel policy", "pre-trip approval",
        "duty of care", "traveller tracking", "negotiated rates", "travel spend",
        "itinerary", "travel management", "airfare", "hotel programme",
    ],
    arch_doc=("Programme_Operating_Model.pdf", "Meridian Travel — Programme Operating Model", "operational"),
    meeting={
        "date": "2026-03-28",
        "attendees": ["Camille Laurent", "Daniel Brooks", "Yuki Tanaka", "Sara Molina"],
        "decisions": [
            "Mandated the online booking tool for standard trips (DEC-MT-01).",
            "Confirmed duty-of-care tracking from launch.",
            "Agreed pilot department for the first release.",
        ],
        "actions": [
            ("Daniel Brooks", "Configure booking-tool policy rules", "2026-04-11"),
            ("Yuki Tanaka", "Finalise negotiated hotel programme", "2026-04-15"),
            ("Sara Molina", "Define duty-of-care alert playbook", "2026-04-09"),
        ],
    },
)

REDWOOD = Project(
    key="Redwood-Facilities",
    code="RF",
    display="Redwood Facilities",
    domain="building maintenance and facilities management",
    sponsor="Harborline Property Trust",
    summary=(
        "Redwood Facilities introduces a computerised maintenance-management system with "
        "preventive maintenance, asset registers, and contractor coordination to improve "
        "building reliability and reduce reactive repairs across a property portfolio."
    ),
    background=(
        "Building maintenance is largely reactive, with paper work-orders, an incomplete "
        "asset register, and inconsistent contractor performance. Redwood Facilities "
        "introduces a computerised maintenance-management system (CMMS) with preventive "
        "maintenance schedules, a complete asset register, and contractor coordination so "
        "that equipment reliability improves and reactive repairs fall."
    ),
    director=("Gregory Palmer", "Facilities Programme Manager"),
    people=[
        ("Gregory Palmer", "Facilities Programme Manager"),
        ("Anita Kapoor", "Maintenance Systems Lead"),
        ("Lucas Meyer", "Asset Management Lead"),
        ("Bianca Ferreira", "Contractor Coordination Lead"),
        ("Samuel Owusu", "Health & Safety Officer"),
    ],
    vendors=[
        ("MaintainPro CMMS", "computerised maintenance-management system"),
        ("AssetRegistry360", "asset register and condition assessment"),
        ("ContractorLink", "contractor scheduling and compliance"),
    ],
    objectives=[
        "Establish a complete asset register across the property portfolio.",
        "Move 70% of maintenance from reactive to preventive.",
        "Reduce critical-equipment downtime by 25%.",
        "Standardise contractor scheduling and compliance tracking.",
    ],
    scope_in=(
        "the CMMS, asset register, preventive-maintenance schedules, work-order "
        "management, and contractor coordination across the portfolio."
    ),
    scope_out=(
        "major capital refurbishment projects and new-build fit-outs, which are managed "
        "by the property development team."
    ),
    requirements=[
        ("REQ-RF-002", "The system shall maintain an asset register with location and criticality.", "Must"),
        ("REQ-RF-006", "The system shall schedule preventive maintenance by asset and interval.", "Must"),
        ("REQ-RF-010", "The system shall manage work orders from request to completion.", "Must"),
        ("REQ-RF-014", "The system shall record contractor assignments and compliance documents.", "Must"),
        ("REQ-RF-018", "The system should track equipment downtime and maintenance history.", "Should"),
        ("REQ-RF-023", "The system should support mobile work-order updates by technicians.", "Should"),
        ("REQ-RF-027", "The system should report maintenance cost by building and asset class.", "Should"),
    ],
    components=[
        ("Asset Register", "Portfolio-wide register with location, criticality, and condition."),
        ("Preventive Maintenance", "Schedules and task lists generated per asset and interval."),
        ("Work Order Management", "Request intake, assignment, execution, and closure."),
        ("Contractor Coordination", "Scheduling, compliance documents, and performance tracking."),
        ("Maintenance Analytics", "Downtime, cost, and reliability reporting by building."),
    ],
    decisions=[
        ("DEC-RF-01", "Build the asset register before enabling preventive maintenance.", "Schedules depend on accurate asset data."),
        ("DEC-RF-02", "Prioritise critical building systems for preventive maintenance.", "Highest reliability and safety impact."),
        ("DEC-RF-03", "Standardise contractor compliance documents.", "Consistent safety and audit posture."),
    ],
    risks=[
        ("RSK-RF-01", "Asset register data incomplete or inaccurate.", "High", "High", "Site surveys; condition assessment; data validation."),
        ("RSK-RF-02", "Technician adoption of mobile work orders is low.", "Medium", "Medium", "Simple mobile UX; on-site training; supervisor support."),
        ("RSK-RF-03", "Contractor non-compliance with safety documents.", "Medium", "High", "Document gating; compliance dashboard; audits."),
        ("RSK-RF-04", "Preventive schedules overload technician capacity.", "Medium", "Medium", "Capacity planning; phased schedule ramp-up."),
        ("RSK-RF-05", "Integration with building systems delayed.", "Medium", "Medium", "Prioritise critical assets; manual fallback."),
    ],
    milestones=[
        ("Asset Foundation", "2026-05-24", "Asset register complete for priority buildings."),
        ("Preventive Rollout", "2026-08-12", "Preventive maintenance live for critical systems."),
        ("Work Orders", "2026-10-24", "Mobile work-order management across the portfolio."),
        ("Contractor Programme", "2026-12-14", "Contractor coordination and compliance operational."),
        ("Optimisation", "2027-02-26", "Downtime and preventive-ratio targets achieved."),
    ],
    budget=[
        ("CMMS platform", "EUR 480,000"),
        ("Asset register and surveys", "EUR 420,000"),
        ("Contractor management", "EUR 180,000"),
        ("Integration and mobile", "EUR 360,000"),
        ("Training and rollout", "EUR 190,000"),
        ("Programme management", "EUR 240,000"),
        ("Contingency (10%)", "EUR 187,000"),
    ],
    vocab=[
        "facilities management", "preventive maintenance", "asset register", "work order",
        "CMMS", "building maintenance", "contractor", "equipment downtime",
        "condition assessment", "maintenance schedule", "reliability", "property portfolio",
    ],
    arch_doc=("Maintenance_Operating_Model.pdf", "Redwood Facilities — Maintenance Operating Model", "operational"),
    meeting={
        "date": "2026-03-29",
        "attendees": ["Gregory Palmer", "Anita Kapoor", "Lucas Meyer", "Bianca Ferreira"],
        "decisions": [
            "Confirmed asset register as the first deliverable (DEC-RF-01).",
            "Prioritised critical building systems for preventive maintenance.",
            "Standardised contractor compliance documentation.",
        ],
        "actions": [
            ("Lucas Meyer", "Complete asset survey plan for priority buildings", "2026-04-10"),
            ("Anita Kapoor", "Configure preventive-maintenance schedules in the CMMS", "2026-04-16"),
            ("Bianca Ferreira", "Define contractor compliance document set", "2026-04-08"),
        ],
    },
)

CEDAR = Project(
    key="Cedar-Events",
    code="CE",
    display="Cedar Events",
    domain="conference and event planning",
    sponsor="Summit Communications",
    summary=(
        "Cedar Events delivers an annual industry conference and a supporting events "
        "programme, covering venue selection, registration, sponsorship, agenda, and "
        "on-site logistics for up to 1,200 attendees."
    ),
    background=(
        "The organisation runs several events each year with fragmented tools for "
        "registration, sponsorship, and logistics, producing duplicated effort and "
        "inconsistent attendee experience. Cedar Events establishes a repeatable event "
        "operating model and toolset covering venue, registration, sponsorship, agenda, "
        "and on-site logistics for its flagship 1,200-attendee conference."
    ),
    director=("Isabel Moreno", "Events Programme Director"),
    people=[
        ("Isabel Moreno", "Events Programme Director"),
        ("Henry Whitfield", "Registration & Technology Lead"),
        ("Layla Nasser", "Sponsorship Manager"),
        ("Oscar Lindgren", "Venue & Logistics Manager"),
        ("Mei Lin", "Attendee Experience Lead"),
    ],
    vendors=[
        ("EventFlow Platform", "registration, ticketing, and attendee app"),
        ("Grand Atrium Venues", "conference venue and catering services"),
        ("StageWorks AV", "staging, audio-visual, and live streaming"),
    ],
    objectives=[
        "Deliver the flagship conference for 1,200 attendees within budget.",
        "Streamline registration with a single platform and attendee app.",
        "Secure sponsorship covering 40% of event cost.",
        "Achieve an attendee satisfaction score above 4.3 of 5.",
    ],
    scope_in=(
        "venue selection, registration and ticketing, sponsorship, agenda and speaker "
        "management, the attendee app, and on-site logistics."
    ),
    scope_out=(
        "post-event marketing campaigns and content publishing, which are handled by the "
        "communications team."
    ),
    requirements=[
        ("REQ-CE-002", "The system shall manage attendee registration and ticketing.", "Must"),
        ("REQ-CE-006", "The system shall publish the agenda and speaker profiles.", "Must"),
        ("REQ-CE-010", "The system shall manage sponsorship packages and deliverables.", "Must"),
        ("REQ-CE-014", "The system shall provide an attendee app with schedule and maps.", "Must"),
        ("REQ-CE-018", "The system should support on-site check-in and badge printing.", "Should"),
        ("REQ-CE-023", "The system should capture attendee feedback per session.", "Should"),
        ("REQ-CE-027", "The system should report registration and sponsorship revenue.", "Should"),
    ],
    components=[
        ("Registration & Ticketing", "Attendee registration, payments, and ticket types."),
        ("Agenda & Speakers", "Session scheduling, speaker profiles, and content."),
        ("Sponsorship", "Package management, deliverables, and sponsor visibility."),
        ("Attendee App", "Schedule, maps, notifications, and session feedback."),
        ("On-site Logistics", "Check-in, badging, staffing, and venue coordination."),
    ],
    decisions=[
        ("DEC-CE-01", "Use one integrated event platform.", "Removes duplicated registration and app tooling."),
        ("DEC-CE-02", "Confirm venue 9 months ahead.", "Secures capacity and catering for peak dates."),
        ("DEC-CE-03", "Tier sponsorship packages.", "Maximises revenue and sponsor satisfaction."),
    ],
    risks=[
        ("RSK-CE-01", "Registration numbers below target.", "Medium", "High", "Early-bird pricing; marketing; partner promotion."),
        ("RSK-CE-02", "Key speaker cancellations.", "Medium", "Medium", "Speaker pipeline; standby list; recorded sessions."),
        ("RSK-CE-03", "Venue or catering capacity shortfall.", "Low", "High", "Early venue confirmation; contracted capacity buffer."),
        ("RSK-CE-04", "On-site check-in bottlenecks.", "Medium", "Medium", "Pre-printed badges; multiple check-in lanes; app QR."),
        ("RSK-CE-05", "Sponsorship revenue shortfall.", "Medium", "High", "Tiered packages; early sponsor outreach; renewals."),
    ],
    milestones=[
        ("Setup", "2026-05-19", "Event platform configured; venue confirmed."),
        ("Registration Open", "2026-07-01", "Registration and sponsorship packages live."),
        ("Agenda Locked", "2026-09-15", "Agenda and speakers confirmed; app content ready."),
        ("Event Delivery", "2026-11-05", "Flagship conference delivered on site."),
        ("Wrap-up", "2026-11-20", "Feedback, revenue, and lessons-learned report."),
    ],
    budget=[
        ("Venue and catering", "EUR 640,000"),
        ("Event platform and app", "EUR 180,000"),
        ("Staging and AV", "EUR 320,000"),
        ("Speaker and content", "EUR 150,000"),
        ("On-site staffing and logistics", "EUR 210,000"),
        ("Programme management", "EUR 160,000"),
        ("Contingency (10%)", "EUR 186,000"),
    ],
    vocab=[
        "conference", "event planning", "registration", "ticketing", "sponsorship",
        "attendee", "venue", "agenda", "speaker", "on-site logistics",
        "attendee app", "event budget",
    ],
    arch_doc=("Event_Operating_Plan.pdf", "Cedar Events — Event Operating Plan", "operational"),
    meeting={
        "date": "2026-03-30",
        "attendees": ["Isabel Moreno", "Henry Whitfield", "Oscar Lindgren", "Mei Lin"],
        "decisions": [
            "Selected one integrated event platform (DEC-CE-01).",
            "Confirmed venue booking nine months ahead.",
            "Agreed tiered sponsorship packages.",
        ],
        "actions": [
            ("Henry Whitfield", "Configure registration and ticket types", "2026-04-12"),
            ("Layla Nasser", "Finalise sponsorship package tiers", "2026-04-14"),
            ("Oscar Lindgren", "Confirm venue contract and catering", "2026-04-07"),
        ],
    },
)


PROJECTS: list[Project] = [
    AURORA, NORTHSTAR, HORIZON, ATLAS, POLARIS, MERIDIAN, REDWOOD, CEDAR,
]

PROJECTS_BY_KEY: dict[str, Project] = {p.key: p for p in PROJECTS}
