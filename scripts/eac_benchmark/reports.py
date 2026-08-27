"""Markdown report generation for the benchmark.

Every report is derived from the same :mod:`scripts.eac_benchmark.catalog`
objects that produce the documents, so the answer key stays consistent with the
generated corpus.
"""

from __future__ import annotations

import os

from .catalog import CATEGORY_LABELS, TestFile
from .data import PROJECTS, PROJECTS_BY_KEY, Project


def _disp(key: str | None) -> str:
    if key is None:
        return "—"
    p = PROJECTS_BY_KEY.get(key)
    return p.display if p else key


def _md_table(header: list[str], rows: list[list[str]]) -> str:
    line = "| " + " | ".join(header) + " |\n"
    line += "| " + " | ".join(["---"] * len(header)) + " |\n"
    for row in rows:
        cells = [str(c).replace("|", "\\|") for c in row]
        line += "| " + " | ".join(cells) + " |\n"
    return line


def _by_cat(files: list[TestFile], cat: str) -> list[TestFile]:
    return [f for f in files if f.category == cat]


def _related_existing(f: TestFile) -> str:
    """Best-effort list of existing project docs relevant to this test file."""
    if f.existing_file:
        return f.existing_file
    if f.expected_project:
        return f"{f.expected_project}/ (project document set)"
    if f.candidates:
        return "; ".join(f"{c}/" for c in f.candidates)
    return "none"


# --- Downloads ground truth --------------------------------------------------
def write_download_ground_truth(path: str, downloads: list[TestFile]) -> None:
    parts: list[str] = ["# File Organization Ground Truth\n",
                        "Answer key for every file in `synthetic-downloads/`. "
                        "Generated from the benchmark catalogue.\n"]

    parts.append("## 1. Obvious Matches\n")
    parts.append(_md_table(
        ["File", "Expected Project", "Expected Action", "Confidence", "Reason"],
        [[f.filename, _disp(f.expected_project), f.expected_action, f.confidence, f.reason]
         for f in _by_cat(downloads, "obvious")]))

    parts.append("\n## 2. Semantic Matches\n")
    parts.append(_md_table(
        ["File", "Expected Project", "Expected Action", "Confidence", "Semantic Evidence"],
        [[f.filename, _disp(f.expected_project), f.expected_action, f.confidence, f.semantic_evidence]
         for f in _by_cat(downloads, "semantic")]))

    parts.append("\n## 3. Ambiguous Matches\n")
    amb_rows = []
    for f in _by_cat(downloads, "ambiguous"):
        c1 = _disp(f.candidates[0]) if len(f.candidates) > 0 else "—"
        c2 = _disp(f.candidates[1]) if len(f.candidates) > 1 else "—"
        extra = f" (+{len(f.candidates) - 2} more)" if len(f.candidates) > 2 else ""
        amb_rows.append([f.filename, c1, c2 + extra, f.expected_action, f.confidence, f.reason])
    parts.append(_md_table(
        ["File", "Candidate Project 1", "Candidate Project 2", "Expected Action", "Confidence", "Reason"],
        amb_rows))

    parts.append("\n## 4. Wrong-Project Matches\n")
    parts.append(_md_table(
        ["File", "Misleading Filename", "Actual Project", "Expected Action", "Reason"],
        [[f.filename, "Yes", _disp(f.expected_project), f.expected_action, f.reason]
         for f in _by_cat(downloads, "wrong")]))

    parts.append("\n## 5. Completely Unrelated\n")
    parts.append(_md_table(
        ["File", "Expected Action", "Reason"],
        [[f.filename, f.expected_action, f.reason]
         for f in _by_cat(downloads, "unrelated")]))

    parts.append("\n## 6. Duplicate / Updated Versions\n")
    parts.append(_md_table(
        ["Downloaded File", "Existing File", "Project", "Relationship", "Expected Action"],
        [[f.filename, f.existing_file, _disp(f.expected_project), f.relationship, f.expected_action]
         for f in _by_cat(downloads, "duplicate")]))

    _write(path, "\n".join(parts))


# --- Floating ground truth ---------------------------------------------------
def write_floating_ground_truth(path: str, floating: list[TestFile]) -> None:
    parts: list[str] = ["# Floating File Ground Truth\n",
                        "Answer key for the unorganized files placed directly in the "
                        "OneDrive root (Workflow A — existing unorganized files).\n"]

    parts.append("## All Floating Files\n")
    rows = []
    for f in floating:
        rows.append([f.filename, CATEGORY_LABELS[f.category], _disp(f.expected_project),
                     f.expected_action, f.confidence, f.reason])
    parts.append(_md_table(
        ["File", "Category", "Expected Project", "Expected Action", "Confidence", "Reason"], rows))

    dup = [f for f in floating if f.category == "duplicate"]
    if dup:
        parts.append("\n## Duplicate / Updated Mapping\n")
        parts.append(_md_table(
            ["Floating File", "Existing File", "Relationship"],
            [[f.filename, f.existing_file, f.relationship] for f in dup]))

    _write(path, "\n".join(parts))


