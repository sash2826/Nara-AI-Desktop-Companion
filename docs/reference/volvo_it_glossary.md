# Volvo IT Terminology Glossary

Common terms used in Volvo IT for project planning and agile methodologies.

---

## Agile Framework Terms

| Term | Definition |
|------|------------|
| Scrum | Iterative agile framework using fixed-length sprints to deliver increments |
| SAFe (Scaled Agile Framework) | Enterprise-scale agile framework widely adopted across Volvo Group |
| Kanban | Flow-based method visualizing work on a board with WIP limits |
| Lean | Principles focused on eliminating waste and maximizing value delivery |
| Agile Release Train (ART) | Long-lived team-of-teams in SAFe that delivers value in a continuous flow |
| Program Increment (PI) | A SAFe timebox (typically 8–12 weeks) during which an ART delivers incremental value |
| PI Planning | Face-to-face or virtual event where ART teams align on objectives for the next PI |
| Iteration | A timebox (usually 2 weeks) within a PI where teams build and deliver stories |

---

## Roles

| Term | Definition |
|------|------------|
| Scrum Master (SM) | Servant-leader who facilitates Scrum events and removes impediments |
| Product Owner (PO) | Owns the team backlog, prioritizes work, and represents stakeholders |
| Release Train Engineer (RTE) | Facilitates ART-level events and processes; the "Scrum Master of the ART" |
| Solution Architect (SA) | Defines and communicates the technical vision across teams |
| Epic Owner (EO) | Shepherds an epic through the portfolio Kanban and drives its analysis |
| Business Owner (BO) | Senior stakeholder accountable for business outcomes of an ART |

---

## Backlog & Work Items

| Term | Definition |
|------|------------|
| Epic | Large body of work decomposed into features; managed at portfolio level |
| Feature | A service or capability that fulfills a stakeholder need; fits within a PI |
| User Story | Small, valuable increment described as "As a [role], I want [goal] so that [benefit]" |
| Enabler | Technical work (infrastructure, architecture, exploration) that supports future features |
| Spike | Time-boxed research or prototyping task to reduce uncertainty |
| Technical Debt | Accumulated shortcuts or suboptimal design that increases future cost of change |
| Backlog Refinement (Grooming) | Recurring session to clarify, estimate, and prioritize backlog items |
| Definition of Done (DoD) | Agreed checklist a work item must satisfy before it is considered complete |
| Definition of Ready (DoR) | Criteria a story must meet before it enters a sprint |
| Acceptance Criteria (AC) | Specific conditions under which a story is accepted by the PO |

---

## Ceremonies & Events

| Term | Definition |
|------|------------|
| Daily Stand-up | 15-minute daily sync: what I did, what I'll do, blockers |
| Sprint Planning | Session where the team commits to a set of stories for the upcoming sprint |
| Sprint Review (Demo) | End-of-sprint demonstration of completed work to stakeholders |
| Sprint Retrospective (Retro) | Team reflection on what went well, what didn't, and improvement actions |
| Inspect and Adapt (I&A) | SAFe event at PI end combining a demo, quantitative review, and problem-solving workshop |
| System Demo | ART-level demo of the integrated solution at the end of each iteration |
| Scrum of Scrums (SoS) | Cross-team sync to surface dependencies and blockers |

---

## Metrics & Tracking

| Term | Definition |
|------|------------|
| Velocity | Amount of work (story points) a team completes per sprint |
| Story Points (SP) | Relative estimate of effort, complexity, and risk for a backlog item |
| Burndown Chart | Graph showing remaining work vs. time in a sprint |
| Burnup Chart | Graph showing completed work vs. total scope over time |
| Cumulative Flow Diagram (CFD) | Visualization of work items across states over time |
| Cycle Time | Elapsed time from when work starts to when it finishes |
| Lead Time | Elapsed time from request to delivery |
| WIP Limit | Maximum number of items allowed in a workflow state to prevent overload |
| PI Objectives | SMART objectives each team commits to during PI Planning, scored 1–10 at PI end |

---

## Project Planning & Governance

| Term | Definition |
|------|------------|
| Tollgate (TG) | Stage-gate review in Volvo's project model (TG0–TG5) to approve progression |
| Volvo Technology Project Model (VTPM) | Volvo's structured project lifecycle model |
| Business Case (BC) | Justification document covering costs, benefits, risks, and timeline |
| Milestone (MS) | Key date marking a significant deliverable or decision point |
| RACI Matrix | Responsibility chart: Responsible, Accountable, Consulted, Informed |
| Risk Register (RR) | Log of identified risks with probability, impact, and mitigation plans |
| Change Request (CR) | Formal proposal to modify scope, schedule, or budget |
| Steering Committee (SteerCo) | Senior governance body that makes go/no-go decisions at tollgates |

---

## DevOps & Delivery

| Term | Definition |
|------|------------|
| Continuous Integration / Continuous Delivery (CI/CD) | Pipeline for automated build, test, and deploy |
| Release on Demand | Capability to deploy features to production when the business decides |
| Minimum Viable Product (MVP) | Smallest product increment that delivers value and enables learning |
| Increment | A usable, tested slice of the solution delivered at the end of a sprint or PI |
| DevOps | Culture and practices unifying development and operations for faster, reliable delivery |

---

## Collaboration & Tools

| Term | Definition |
|------|------------|
| Azure DevOps (ADO) | Primary ALM tool at Volvo IT for backlogs, boards, repos, and pipelines |
| Confluence | Wiki platform used for documentation and knowledge sharing |
| Jira | Alternative work-tracking tool used by some teams |
| Miro / Mural | Digital whiteboard tools used during PI Planning and workshops |
| Teams Channel | Microsoft Teams space for team communication and async collaboration |

---

> This glossary covers standard SAFe/Scrum terminology as used in Volvo IT.
> Local team or ART conventions (e.g. custom ADO work-item types, local governance steps) may vary — check your ART's Confluence wiki for additions.
