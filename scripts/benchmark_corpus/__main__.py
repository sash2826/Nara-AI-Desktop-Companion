"""Entry point that generates the full benchmark corpus and validates it.

Run with:
    python -m scripts.benchmark_corpus
"""

from __future__ import annotations

import os

from . import downloads, manifest
from . import project_atlas, project_aurora, project_horizon, project_northstar, project_polaris

ONEDRIVE = os.path.join(os.path.expanduser("~"), "OneDrive - Volvo Group")
TEST_DRIVE = os.path.join(ONEDRIVE, "test-drive")
DOWNLOADS = os.path.join(ONEDRIVE, "download-recommendations")

PROJECT_MODULES = [
    project_aurora,
    project_northstar,
    project_horizon,
    project_atlas,
    project_polaris,
]

# Duplicate download -> existing project file it updates (for validation).
DUPLICATE_MAP = {
    "Aurora_Technical_Architecture_v2.pdf": "Aurora-Mobility/Technical_Architecture.pdf",
    "Data_Platform_Requirements_RevB.docx": "Northstar-Analytics/Data_Platform_Requirements.docx",
    "Warehouse_Requirements_Updated.pdf": "Horizon-Logistics/Warehouse_Requirements.pdf",
    "Access_Control_Plan_v2.pdf": "Atlas-Workplace/Access_Control_Plan.pdf",
    "Carbon_Reporting_Framework_2026_Update.pdf": "Polaris-Sustainability/Carbon_Reporting_Framework.pdf",
}

CATEGORY_COUNTS = {
    "Obvious": 5,
    "Semantic": 5,
    "Ambiguous": 5,
    "Wrong-project": 4,
    "Unrelated": 3,
    "Duplicate/Updated": 5,
}


def main() -> None:
    print("Generating existing project corpus under:", TEST_DRIVE)
    project_files: list[str] = []
    for module in PROJECT_MODULES:
        files = module.generate(TEST_DRIVE)
        project_files.extend(files)
        print(f"  {module.PROJECT}: {len(files)} documents")

    print("\nGenerating download-recommendation corpus under:", DOWNLOADS)
    os.makedirs(DOWNLOADS, exist_ok=True)
    download_files = downloads.generate(DOWNLOADS)
    print(f"  download files: {len(download_files)}")

    print("\nGenerating ground-truth manifest and test instructions")
    manifest_files = manifest.generate(TEST_DRIVE)
    for path in manifest_files:
        print("  ", os.path.basename(path))

    # --- Validation ---------------------------------------------------------
    print("\n--- Validation ---")
    errors: list[str] = []

    for path in project_files + download_files + manifest_files:
        if not os.path.exists(path):
            errors.append(f"Missing expected file: {path}")

    for module in PROJECT_MODULES:
        proj_dir = os.path.join(TEST_DRIVE, module.PROJECT)
        count = len([n for n in os.listdir(proj_dir) if os.path.isfile(os.path.join(proj_dir, n))])
        if count < 2:
            errors.append(f"Project {module.PROJECT} has fewer than 2 documents ({count})")

    for dup_name, existing_rel in DUPLICATE_MAP.items():
        if not os.path.exists(os.path.join(DOWNLOADS, dup_name)):
            errors.append(f"Duplicate download missing: {dup_name}")
        if not os.path.exists(os.path.join(TEST_DRIVE, *existing_rel.split("/"))):
            errors.append(f"Existing doc for duplicate missing: {existing_rel}")

    if os.path.isdir(DOWNLOADS):
        subdirs = [n for n in os.listdir(DOWNLOADS) if os.path.isdir(os.path.join(DOWNLOADS, n))]
        if subdirs:
            errors.append(f"download-recommendations must be flat; found subfolders: {subdirs}")

    if errors:
        print("VALIDATION FAILED:")
        for err in errors:
            print("  -", err)
    else:
        print("All validation checks passed.")

    # --- Directory tree -----------------------------------------------------
    print("\n--- test-drive/ tree ---")
    _print_tree(TEST_DRIVE)
    print("\n--- download-recommendations/ (flat) ---")
    for name in sorted(os.listdir(DOWNLOADS)):
        print("  ", name)

    # --- Summary ------------------------------------------------------------
    total = len(project_files) + len(download_files) + len(manifest_files)
    print("\n--- Classification Summary ---")
    print(f"Existing project documents : {len(project_files)}")
    print(f"Downloadable test documents: {len(download_files)}")
    for label, count in CATEGORY_COUNTS.items():
        print(f"  {label:<18}: {count}")
    print(f"Manifest / instruction docs: {len(manifest_files)}")
    print(f"TOTAL generated files      : {total}")


def _print_tree(root: str) -> None:
    for entry in sorted(os.listdir(root)):
        full = os.path.join(root, entry)
        if os.path.isdir(full):
            print(f"  {entry}/")
            for child in sorted(os.listdir(full)):
                print(f"      {child}")
        else:
            print(f"  {entry}")


if __name__ == "__main__":
    main()