# --- Test matrix (downloads) -------------------------------------------------
def write_test_matrix(path: str, downloads: list[TestFile]) -> None:
    parts: list[str] = ["# Download Test Matrix\n",
                        "Human-readable matrix of every file in `synthetic-downloads/`.\n"]
    rows = []
    for f in downloads:
        rows.append([
            f.filename,
            CATEGORY_LABELS[f.category],
            _disp(f.expected_project),
            f.expected_action,
            f.confidence,
            f.reason,
            _related_existing(f),
            "Yes" if f.misleading_filename else "No",
            "Yes" if f.semantic_required else "No",
        ])
    parts.append(_md_table(
        ["Filename", "Category", "Expected Project", "Expected Action", "Expected Confidence",
         "Why", "Relevant Existing Documents", "Misleading Filename", "Semantic Analysis Required"],
        rows))
    _write(path, "\n".join(parts))


# --- Scorecard ---------------------------------------------------------------
def write_scorecard(path: str, downloads: list[TestFile], floating: list[TestFile]) -> None:
    def count(files: list[TestFile], cat: str) -> int:
        return len(_by_cat(files, cat))

    parts: list[str] = ["# Benchmark Scorecard\n",
                        "Record the Enterprise AI Companion's results against the ground "
                        "truth using the metrics below. Tally one point per file that matches "
                        "the expected outcome, then compute each rate.\n"]

    parts.append("## Dataset Sizes\n")
    parts.append(_md_table(
        ["Category", "Downloads", "Floating"],
        [[CATEGORY_LABELS[c], str(count(downloads, c)), str(count(floating, c))]
         for c in ["obvious", "semantic", "ambiguous", "wrong", "unrelated", "duplicate"]]
        + [["**Total**", str(len(downloads)), str(len(floating))]]))

    parts.append("\n## Metrics and Formulas\n")
    metrics = [
        ("1. Project Classification Accuracy",
         "Correct project assignments / total classifiable files",
         "Classifiable = obvious + semantic + wrong + duplicate (files with one true project)."),
        ("2. Semantic Classification Accuracy",
         "Correct project on semantic files / total semantic files",
         "Isolates cases where the filename does not reveal the project."),
        ("3. Ambiguity Detection Accuracy",
         "Ambiguous files correctly flagged (ASK_USER / low confidence) / total ambiguous files",
         "Rewards not auto-moving genuinely ambiguous files."),
        ("4. Wrong-Project Rejection Accuracy",
         "Wrong-project files routed to the true project / total wrong-project files",
         "Measures content understanding over filename keywords."),
        ("5. Unrelated File Rejection Accuracy",
         "Unrelated files with NO_RECOMMENDATION / total unrelated files",
         "Rewards correctly declining to file personal/off-topic documents."),
        ("6. Duplicate Detection Accuracy",
         "Duplicate/updated files linked to the correct existing document / total duplicate files",
         "Existing document correctly identified."),
        ("7. Updated-Version Detection Accuracy",
         "Duplicate files with the correct relationship label / total duplicate files",
         "DUPLICATE vs UPDATED_VERSION vs REVISED_VERSION vs POSSIBLE_DUPLICATE."),
        ("8. Confidence Calibration",
         "Files where reported confidence band matches the expected band / total files",
         "High/Medium/Low/None as recorded in the ground truth."),
        ("9. Recommendation Precision",
         "Correct move recommendations / total move recommendations made",
         "Penalises confident moves that are wrong (including unrelated files moved)."),
        ("10. Recommendation Recall",
         "Correct move recommendations / total files that should be moved",
         "Should-move = obvious + semantic + wrong + duplicate + their floating equivalents."),
    ]
    parts.append(_md_table(
        ["Metric", "Formula", "Notes"],
        [[m, f, n] for m, f, n in metrics]))

    parts.append("\n## Per-Category Results (fill in during testing)\n")
    parts.append(_md_table(
        ["Category", "Total", "Correct", "Accuracy"],
        [[CATEGORY_LABELS[c], str(count(downloads, c) + count(floating, c)), "", ""]
         for c in ["obvious", "semantic", "ambiguous", "wrong", "unrelated", "duplicate"]]))

    parts.append("\n## Overall Results (fill in during testing)\n")
    parts.append(_md_table(
        ["Metric", "Value"],
        [[m.split(". ", 1)[1], ""] for m, _f, _n in metrics]))

    _write(path, "\n".join(parts))


