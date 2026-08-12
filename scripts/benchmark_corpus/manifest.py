"""Ground-truth manifest and test-instruction generators."""

from __future__ import annotations

import os

GROUND_TRUTH = """# File Organization Ground Truth

This manifest is the authoritative expected result for every file in
`download-recommendations`. All projects, people, vendors, and figures are
fictional. Compare the Enterprise AI Companion's recommendations against this
table when scoring a test run.

Project folders live under `test-drive/`:

- `Aurora-Mobility` — EV charging infrastructure
- `Northstar-Analytics` — business analytics / data platform
- `Horizon-Logistics` — warehouse and logistics optimization
- `Atlas-Workplace` — office / workplace modernization
- `Polaris-Sustainability` — environmental / sustainability reporting

---

## 1. Obvious Matches

| File | Expected Folder | Expected Action | Confidence | Reason |
| ---- | --------------- | --------------- | ---------- | ------ |
| Aurora_Mobility_Charging_Deployment_Proposal.pdf | Aurora-Mobility | Move | High | Names Aurora Mobility and charging-station deployment explicitly. |
| Northstar_Dashboard_Requirements_Update.docx | Northstar-Analytics | Move | High | Names Northstar Analytics and dashboard requirements explicitly. |
| Horizon_Warehouse_Optimization_Proposal.pdf | Horizon-Logistics | Move | High | Names Horizon Logistics and warehouse optimization explicitly. |
| Atlas_Meeting_Room_Technology_Proposal.pdf | Atlas-Workplace | Move | High | Names Atlas Workplace and meeting room technology explicitly. |
| Polaris_Carbon_Reporting_Guidelines.pdf | Polaris-Sustainability | Move | High | Names Polaris Sustainability and carbon reporting explicitly. |

---

## 2. Semantic Matches

Filename does not name the target project; the content determines the destination.

| File | Expected Folder | Expected Action | Confidence | Reason |
| ---- | --------------- | --------------- | ---------- | ------ |
| Smart_Energy_Load_Management_Study.pdf | Aurora-Mobility | Move / Suggest | Medium-High | Content is EV charging load balancing, station utilisation, fleet charging, off-peak schedules. |
| Data_Quality_Monitoring_Framework.docx | Northstar-Analytics | Move / Suggest | Medium-High | Content is data pipelines, warehouse quality, dashboard accuracy, reporting. |
| Warehouse_Demand_Forecasting_Model.xlsx | Horizon-Logistics | Move / Suggest | Medium-High | Content is warehouse demand, inventory, routing, delivery forecasting. |
| Workspace_Access_Experience_Study.pdf | Atlas-Workplace | Move / Suggest | Medium-High | Content is office access, meeting rooms, workplace experience, room booking. |
| Supplier_Emissions_Data_Framework.docx | Polaris-Sustainability | Move / Suggest | Medium-High | Content is supplier emissions, carbon accounting, environmental data, sustainability metrics. |

---

## 3. Ambiguous Matches

Multiple plausible destinations. The correct behaviour is to flag ambiguity, not to auto-move.

| File | Possible Folder 1 | Possible Folder 2 | Expected Action | Confidence | Reason |
| ---- | ----------------- | ----------------- | --------------- | ---------- | ------ |
| Enterprise_Data_Governance_Guide.pdf | Northstar-Analytics | Polaris-Sustainability | Ask user | Low | Data governance applies to both the analytics warehouse and sustainability reporting data. |
| Energy_Consumption_Analytics_Report.xlsx | Aurora-Mobility | Polaris-Sustainability | Ask user | Low | Energy/charging load (Aurora), CO2e reporting (Polaris), and analytics (Northstar) all plausible. |
| Operations_Performance_Review.pdf | Horizon-Logistics | Northstar-Analytics | Ask user | Low | Operational metrics fit logistics operations and analytics dashboards. |
| Access_Security_Architecture.pdf | Atlas-Workplace | Aurora-Mobility | Ask user | Low | Access control fits workplace entry and charging-endpoint/API security. |
| Vendor_Performance_Framework.docx | (any) | (any) | Ask user | Low | Generic vendor-scoring framework; no project-specific content. |

---

## 4. Wrong-Project Matches

Filename points at the wrong project; content determines the true destination. Filename-based classification would fail.

| File | Filename Suggests | Actual Folder | Expected Action | Reason |
| ---- | ----------------- | ------------- | --------------- | ------ |
| Aurora_Analytics_Dashboard.pdf | Aurora-Mobility | Northstar-Analytics | Move to Northstar-Analytics | Content is analytics dashboards, warehouse marts, data quality — not charging. |
| Horizon_Employee_Workplace_Report.pdf | Horizon-Logistics | Atlas-Workplace | Move to Atlas-Workplace | Content is office space, meeting rooms, workplace access, employee experience. |
| Polaris_Logistics_Data_Report.pdf | Polaris-Sustainability | Horizon-Logistics | Move to Horizon-Logistics | Content is inventory, routing, fleet scheduling, distribution centres. |
| Atlas_Sustainability_Review.pdf | Atlas-Workplace | Polaris-Sustainability | Move to Polaris-Sustainability | Content is carbon accounting, supplier emissions, energy consumption. |

---

## 5. Completely Unrelated Files

| File | Expected Action | Reason |
| ---- | --------------- | ------ |
| Personal_Travel_Insurance.pdf | No migration recommendation | Personal travel insurance; no relationship to any project. |
| Home_Garden_Improvement_Budget.xlsx | No migration recommendation | Personal home/garden expenses; no relationship to any project. |
| Photography_Equipment_Guide.pdf | No migration recommendation | Personal photography hobby guide; no relationship to any project. |

---

## 6. Duplicate / Updated Versions

Each downloaded file is a newer version of an existing project document. The system should detect the project AND the relationship to the existing file.

| Downloaded File | Existing File | Expected Relationship | Expected Action | Reason |
| --------------- | ------------- | --------------------- | --------------- | ------ |
| Aurora_Technical_Architecture_v2.pdf | Aurora-Mobility/Technical_Architecture.pdf | Updated version (v2.0) | Flag as updated version | Same architecture (AM-DOC-003) plus new authentication section and revised REQ-AM-034/021. |
| Data_Platform_Requirements_RevB.docx | Northstar-Analytics/Data_Platform_Requirements.docx | Updated version (Rev B) | Flag as updated version | Same requirements (NA-DOC-002); 14→16 sources, REQ-NA-012 promoted, REQ-NA-018 added. |
| Warehouse_Requirements_Updated.pdf | Horizon-Logistics/Warehouse_Requirements.pdf | Updated version (v1.3) | Flag as updated version | Same requirements (HL-DOC-002); REQ-HL-015 promoted, REQ-HL-018 added. |
| Access_Control_Plan_v2.pdf | Atlas-Workplace/Access_Control_Plan.pdf | Updated version (v2.0) | Flag as updated version | Same plan (AW-DOC-004); adds Event Guest group, retention 90→180 days. |
| Carbon_Reporting_Framework_2026_Update.pdf | Polaris-Sustainability/Carbon_Reporting_Framework.pdf | Updated version (v2.0) | Flag as updated version | Same framework (PS-DOC-003); adds market-based Scope 2, 2026 factor set. |
"""


