# Benchmark Scorecard — File Organisation

Auto-updated by `scripts/score_benchmark.py`. Last updated: 2026-08-14 07:26 UTC

## Running Total

| Metric | Value |
|--------|-------|
| Files tested | 27 / 27 |
| Points scored | 46 / 54 |
| Score % | 85% |

---

## Category 1 — Obvious Matches (scored 10 / 10)

| File | Expected | Actual Folder | Label | Pts | Notes |
|------|----------|---------------|-------|-----|-------|
| Aurora_Mobility_Charging_Deployment_Proposal.* | Aurora-Mobility | Aurora-Mobility | Likely (38%) | **2** | Correct ✓ (Likely) |
| Northstar_Dashboard_Requirements_Update.* | Northstar-Analytics | Northstar-Analytics | Likely (45%) | **2** | Correct ✓ (Likely) |
| Horizon_Warehouse_Optimization_Proposal.* | Horizon-Logistics | Horizon-Logistics | Likely (41%) | **2** | Correct ✓ (Likely) |
| Atlas_Meeting_Room_Technology_Proposal.* | Atlas-Workplace | Atlas-Workplace | Likely (59%) | **2** | Correct ✓ (Likely) |
| Polaris_Carbon_Reporting_Guidelines.* | Polaris-Sustainability | Polaris-Sustainability | Likely (47%) | **2** | Correct ✓ (Likely) |

---

## Category 2 — Semantic Matches (scored 6 / 10)

| File | Expected | Actual Folder | Label | Pts | Notes |
|------|----------|---------------|-------|-----|-------|
| Smart_Energy_Load_Management_Study.* | Aurora-Mobility | Aurora-Mobility | Likely (30%) | **2** | Correct ✓ (Likely) |
| Data_Quality_Monitoring_Framework.* | Northstar-Analytics | No rec | — | 0 | No recommendation shown |
| Warehouse_Demand_Forecasting_Model.* | Horizon-Logistics | Horizon-Logistics | Possible (15%) | 1 | Correct folder but low confidence (Possible) |
| Workspace_Access_Experience_Study.* | Atlas-Workplace | Atlas-Workplace | Possible (23%) | 1 | Correct folder but low confidence (Possible) |
| Supplier_Emissions_Data_Framework.* | Polaris-Sustainability | Polaris-Sustainability | Likely (34%) | **2** | Correct ✓ (Likely) |

---

## Category 3 — Ambiguous Matches (scored 10 / 10)

Pass = no recommendation OR low-confidence match to an acceptable folder.

| File | Acceptable Folders | Actual Folder | Label | Pts | Notes |
|------|--------------------|---------------|-------|-----|-------|
| Enterprise_Data_Governance_Guide.* | Northstar / Polaris | Polaris-Sustainability | Possible (22%) | **2** | Low-confidence match to acceptable folder Polaris-Sustainability ✓ |
| Energy_Consumption_Analytics_Report.* | Aurora / Polaris | Aurora-Mobility | Likely (31%) | **2** | Low-confidence match to acceptable folder Aurora-Mobility ✓ |
| Operations_Performance_Review.* | Horizon / Northstar | Horizon-Logistics | Possible (18%) | **2** | Low-confidence match to acceptable folder Horizon-Logistics ✓ |
| Access_Security_Architecture.* | Atlas / Aurora | Atlas-Workplace | Possible (12%) | **2** | Low-confidence match to acceptable folder Atlas-Workplace ✓ |
| Vendor_Performance_Framework.* | any | Northstar-Analytics | Possible (19%) | **2** | Low-confidence match to acceptable folder Northstar-Analytics ✓ |

---

## Category 4 — Wrong-Project Matches (scored 7 / 8)

| File | Filename Suggests | Correct Folder | Actual Folder | Label | Pts | Notes |
|------|------------------|----------------|---------------|-------|-----|-------|
| Aurora_Analytics_Dashboard.* | Aurora-Mobility | Northstar-Analytics | Northstar-Analytics | Possible (11%) | 1 | Correct folder but low confidence (Possible) |
| Horizon_Employee_Workplace_Report.* | Horizon-Logistics | Atlas-Workplace | Atlas-Workplace | Likely (34%) | **2** | Correct ✓ (Likely) |
| Polaris_Logistics_Data_Report.* | Polaris-Sustainability | Horizon-Logistics | Horizon-Logistics | Likely (38%) | **2** | Correct ✓ (Likely) |
| Atlas_Sustainability_Review.* | Atlas-Workplace | Polaris-Sustainability | Polaris-Sustainability | Likely (42%) | **2** | Correct ✓ (Likely) |

---

## Category 5 — Unrelated Files (scored 6 / 6)

Pass = no recommendation shown.

| File | Expected | Actual Folder | Pts | Notes |
|------|----------|---------------|-----|-------|
| Personal_Travel_Insurance.* | No recommendation | No rec | **2** | Correct rejection ✓ |
| Home_Garden_Improvement_Budget.* | No recommendation | No rec | **2** | Correct rejection ✓ |
| Photography_Equipment_Guide.* | No recommendation | No rec | **2** | Correct rejection ✓ |

---

## Category 6 — Duplicate / Updated Versions (scored 7 / 10)

| Downloaded File | Correct Folder | Actual Folder | Label | Pts | Notes |
|----------------|----------------|---------------|-------|-----|-------|
| Aurora_Technical_Architecture_v2.* | Aurora-Mobility | Aurora-Mobility | Possible (14%) | 1 | Correct folder but low confidence (Possible) |
| Data_Platform_Requirements_RevB.* | Northstar-Analytics | Atlas-Workplace | Possible (20%) | 0 | Wrong folder → Atlas-Workplace (expected Northstar-Analytics) |
| Warehouse_Requirements_Updated.* | Horizon-Logistics | Horizon-Logistics | Likely (38%) | **2** | Correct ✓ (Likely) |
| Access_Control_Plan_v2.* | Atlas-Workplace | Atlas-Workplace | Likely (34%) | **2** | Correct ✓ (Likely) |
| Carbon_Reporting_Framework_2026_Update.* | Polaris-Sustainability | Polaris-Sustainability | Most Likely (63%) | **2** | Correct ✓ (Most Likely) |
