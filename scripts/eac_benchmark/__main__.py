"""Benchmark generator entry point.

Orchestrates the read-only audit, corpus generation, floating-file generation,
report writing, validation, and summary. Run from the repository root::

    python -m scripts.eac_benchmark

Optional flags::

    --root PATH   Override the OneDrive root (default: two levels above the repo).
    --dry-run     Resolve paths and print the plan without writing files.
"""

from __future__ import annotations

import argparse
import os
import sys

from .audit import audit_root
from .builders import generate_project
from .catalog import CATEGORY_LABELS, all_downloads, all_floating
from .data import PROJECTS
from .generate import write_test_file
from .reports import (
    write_download_ground_truth,
    write_floating_ground_truth,
    write_readme,
    write_scorecard,
    write_test_guide,
    write_test_matrix,
)

DOCS_PER_PROJECT = 11
BENCH_DIRNAME = "Enterprise-AI-Companion-Benchmark"
DOWNLOAD_REL = os.path.join("My Videos", "download test files")


def _default_root() -> str:
    # scripts/eac_benchmark/__main__.py -> repo root is three parents up.
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(here))
    return os.path.dirname(repo_root)  # the OneDrive - Volvo Group folder


def _ensure_dirs(*paths: str) -> None:
    for p in paths:
        os.makedirs(p, exist_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the EAC file-organization benchmark.")
    parser.add_argument("--root", default=_default_root(), help="OneDrive root directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without writing files.")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    bench = os.path.join(root, BENCH_DIRNAME)
    projects_dir = os.path.join(bench, "synthetic-projects")
    downloads_dir = os.path.join(bench, "synthetic-downloads")
    audit_dir = os.path.join(bench, "audit")
    ground_dir = os.path.join(bench, "ground-truth")
    reports_dir = os.path.join(bench, "reports")
    downloads_test_dir = os.path.join(root, DOWNLOAD_REL)

    downloads = all_downloads()
    floating = all_floating()

    print(f"Root:            {root}")
    print(f"Benchmark:       {bench}")
    print(f"Downloads dir:   {downloads_test_dir}")
    print(f"Projects:        {len(PROJECTS)} x {DOCS_PER_PROJECT} docs")
    print(f"Download files:  {len(downloads)}")
    print(f"Floating files:  {len(floating)}")

    if not os.path.isdir(root):
        print(f"ERROR: root does not exist: {root}", file=sys.stderr)
        return 2

    if args.dry_run:
        print("\n[dry-run] No files written.")
        return 0

    # 1. Read-only audit FIRST, excluding our own generated areas.
    print("\n[1/6] Auditing real Documents root (read-only)...")
    audit_md = audit_root(root, exclude={BENCH_DIRNAME, "My Videos"})

    # 2. Create benchmark directory structure.
    print("[2/6] Creating benchmark directories...")
    _ensure_dirs(projects_dir, downloads_dir, audit_dir, ground_dir, reports_dir, downloads_test_dir)
    _write(os.path.join(audit_dir, "REAL_DOCUMENTS_AUDIT.md"), audit_md)

    # 3. Generate project corpus.
    print("[3/6] Generating synthetic projects...")
    project_files = 0
    for project in PROJECTS:
        written = generate_project(project, projects_dir)
        project_files += len(written)
        print(f"    - {project.display}: {len(written)} documents")

    # 4. Generate downloads and floating files.
    print("[4/6] Generating download and floating test files...")
    for tf in downloads:
        write_test_file(tf, downloads_dir)
    for tf in floating:
        write_test_file(tf, root)  # directly in the OneDrive root
    print(f"    - {len(downloads)} downloads, {len(floating)} floating")

    # 5. Ground truth and reports.
    print("[5/6] Writing ground truth and reports...")
    write_download_ground_truth(os.path.join(ground_dir, "FILE_ORGANIZATION_GROUND_TRUTH.md"), downloads)
    write_floating_ground_truth(os.path.join(ground_dir, "FLOATING_FILE_GROUND_TRUTH.md"), floating)
    write_test_matrix(os.path.join(ground_dir, "TEST_MATRIX.md"), downloads)
    write_scorecard(os.path.join(reports_dir, "BENCHMARK_SCORECARD.md"), downloads, floating)
    write_test_guide(os.path.join(reports_dir, "REAL_WORLD_TEST_GUIDE.md"))
    write_readme(os.path.join(bench, "README.md"), downloads, floating, DOCS_PER_PROJECT)

    # 6. Validate and summarise.
    print("[6/6] Validating...")
    ok, problems = _validate(projects_dir, downloads_dir, root, downloads, floating)
    for msg in problems:
        print(f"    ! {msg}")

    _print_summary(downloads, floating, project_files, bench, root, downloads_test_dir)
    return 0 if ok else 1


def _validate(projects_dir, downloads_dir, root, downloads, floating):
    problems: list[str] = []

    for project in PROJECTS:
        pdir = os.path.join(projects_dir, project.key)
        if not os.path.isdir(pdir):
            problems.append(f"missing project folder: {project.key}")
            continue
        n = len([f for f in os.listdir(pdir) if os.path.isfile(os.path.join(pdir, f))])
        if n < DOCS_PER_PROJECT:
            problems.append(f"{project.key}: expected {DOCS_PER_PROJECT} docs, found {n}")

    for tf in downloads:
        if not os.path.isfile(os.path.join(downloads_dir, tf.filename)):
            problems.append(f"missing download: {tf.filename}")
    for tf in floating:
        if not os.path.isfile(os.path.join(root, tf.filename)):
            problems.append(f"missing floating file: {tf.filename}")

    # Duplicate files must reference an existing project doc (path or asset note).
    for tf in [*downloads, *floating]:
        if tf.category == "duplicate" and not tf.existing_file:
            problems.append(f"duplicate without existing_file: {tf.filename}")
    # Ambiguous files must have >=2 candidates.
    for tf in [*downloads, *floating]:
        if tf.category == "ambiguous" and len(tf.candidates) < 2:
            problems.append(f"ambiguous with <2 candidates: {tf.filename}")

    return (len(problems) == 0), problems


def _count(files, cat):
    return len([f for f in files if f.category == cat])


def _print_summary(downloads, floating, project_files, bench, root, downloads_test_dir):
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print(f" 1. Project folders created:        {len(PROJECTS)}")
    print(f" 2. Existing synthetic documents:   {project_files}")
    print(f" 3. Download test files:            {len(downloads)}")
    print(f" 4. Obvious matches (dl):           {_count(downloads, 'obvious')}")
    print(f" 5. Semantic matches (dl):          {_count(downloads, 'semantic')}")
    print(f" 6. Ambiguous matches (dl):         {_count(downloads, 'ambiguous')}")
    print(f" 7. Wrong-project matches (dl):     {_count(downloads, 'wrong')}")
    print(f" 8. Unrelated files (dl):           {_count(downloads, 'unrelated')}")
    print(f" 9. Duplicate/updated files (dl):   {_count(downloads, 'duplicate')}")
    print(f"10. Floating files:                 {len(floating)}")
    total = project_files + len(downloads) + len(floating)
    print(f"    Total benchmark files:          {total}")

    print("\nFloating breakdown:")
    for c in ["obvious", "semantic", "ambiguous", "wrong", "unrelated", "duplicate"]:
        print(f"    - {CATEGORY_LABELS[c]:<28} {_count(floating, c)}")

    print("\nDirectory tree:")
    print(f"{root}")
    print("├── (floating test files: {} generated directly in root)".format(len(floating)))
    print(f"├── {os.path.relpath(downloads_test_dir, root)}/   ({len(downloads)} download files)")
    print(f"└── {os.path.basename(bench)}/")
    print("    ├── README.md")
    print("    ├── synthetic-projects/")
    for project in PROJECTS:
        print(f"    │   ├── {project.key}/   ({DOCS_PER_PROJECT} documents)")
    print("    ├── synthetic-downloads/   ({} files)".format(len(downloads)))
    print("    ├── audit/")
    print("    │   └── REAL_DOCUMENTS_AUDIT.md")
    print("    ├── ground-truth/")
    print("    │   ├── FILE_ORGANIZATION_GROUND_TRUTH.md")
    print("    │   ├── FLOATING_FILE_GROUND_TRUTH.md")
    print("    │   └── TEST_MATRIX.md")
    print("    └── reports/")
    print("        ├── BENCHMARK_SCORECARD.md")
    print("        └── REAL_WORLD_TEST_GUIDE.md")


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


if __name__ == "__main__":
    raise SystemExit(main())
