"""Northstar Analytics project corpus — business analytics and data platform.

Domain terminology: data pipelines, analytics, dashboards, data warehouse,
data quality, governance, reporting, business intelligence.
"""

from __future__ import annotations

import os

from .common import SheetSpec, write_docx, write_pdf, write_xlsx

PROJECT = "Northstar-Analytics"

# Reusable requirements prose (consumed by the RevB duplicate download).
REQ_PURPOSE = (
    "This specification defines the requirements for the Northstar Analytics data "
    "platform: the data pipelines, the central data warehouse, data quality "
    "controls, and the reporting and dashboard layer. Requirements are realised by "
    "the Analytics Architecture (NA-DOC-003) and governed by the Data Governance "
    "Plan (NA-DOC-004)."
)
REQ_PIPELINE = (
    "Ingestion pipelines shall land raw source data, apply validation, and publish "
    "conformed tables into the data warehouse. Each pipeline shall record row counts "
    "and data-quality outcomes so that dashboard accuracy can be traced to source "
    "loads (REQ-NA-006)."
)


def generate(root: str) -> list[str]:
    project_dir = os.path.join(root, PROJECT)
    written: list[str] = []

    path = os.path.join(project_dir, "Project_Overview.pdf")
    write_pdf(
        path,
        [
            ("title", "Northstar Analytics — Project Overview"),
            ("para", "Document ID: NA-DOC-001  |  Version: 1.1  |  Date: 2026-02-20  |  Owner: Hannah Boateng (Product Lead)"),
            ("heading", "Executive Summary"),
            ("para",
             "Northstar Analytics delivers an enterprise business-intelligence platform that unifies "
             "fragmented reporting into a governed data warehouse with curated data pipelines and "
             "self-service dashboards. The platform gives business teams trusted analytics without "
             "extracting data into personal spreadsheets."),
            ("heading", "Objectives"),
            ("bullets", [
                "Consolidate 14 source systems into a single governed data warehouse.",
                "Provide certified dashboards with documented data quality metrics.",
                "Reduce manual reporting effort through automated data pipelines.",
                "Establish data governance ownership for every reporting domain.",
            ]),
            ("heading", "Scope"),
            ("para",
             "In scope: data pipelines, the data warehouse, data quality monitoring, governance, and "
             "the dashboard reporting layer. Out of scope: source-system remediation, which is handled "
             "by each system owner."),
            ("heading", "Stakeholders"),
            ("table", (
                ["Name", "Role", "Interest"],
                [
                    ["Hannah Boateng", "Product Lead", "Dashboard adoption"],
                    ["Ibrahim Osei", "Data Platform Architect", "Warehouse and pipelines"],
                    ["Lena Vogt", "Data Governance Lead", "Data quality and ownership"],
                    ["Marcus Reid", "Security Reviewer", "Access and data protection"],
                ],
            )),
            ("heading", "Related Documents"),
            ("bullets", [
                "Data Platform Requirements (NA-DOC-002)",
                "Analytics Architecture (NA-DOC-003)",
                "Data Governance Plan (NA-DOC-004)",
                "Dashboard Specification (NA-DOC-005)",
            ]),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Data_Platform_Requirements.docx")
    write_docx(
        path,
        [
            ("title", "Northstar Analytics — Data Platform Requirements"),
            ("para", "Document ID: NA-DOC-002  |  Version: 1.3  |  Date: 2026-03-05  |  Author: Ibrahim Osei"),
            ("heading", "Purpose"),
            ("para", REQ_PURPOSE),
            ("heading", "Functional Requirements"),
            ("table", (
                ["ID", "Requirement", "Priority"],
                [
                    ["REQ-NA-001", "The platform shall ingest data from 14 registered source systems.", "Must"],
                    ["REQ-NA-006", "Pipelines shall record row counts and data-quality outcomes per load.", "Must"],
                    ["REQ-NA-009", "The warehouse shall expose conformed reporting tables per domain.", "Must"],
                    ["REQ-NA-012", "Dashboards shall display certified data-quality indicators.", "Should"],
                    ["REQ-NA-015", "Governance shall assign an owner to every reporting domain.", "Must"],
                ],
            )),
            ("heading", "Data Pipeline Requirements"),
            ("para", REQ_PIPELINE),
            ("heading", "Non-Functional Requirements"),
            ("bullets", [
                "REQ-NA-030: Daily pipelines shall complete within the overnight batch window.",
                "REQ-NA-032: Dashboard queries shall return within three seconds at P95.",
                "REQ-NA-034: All warehouse access shall be role-based and audited.",
            ]),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Analytics_Architecture.pdf")
    write_pdf(
        path,
        [
            ("title", "Northstar Analytics — Analytics Architecture"),
            ("para", "Document ID: NA-DOC-003  |  Version: 1.2  |  Date: 2026-03-19  |  Author: Ibrahim Osei"),
            ("heading", "Overview"),
            ("para",
             "The analytics architecture realises the Data Platform Requirements (NA-DOC-002). It "
             "comprises ingestion pipelines, a layered data warehouse, a data quality service, and a "
             "dashboard serving layer for business intelligence."),
            ("heading", "Warehouse Layers"),
            ("table", (
                ["Layer", "Purpose", "Related Requirement"],
                [
                    ["Raw", "Immutable landing of source data", "REQ-NA-001"],
                    ["Conformed", "Cleaned, standardised entities", "REQ-NA-009"],
                    ["Mart", "Domain reporting tables", "REQ-NA-009"],
                    ["Quality", "Data-quality metrics per load", "REQ-NA-006"],
                ],
            )),
            ("heading", "Data Quality Service"),
            ("para",
             "The data quality service evaluates completeness, validity, and freshness for each pipeline "
             "load and publishes indicators consumed by the Dashboard Specification (NA-DOC-005). This "
             "supports REQ-NA-012."),
            ("heading", "Cross-References"),
            ("para",
             "Platform tooling selection is assessed in the Vendor Evaluation (NA-DOC-006); access "
             "controls are covered by the Security Review (NA-DOC-007)."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Data_Governance_Plan.pdf")
    write_pdf(
        path,
        [
            ("title", "Northstar Analytics — Data Governance Plan"),
            ("para", "Document ID: NA-DOC-004  |  Version: 1.0  |  Date: 2026-03-26  |  Author: Lena Vogt"),
            ("heading", "Purpose"),
            ("para",
             "This plan establishes governance for the Northstar Analytics data platform: ownership, "
             "data quality standards, and stewardship processes that keep dashboards trustworthy."),
            ("heading", "Governance Model"),
            ("bullets", [
                "Each reporting domain has a named data owner and steward (REQ-NA-015).",
                "Data quality thresholds are agreed per domain and monitored per load.",
                "Changes to conformed tables follow a review and approval workflow.",
            ]),
            ("heading", "Data Quality Standards"),
            ("table", (
                ["Dimension", "Definition", "Threshold"],
                [
                    ["Completeness", "Required fields populated", ">= 99%"],
                    ["Validity", "Values conform to domain rules", ">= 98%"],
                    ["Freshness", "Load within batch window", "100%"],
                ],
            )),
            ("heading", "Cross-References"),
            ("para",
             "Quality indicators defined here are surfaced through the Dashboard Specification "
             "(NA-DOC-005) and derived by the data quality service in the Analytics Architecture "
             "(NA-DOC-003)."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Dashboard_Specification.docx")
    write_docx(
        path,
        [
            ("title", "Northstar Analytics — Dashboard Specification"),
            ("para", "Document ID: NA-DOC-005  |  Version: 1.1  |  Date: 2026-04-01  |  Author: Hannah Boateng"),
            ("heading", "Purpose"),
            ("para",
             "This specification defines the certified dashboards delivered by Northstar Analytics and "
             "the data-quality indicators they display, satisfying REQ-NA-012."),
            ("heading", "Dashboard Catalogue"),
            ("table", (
                ["Dashboard", "Domain", "Primary Metrics"],
                [
                    ["Revenue Overview", "Finance", "Revenue, margin, trend"],
                    ["Operations Pulse", "Operations", "Throughput, backlog"],
                    ["Customer Insights", "Sales", "Acquisition, retention"],
                    ["Data Quality Monitor", "Governance", "Completeness, validity, freshness"],
                ],
            )),
            ("heading", "Certification"),
            ("para",
             "A dashboard is certified only when its underlying marts pass the data quality thresholds "
             "in the Data Governance Plan (NA-DOC-004). Certification status is shown on each dashboard."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Vendor_Evaluation.docx")
    write_docx(
        path,
        [
            ("title", "Northstar Analytics — Vendor Evaluation"),
            ("para", "Document ID: NA-DOC-006  |  Version: 1.0  |  Date: 2026-04-08  |  Author: Ibrahim Osei"),
            ("heading", "Purpose"),
            ("para",
             "This evaluation selects platform tooling for the warehouse, pipelines, and dashboards "
             "defined in the Analytics Architecture (NA-DOC-003)."),
            ("heading", "Candidate Vendors"),
            ("table", (
                ["Vendor", "Component", "Score (/100)", "Notes"],
                [
                    ["Lumen Data Cloud", "Data warehouse", "89", "Strong governance features"],
                    ["FlowForge", "Pipeline orchestration", "85", "Good data-quality hooks"],
                    ["InsightBoard", "Dashboard/BI", "83", "Fast query serving"],
                    ["ClearMetrics", "Data quality", "80", "Complements FlowForge"],
                ],
            )),
            ("heading", "Recommendation"),
            ("para",
             "Adopt Lumen Data Cloud for the warehouse, FlowForge for pipelines, and InsightBoard for "
             "dashboards. Costs are captured in the Budget (NA-DOC-008)."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Security_Review.pdf")
    write_pdf(
        path,
        [
            ("title", "Northstar Analytics — Security Review"),
            ("para", "Document ID: NA-DOC-007  |  Version: 1.0  |  Date: 2026-04-12  |  Author: Marcus Reid"),
            ("heading", "Scope"),
            ("para",
             "This review evaluates access control and data protection for the Northstar Analytics "
             "warehouse and dashboards defined in the Analytics Architecture (NA-DOC-003)."),
            ("heading", "Findings"),
            ("table", (
                ["Area", "Finding", "Action"],
                [
                    ["Warehouse access", "Role-based access present", "Add quarterly access review"],
                    ["Dashboard sharing", "Broad share links possible", "Restrict to governed groups"],
                    ["Audit logging", "Query audit enabled", "Retain logs 12 months"],
                    ["PII in marts", "Some marts contain PII", "Apply column masking"],
                ],
            )),
            ("heading", "Recommendation"),
            ("para",
             "Apply column masking to PII marts and restrict dashboard sharing before broad rollout, "
             "meeting REQ-NA-034."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Budget.xlsx")
    write_xlsx(
        path,
        [
            SheetSpec(
                title="Platform Costs",
                intro=["Northstar Analytics — Budget (NA-DOC-008)", "Version 1.0  |  2026-04-15  |  Currency: EUR (fictional)"],
                header=["Item", "Vendor", "Basis", "Annual Cost"],
                rows=[
                    ["Data warehouse", "Lumen Data Cloud", "Compute + storage", 168000],
                    ["Pipeline orchestration", "FlowForge", "Managed service", 54000],
                    ["Dashboard / BI", "InsightBoard", "Per user", 72000],
                    ["Data quality", "ClearMetrics", "Add-on", 26000],
                ],
            ),
            SheetSpec(
                title="Implementation",
                header=["Item", "Basis", "One-off Cost"],
                rows=[
                    ["Pipeline build", "14 source systems", 96000],
                    ["Warehouse modelling", "Conformed + marts", 58000],
                    ["Dashboard build", "Certified dashboards", 44000],
                ],
            ),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Meeting_Notes.docx")
    write_docx(
        path,
        [
            ("title", "Northstar Analytics — Meeting Notes"),
            ("para", "Document ID: NA-DOC-009  |  Version: rolling  |  Last updated: 2026-04-18"),
            ("heading", "2026-03-20 — Architecture Sign-off"),
            ("para",
             "The team approved the Analytics Architecture (NA-DOC-003) including the four warehouse "
             "layers and the data quality service. Action: Lena to finalise domain ownership in the "
             "Data Governance Plan."),
            ("heading", "2026-04-09 — Tooling Decision"),
            ("para",
             "Accepted the Vendor Evaluation (NA-DOC-006) recommendation: Lumen Data Cloud, FlowForge, "
             "and InsightBoard. Budget to be updated in NA-DOC-008."),
            ("heading", "2026-04-17 — Dashboard Certification"),
            ("para",
             "Confirmed that dashboards display data-quality indicators per the Dashboard Specification "
             "(NA-DOC-005) and only certify when marts meet governance thresholds."),
        ],
    )
    written.append(path)

    return written