TEST_INSTRUCTIONS = """# Test Instructions — File Organization Benchmark

This benchmark evaluates the Enterprise AI Companion's file placement pipeline:
download detection, content extraction, semantic understanding, project
classification, migration recommendation, duplicate/updated-version detection,
confidence scoring, and correct rejection of ambiguous or unrelated files.

All data is synthetic. Ground truth is in `FILE_ORGANIZATION_GROUND_TRUTH.md`.

## Layout

- Existing project corpus: `test-drive/` (five project folders).
- Download simulation corpus: `download-recommendations/` (flat folder, no subfolders).

## Test Procedure

1. Ensure the five project folders exist under `test-drive/` and each contains multiple documents.
2. Ensure the downloaded test files are present in `download-recommendations/`.
3. Move or copy one downloaded file at a time into the user's Downloads folder (the folder EAC watches).
4. Wait for the Enterprise AI Companion to detect the file.
5. Record the recommendation (target folder or "no recommendation").
6. Record the confidence label/score.
7. Record whether the assistant identified the correct project.
8. For duplicate/updated files, check whether the assistant identifies the existing document and the update relationship.
9. Compare the result against `FILE_ORGANIZATION_GROUND_TRUTH.md`.
10. Repeat for every file and total the score below.

## Scorecard

Track, per file:

- Correct project classification
- Incorrect classification
- Correct rejection (unrelated files)
- Correct ambiguity detection
- Duplicate detection
- Updated-version detection
- Confidence accuracy
- Explanation quality

### Scoring Model

| Points | Condition |
| ------ | --------- |
| 2 | Correct classification AND correct confidence/action. |
| 1 | Correct project BUT incorrect confidence/action. |
| 0 | Incorrect project. |

Special cases:

- Completely unrelated file: 2 points if the assistant correctly recommends no project.
- Ambiguous file: 2 points if it correctly identifies ambiguity (asks / low confidence) rather than blindly moving the file.
- Duplicate/update file: 2 points if it correctly identifies both the project AND the relationship to the existing document.

### Scorecard Template

| File | Category | Expected | Actual | Confidence | Duplicate Detected | Points (0/1/2) | Notes |
| ---- | -------- | -------- | ------ | ---------- | ------------------ | -------------- | ----- |

Maximum score = 2 × (number of downloadable files).

## Interpreting Results

- Category 1 (Obvious): sanity check. Failures indicate a broken pipeline.
- Category 2 (Semantic): tests content understanding beyond filenames.
- Category 3 (Ambiguous): tests calibrated uncertainty and human-in-the-loop behaviour.
- Category 4 (Wrong-project): tests that content overrides misleading filenames.
- Category 5 (Unrelated): tests that the system does not force every file into a project.
- Category 6 (Duplicate/Updated): tests version and duplicate detection against existing documents.
"""


def generate(test_drive_root: str) -> list[str]:
    written: list[str] = []
    gt_path = os.path.join(test_drive_root, "FILE_ORGANIZATION_GROUND_TRUTH.md")
    ti_path = os.path.join(test_drive_root, "TEST_INSTRUCTIONS.md")
    os.makedirs(test_drive_root, exist_ok=True)
    with open(gt_path, "w", encoding="utf-8") as fh:
        fh.write(GROUND_TRUTH)
    with open(ti_path, "w", encoding="utf-8") as fh:
        fh.write(TEST_INSTRUCTIONS)
    written.extend([gt_path, ti_path])
    return written