# --- Real-world test guide ---------------------------------------------------
def write_test_guide(path: str) -> None:
    content = """# Real-World Test Guide

This guide explains how to benchmark the Enterprise AI Companion against the two
workflows this corpus is designed to exercise.

## Workflows

- **Workflow A — Existing unorganized file.** A file already sits directly in
  `C:\\Users\\A533062\\OneDrive - Volvo Group` (the floating files). The assistant
  should detect that it is unorganized and recommend a suitable project folder.
- **Workflow B — New download.** A file appears in
  `C:\\Users\\A533062\\OneDrive - Volvo Group\\My Videos\\download test files`.
  The assistant should analyse it and recommend a destination.

Treat these as two separate benchmark scenarios and score them independently.

## Setup

1. Establish the synthetic project folders as the "known" corpus. Point the
   Enterprise AI Companion at
   `Enterprise-AI-Companion-Benchmark/synthetic-projects/` so the eight projects
   are indexed.
2. Start the Enterprise AI Companion and let indexing complete.
3. Confirm the monitored Downloads folder is configured.

## Workflow B — one download at a time

1. Copy **one** file from `My Videos/download test files` into the application's
   monitored Downloads folder.
2. Wait for the application to detect the new file.
3. Record: recommendation, confidence, suggested destination, and whether related
   existing documents were identified.
4. Approve or reject the recommendation.
5. Compare against `ground-truth/FILE_ORGANIZATION_GROUND_TRUTH.md`.
6. Repeat for the next file.

Do **not** test all files simultaneously — the goal is to observe individual
recommendations.

## Workflow A — floating files

1. Run the assistant's organize/audit function over the OneDrive root (read-only
   analysis; do not let it auto-move).
2. For each floating file, record the recommendation and confidence.
3. Compare against `ground-truth/FLOATING_FILE_GROUND_TRUTH.md`.

## Scoring

Transfer results into `reports/BENCHMARK_SCORECARD.md` and compute each metric.
Pay particular attention to:

- Wrong-project files (content must beat filename).
- Ambiguous files (should ask, not auto-move).
- Unrelated files (should decline).
- Duplicate/updated files (must link to the correct existing document).
"""
    _write(path, content)


# --- README ------------------------------------------------------------------
def write_readme(path: str, downloads: list[TestFile], floating: list[TestFile],
                 docs_per_project: int) -> None:
    def count(files: list[TestFile], cat: str) -> int:
        return len(_by_cat(files, cat))

    project_rows = [[p.display, p.domain] for p in PROJECTS]

    content = f"""# Enterprise AI Companion — File Organization Benchmark

A synthetic benchmark corpus for evaluating whether an AI file organizer can
understand an existing Documents environment and the semantic relationship
between newly downloaded files and existing projects.

All content is fictional. No real personal, customer, or Volvo-internal
information is used.

## Purpose

Evaluate file understanding, project detection, semantic classification,
download detection, migration recommendations, duplicate/updated-version
detection, cross-document relationships, confidence scoring, and correct
rejection of unrelated files.

## Dataset Structure

```
Enterprise-AI-Companion-Benchmark/
  synthetic-projects/     8 projects, {docs_per_project} documents each
  synthetic-downloads/    {len(downloads)} download test files
  audit/                  read-only audit of the real Documents folder
  ground-truth/           answer keys (downloads + floating)
  reports/                scorecard, test guide, this summary
```

Floating (unorganized) test files are generated **directly in the OneDrive
root**, not inside this benchmark directory, to exercise Workflow A.

## Projects

{_md_table(["Project", "Domain"], project_rows)}

Each project contains {docs_per_project} cross-referenced documents (overview,
requirements, architecture/operating model, vendor evaluation, deployment plan,
meeting notes, risk assessment, status report, budget, timeline, and an overview
presentation) spanning PDF, DOCX, XLSX, and PPTX.

## Test Files

Downloads ({len(downloads)}):

{_md_table(["Category", "Count"], [[CATEGORY_LABELS[c], str(count(downloads, c))] for c in ["obvious", "semantic", "ambiguous", "wrong", "unrelated", "duplicate"]])}

Floating ({len(floating)}):

{_md_table(["Category", "Count"], [[CATEGORY_LABELS[c], str(count(floating, c))] for c in ["obvious", "semantic", "ambiguous", "wrong", "unrelated", "duplicate"]])}

## Ground Truth

- `ground-truth/FILE_ORGANIZATION_GROUND_TRUTH.md` — downloads answer key.
- `ground-truth/FLOATING_FILE_GROUND_TRUTH.md` — floating-files answer key.
- `ground-truth/TEST_MATRIX.md` — full download test matrix.

## How to Run and Score

See `reports/REAL_WORLD_TEST_GUIDE.md` for the step-by-step workflow and
`reports/BENCHMARK_SCORECARD.md` for the metrics and formulas.
"""
    _write(path, content)


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
