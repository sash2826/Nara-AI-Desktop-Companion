"""Atlas Workplace project corpus — office/workplace modernization.

Domain terminology: meeting rooms, office space, access control, workplace
technology, employee experience, room booking, office redesign.
"""

from __future__ import annotations

import os

from .common import SheetSpec, write_docx, write_pdf, write_xlsx

PROJECT = "Atlas-Workplace"

# Reusable access-control prose (consumed by the v2 duplicate download).
ACCESS_PURPOSE = (
    "This plan defines the access control approach for the Atlas Workplace "
    "modernisation programme, covering building entry, floor access, and meeting "
    "room access for employees and visitors across the redesigned office."
)
ACCESS_MODEL = (
    "Access is granted by role-based credentials on mobile and badge. Building entry "
    "uses turnstiles; sensitive floors require an additional access group. Meeting "
    "rooms integrate with the room booking system so that a confirmed booking grants "
    "temporary room access (REQ-AW-012)."
)


def generate(root: str) -> list[str]:
    project_dir = os.path.join(root, PROJECT)
    written: list[str] = []

    path = os.path.join(project_dir, "Project_Overview.pdf")
    write_pdf(
        path,
        [
            ("title", "Atlas Workplace — Project Overview"),
            ("para", "Document ID: AW-DOC-001  |  Version: 1.0  |  Date: 2026-01-28  |  Owner: Grace Fields (Workplace Lead)"),
            ("heading", "Executive Summary"),
            ("para",
             "Atlas Workplace modernises two office buildings into an activity-based workplace with "
             "flexible office space, upgraded meeting rooms, streamlined access control, and improved "
             "employee experience. The programme aligns office redesign with room booking and workplace "
             "technology to support hybrid working."),
            ("heading", "Objectives"),
            ("bullets", [
                "Redesign office space into activity-based zones.",
                "Upgrade 28 meeting rooms with booking and conferencing technology.",
                "Modernise access control for building and floor entry.",
                "Improve employee experience scores measured by survey.",
            ]),
            ("heading", "Scope"),
            ("para",
             "In scope: office layout, meeting room technology, access control, and employee experience. "
             "Out of scope: building HVAC upgrades, handled by facilities."),
            ("heading", "Stakeholders"),
            ("table", (
                ["Name", "Role", "Interest"],
                [
                    ["Grace Fields", "Workplace Lead", "Overall delivery"],
                    ["Owen Bradley", "Facilities Architect", "Office layout"],
                    ["Sara Lindholm", "Security Lead", "Access control"],
                    ["Diego Herrera", "Technology Lead", "Meeting room technology"],
                ],
            )),
            ("heading", "Related Documents"),
            ("bullets", [
                "Workplace Requirements (AW-DOC-002)",
                "Office Layout Proposal (AW-DOC-003)",
                "Access Control Plan (AW-DOC-004)",
                "Meeting Room Strategy (AW-DOC-005)",
            ]),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Workplace_Requirements.docx")
    write_docx(
        path,
        [
            ("title", "Atlas Workplace — Workplace Requirements"),
            ("para", "Document ID: AW-DOC-002  |  Version: 1.1  |  Date: 2026-02-10  |  Author: Owen Bradley"),
            ("heading", "Purpose"),
            ("para",
             "This specification defines requirements for the Atlas Workplace modernisation: office "
             "space, meeting rooms, room booking, access control, and workplace technology. Requirements "
             "are realised by the Office Layout Proposal (AW-DOC-003) and Access Control Plan (AW-DOC-004)."),
            ("heading", "Functional Requirements"),
            ("table", (
                ["ID", "Requirement", "Priority"],
                [
                    ["REQ-AW-001", "The workplace shall provide activity-based zones per floor.", "Must"],
                    ["REQ-AW-005", "Meeting rooms shall be reservable through a room booking system.", "Must"],
                    ["REQ-AW-008", "Room booking shall show real-time availability on floor displays.", "Should"],
                    ["REQ-AW-012", "A confirmed booking shall grant temporary meeting room access.", "Must"],
                    ["REQ-AW-016", "Access control shall use role-based credentials for building and floors.", "Must"],
                ],
            )),
            ("heading", "Non-Functional Requirements"),
            ("bullets", [
                "REQ-AW-030: Employee experience score shall improve to 4.2/5 by programme end.",
                "REQ-AW-032: Room booking availability updates shall reflect within 10 seconds.",
                "REQ-AW-034: Access events shall be logged and retained for 90 days.",
            ]),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Office_Layout_Proposal.pdf")
    write_pdf(
        path,
        [
            ("title", "Atlas Workplace — Office Layout Proposal"),
            ("para", "Document ID: AW-DOC-003  |  Version: 1.0  |  Date: 2026-02-20  |  Author: Owen Bradley"),
            ("heading", "Purpose"),
            ("para",
             "This proposal defines the activity-based office layout realising REQ-AW-001 in the "
             "Workplace Requirements (AW-DOC-002)."),
            ("heading", "Zone Model"),
            ("table", (
                ["Zone", "Purpose", "Capacity"],
                [
                    ["Focus", "Quiet individual work", "40 seats/floor"],
                    ["Collaborate", "Team work and meeting rooms", "6 rooms/floor"],
                    ["Social", "Breakout and informal meetings", "1 hub/floor"],
                    ["Support", "Lockers, print, utilities", "1 area/floor"],
                ],
            )),
            ("heading", "Meeting Rooms"),
            ("para",
             "Meeting rooms are concentrated in the Collaborate zone and integrate with room booking per "
             "the Meeting Room Strategy (AW-DOC-005). Access follows the Access Control Plan (AW-DOC-004)."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Access_Control_Plan.pdf")
    write_pdf(
        path,
        [
            ("title", "Atlas Workplace — Access Control Plan"),
            ("para", "Document ID: AW-DOC-004  |  Version: 1.1  |  Date: 2026-02-27  |  Author: Sara Lindholm"),
            ("heading", "Purpose"),
            ("para", ACCESS_PURPOSE),
            ("heading", "Access Model"),
            ("para", ACCESS_MODEL),
            ("heading", "Access Groups"),
            ("table", (
                ["Group", "Scope", "Credential"],
                [
                    ["Employee", "Building + assigned floors", "Mobile or badge"],
                    ["Visitor", "Reception + booked room", "Temporary QR"],
                    ["Facilities", "All floors + support areas", "Badge"],
                    ["Contractor", "Specific floor + hours", "Time-boxed badge"],
                ],
            )),
            ("heading", "Logging"),
            ("para",
             "All access events are logged and retained for 90 days per REQ-AW-034 and reviewed monthly "
             "by the Security Lead."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Meeting_Room_Strategy.docx")
    write_docx(
        path,
        [
            ("title", "Atlas Workplace — Meeting Room Strategy"),
            ("para", "Document ID: AW-DOC-005  |  Version: 1.0  |  Date: 2026-03-04  |  Author: Diego Herrera"),
            ("heading", "Purpose"),
            ("para",
             "This strategy defines the meeting room technology and room booking approach realising "
             "REQ-AW-005, REQ-AW-008, and REQ-AW-012 in the Workplace Requirements (AW-DOC-002)."),
            ("heading", "Room Tiers"),
            ("table", (
                ["Tier", "Capacity", "Technology"],
                [
                    ["Huddle", "2-4", "Display + booking panel"],
                    ["Standard", "6-8", "Video bar + booking panel"],
                    ["Boardroom", "12-16", "Dual display + room controller"],
                ],
            )),
            ("heading", "Booking and Access"),
            ("para",
             "Room booking panels show availability on floor displays and a confirmed booking grants "
             "temporary room access via the Access Control Plan (AW-DOC-004)."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Employee_Experience_Survey.xlsx")
    write_xlsx(
        path,
        [
            SheetSpec(
                title="Survey Results",
                intro=["Atlas Workplace — Employee Experience Survey (AW-DOC-006)", "Version 1.0  |  2026-03-12  |  Respondents: 412 (fictional)"],
                header=["Question", "Score (/5)", "Prior", "Target"],
                rows=[
                    ["Ease of finding a workspace", 3.6, 3.1, 4.2],
                    ["Meeting room availability", 3.4, 2.9, 4.2],
                    ["Room booking experience", 3.8, 3.2, 4.2],
                    ["Building access convenience", 3.9, 3.5, 4.2],
                    ["Overall workplace satisfaction", 3.7, 3.2, 4.2],
                ],
            )
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Vendor_Proposal.docx")
    write_docx(
        path,
        [
            ("title", "Atlas Workplace — Vendor Proposal"),
            ("para", "Document ID: AW-DOC-007  |  Version: 1.0  |  Date: 2026-03-18  |  Author: Diego Herrera"),
            ("heading", "Purpose"),
            ("para",
             "This proposal evaluates vendors for room booking, meeting room technology, and access "
             "control aligned to the Workplace Requirements (AW-DOC-002)."),
            ("heading", "Candidate Vendors"),
            ("table", (
                ["Vendor", "Component", "Score (/100)", "Notes"],
                [
                    ["RoomFlow", "Room booking", "88", "Strong floor-display support"],
                    ["ConferSpace", "Meeting room AV", "85", "Reliable video bars"],
                    ["GateKey", "Access control", "84", "Mobile credentials"],
                    ["DeskMap", "Workspace booking", "80", "Activity-based zones"],
                ],
            )),
            ("heading", "Recommendation"),
            ("para",
             "Adopt RoomFlow for room booking, ConferSpace for AV, and GateKey for access control; costs "
             "feed the Budget (AW-DOC-008)."),
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Budget.xlsx")
    write_xlsx(
        path,
        [
            SheetSpec(
                title="Costs",
                intro=["Atlas Workplace — Budget (AW-DOC-008)", "Version 1.0  |  2026-03-22  |  Currency: EUR (fictional)"],
                header=["Item", "Vendor", "Qty", "Unit Cost", "Total"],
                rows=[
                    ["Meeting room AV kit", "ConferSpace", 28, 4200, 117600],
                    ["Room booking panel", "RoomFlow", 28, 520, 14560],
                    ["Access control readers", "GateKey", 46, 380, 17480],
                    ["Workspace booking sensors", "DeskMap", 240, 45, 10800],
                    ["Office fit-out", "Facilities", 1, 380000, 380000],
                ],
            )
        ],
    )
    written.append(path)

    path = os.path.join(project_dir, "Implementation_Timeline.xlsx")
    write_xlsx(
        path,
        [
            SheetSpec(
                title="Timeline",
                intro=["Atlas Workplace — Implementation Timeline (AW-DOC-009)", "Version 1.0  |  2026-03-26"],
                header=["Milestone", "Building", "Start", "End", "Status"],
                rows=[
                    ["Office layout fit-out", "Building A", "2026-04-01", "2026-05-30", "Planned"],
                    ["Meeting room AV install", "Building A", "2026-05-01", "2026-06-15", "Planned"],
                    ["Access control cutover", "Building A", "2026-06-01", "2026-06-20", "Planned"],
                    ["Office layout fit-out", "Building B", "2026-06-15", "2026-08-15", "Planned"],
                    ["Employee experience resurvey", "Both", "2026-09-01", "2026-09-15", "Planned"],
                ],
            )
        ],
    )
    written.append(path)

    return written
