"""Polaris Sustainability project corpus — environmental reporting.

Domain terminology: carbon emissions, sustainability, environmental reporting,
supplier emissions, energy consumption, carbon accounting, sustainability metrics.
"""

from __future__ import annotations

import os

from .common import SheetSpec, write_docx, write_pdf, write_xlsx

PROJECT = "Polaris-Sustainability"

# Reusable carbon-framework prose (consumed by the 2026 Update duplicate).
CARBON_PURPOSE = (
    "This framework defines how the Polaris Sustainability programme measures, "
    "accounts for, and reports carbon emissions across Scope 1, Scope 2, and Scope 3 "
    "sources, including supplier emissions and energy consumption."
)
CARBON_METHOD = (
    "Carbon accounting follows an activity-data approach: consumption quantities are "
    "multiplied by emission factors to produce tonnes of CO2-equivalent. Supplier "
    "emissions are collected through the Supplier Sustainability Assessment and "
    "consolidated into the environmental data model (REQ-PS-009)."
)


def generate(root: str) -> list[str]:
    project_dir = os.path.join(root, PROJECT)
    written: list[str] = []

    path = os.path.join(project_dir, "Project_Overview.pdf")
    write_pdf(
        path,
        [
            ("title", "Polaris Sustainability — Project Overview"),
            ("para", "Document ID: PS-DOC-001  |  Version: 1.0  |  Date: 2026-01-15  |  Owner: Elena Marković (Sustainability Lead)"),
            ("heading", "Executive Summary"),
            ("para",
             "Polaris Sustainability establishes an environmental reporting programme to measure carbon "
             "emissions, track energy consumption, and report sustainability metrics across operations "
             "and the supply chain. It delivers a carbon reporting framework, an environmental data "
             "model, and supplier sustainability assessments to support compliant disclosure."),
            ("heading", "Objectives"),
            ("bullets", [
                "Establish carbon accounting across Scope 1, 2, and 3 emissions.",
                "Collect supplier emissions through structured assessments.",
                "Automate environmental reporting from a single data model.",
                "Meet disclosure requirements with auditable sustainability metrics.",
            ]),
            ("heading", "Scope"),
            ("para",
             "In scope: carbon accounting, energy consumption tracking, supplier emissions, and "
             "environmental reporting. Out of scope: operational emission-reduction projects, tracked "
             "separately by operations."),
            ("heading", "Stakeholders"),
            ("table", (
                ["Name", "Role", "Interest"],
                [
                    ["Elena Marković", "Sustainability Lead", "Programme delivery"],
                    ["Johan Pettersson", "Data Model Owner", "Environmental data"],
                    ["Amara Diallo", "Supplier Programme Lead", "Supplier emissions"],
                    ["Ravi Menon", "Compliance Officer", "Disclosure compliance"],
                ],
            )),
            ("heading", "Related Documents"),
            ("bullets", [
                "Sustainability Requirements (PS-DOC-002)",
                "Carbon Reporting Framework (PS-DOC-003)",
                "Environmental Data Model (PS-DOC-004)",
                "Supplier Sustainability Assessment (PS-DOC-005)",
            ]),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Sustainability_Requirements.docx")
    write_docx(
        path,
        [
            ("title", "Polaris Sustainability — Sustainability Requirements"),
            ("para", "Document ID: PS-DOC-002  |  Version: 1.2  |  Date: 2026-01-29  |  Author: Johan Pettersson"),
            ("heading", "Purpose"),
            ("para",
             "This specification defines requirements for carbon accounting, energy consumption "
             "tracking, supplier emissions, and environmental reporting. Requirements are realised by "
             "the Carbon Reporting Framework (PS-DOC-003) and Environmental Data Model (PS-DOC-004)."),
            ("heading", "Functional Requirements"),
            ("table", (
                ["ID", "Requirement", "Priority"],
                [
                    ["REQ-PS-001", "The system shall record activity data for Scope 1 and 2 emissions.", "Must"],
                    ["REQ-PS-005", "The system shall apply emission factors to compute CO2e.", "Must"],
                    ["REQ-PS-009", "The system shall consolidate supplier emissions into the data model.", "Must"],
                    ["REQ-PS-013", "The system shall generate periodic environmental reports.", "Must"],
                    ["REQ-PS-016", "The system shall retain auditable calculation trails.", "Should"],
                ],
            )),
            ("heading", "Non-Functional Requirements"),
            ("bullets", [
                "REQ-PS-030: Emission calculations shall be reproducible from stored activity data.",
                "REQ-PS-032: Reports shall be exportable in a disclosure-ready format.",
                "REQ-PS-034: Emission factors shall be versioned with effective dates.",
            ]),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Carbon_Reporting_Framework.pdf")
    write_pdf(
        path,
        [
            ("title", "Polaris Sustainability — Carbon Reporting Framework"),
            ("para", "Document ID: PS-DOC-003  |  Version: 1.1  |  Date: 2026-02-12  |  Author: Elena Marković"),
            ("heading", "Purpose"),
            ("para", CARBON_PURPOSE),
            ("heading", "Accounting Method"),
            ("para", CARBON_METHOD),
            ("heading", "Emission Scopes"),
            ("table", (
                ["Scope", "Source", "Example"],
                [
                    ["Scope 1", "Direct emissions", "On-site fuel combustion"],
                    ["Scope 2", "Purchased energy", "Electricity consumption"],
                    ["Scope 3", "Value chain", "Supplier emissions, logistics"],
                ],
            )),
            ("heading", "Reporting Cadence"),
            ("para",
             "Emissions are reported quarterly and consolidated annually. Supplier emissions are drawn "
             "from the Supplier Sustainability Assessment (PS-DOC-005) and modelled per the "
             "Environmental Data Model (PS-DOC-004)."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Environmental_Data_Model.docx")
    write_docx(
        path,
        [
            ("title", "Polaris Sustainability — Environmental Data Model"),
            ("para", "Document ID: PS-DOC-004  |  Version: 1.0  |  Date: 2026-02-19  |  Author: Johan Pettersson"),
            ("heading", "Purpose"),
            ("para",
             "This model defines the entities and relationships for storing activity data, emission "
             "factors, and computed emissions realising REQ-PS-005 and REQ-PS-009."),
            ("heading", "Core Entities"),
            ("table", (
                ["Entity", "Description", "Key Fields"],
                [
                    ["ActivityRecord", "Consumption/activity data", "site, period, quantity, unit"],
                    ["EmissionFactor", "Factor per activity type", "type, factor, effective_date"],
                    ["EmissionResult", "Computed CO2e", "scope, tonnes_co2e, source"],
                    ["Supplier", "Supplier emissions source", "supplier_id, scope3_co2e"],
                ],
            )),
            ("heading", "Cross-References"),
            ("para",
             "Emission factors are versioned per REQ-PS-034; supplier records are populated from the "
             "Supplier Sustainability Assessment (PS-DOC-005)."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Supplier_Sustainability_Assessment.xlsx")
    write_xlsx(
        path,
        [
            SheetSpec(
                title="Supplier Emissions",
                intro=["Polaris Sustainability — Supplier Sustainability Assessment (PS-DOC-005)", "Version 1.0  |  2026-02-26"],
                header=["Supplier", "Category", "Scope 3 CO2e (t)", "Data Quality"],
                rows=[
                    ["Everbright Materials", "Raw materials", 1420, "Measured"],
                    ["TransNordic Freight", "Logistics", 980, "Estimated"],
                    ["PackWell", "Packaging", 310, "Measured"],
                    ["GreenGrid Energy", "Energy", 640, "Measured"],
                    ["OfficeSupplyCo", "Indirect goods", 120, "Estimated"],
                ],
            ),
            SheetSpec(
                title="Assessment Scores",
                header=["Supplier", "Sustainability Score (/100)", "Improvement Area"],
                rows=[
                    ["Everbright Materials", 74, "Recycled content"],
                    ["TransNordic Freight", 68, "Fleet electrification"],
                    ["PackWell", 82, "Renewable energy"],
                    ["GreenGrid Energy", 88, "Reporting cadence"],
                ],
            ),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Reporting_Requirements.pdf")
    write_pdf(
        path,
        [
            ("title", "Polaris Sustainability — Reporting Requirements"),
            ("para", "Document ID: PS-DOC-006  |  Version: 1.0  |  Date: 2026-03-03  |  Author: Ravi Menon"),
            ("heading", "Purpose"),
            ("para",
             "This document specifies the environmental reporting outputs realising REQ-PS-013, drawing "
             "on the Carbon Reporting Framework (PS-DOC-003) and Environmental Data Model (PS-DOC-004)."),
            ("heading", "Report Catalogue"),
            ("table", (
                ["Report", "Cadence", "Contents"],
                [
                    ["Emissions Summary", "Quarterly", "Scope 1/2/3 CO2e totals"],
                    ["Supplier Emissions", "Quarterly", "Top supplier Scope 3"],
                    ["Energy Consumption", "Monthly", "Electricity and fuel use"],
                    ["Annual Disclosure", "Annual", "Consolidated CO2e and trends"],
                ],
            )),
            ("heading", "Auditability"),
            ("para",
             "Every reported figure links to stored activity data and versioned emission factors per "
             "REQ-PS-016 and REQ-PS-030."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Compliance_Review.pdf")
    write_pdf(
        path,
        [
            ("title", "Polaris Sustainability — Compliance Review"),
            ("para", "Document ID: PS-DOC-007  |  Version: 1.0  |  Date: 2026-03-11  |  Author: Ravi Menon"),
            ("heading", "Scope"),
            ("para",
             "This review checks the Polaris Sustainability reporting outputs against fictional "
             "disclosure obligations and internal sustainability metrics."),
            ("heading", "Findings"),
            ("table", (
                ["Area", "Finding", "Action"],
                [
                    ["Scope 3 coverage", "Some suppliers estimated", "Increase measured data share"],
                    ["Emission factors", "Versioned with dates", "Maintain factor register"],
                    ["Audit trail", "Calculations reproducible", "Document review sign-off"],
                    ["Disclosure format", "Export ready", "Confirm annual template"],
                ],
            )),
            ("heading", "Recommendation"),
            ("para",
             "Increase the share of measured supplier emissions and maintain the emission factor "
             "register before annual disclosure."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Budget.xlsx")
    write_xlsx(
        path,
        [
            SheetSpec(
                title="Costs",
                intro=["Polaris Sustainability — Budget (PS-DOC-008)", "Version 1.0  |  2026-03-15  |  Currency: EUR (fictional)"],
                header=["Item", "Basis", "Annual Cost"],
                rows=[
                    ["Carbon accounting platform", "Managed service", 88000],
                    ["Supplier assessment programme", "Per programme", 42000],
                    ["Environmental data modelling", "Implementation", 60000],
                    ["Compliance and assurance", "Annual", 35000],
                ],
            )
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Meeting_Notes.docx")
    write_docx(
        path,
        [
            ("title", "Polaris Sustainability — Meeting Notes"),
            ("para", "Document ID: PS-DOC-009  |  Version: rolling  |  Last updated: 2026-03-17"),
            ("heading", "2026-02-13 — Framework Review"),
            ("para",
             "Approved the Carbon Reporting Framework (PS-DOC-003) including the activity-data method "
             "and Scope 1/2/3 breakdown. Action: Johan to finalise the Environmental Data Model."),
            ("heading", "2026-02-27 — Supplier Programme"),
            ("para",
             "Reviewed the Supplier Sustainability Assessment (PS-DOC-005). Agreed to raise the share of "
             "measured supplier emissions ahead of annual disclosure."),
            ("heading", "2026-03-12 — Compliance Check"),
            ("para",
             "Accepted the Compliance Review (PS-DOC-007) findings. Emission factor register to be "
             "maintained and calculation trails documented per the Reporting Requirements (PS-DOC-006)."),
        ],
    )
    written.append(path)

    return written
