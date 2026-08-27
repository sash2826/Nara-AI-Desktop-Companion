"""Read-only audit of the real Documents (OneDrive) root.

This module inspects folder and file *metadata only* — names, extensions, sizes,
modification dates, and hierarchy depth. It never opens, reads, moves, renames,
or modifies any existing file. It is used to produce ``REAL_DOCUMENTS_AUDIT.md``.
"""

from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

# Safety caps so the walk stays fast and shallow on a large synced drive.
_MAX_FILES = 40000
_MAX_DEPTH = 6

_DOWNLOAD_HINT = re.compile(r"download|temp|inbox|to.?sort|unsorted|new folder", re.I)
_VERSION_HINT = re.compile(r"(_v\d+|\bv\d+\b|final|copy|draft|rev\b|\(\d+\))", re.I)
_PROJECT_DOC_EXT = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"}


def _mtime_str(ts: float) -> str:
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    except (OverflowError, OSError, ValueError):
        return "unknown"


def _scan_folder(root: str) -> dict:
    """Bounded, metadata-only walk of one top-level folder."""
    ext_counts: Counter[str] = Counter()
    file_count = 0
    dir_count = 0
    max_depth = 0
    latest = 0.0
    stems: dict[str, list[str]] = defaultdict(list)
    version_like: list[str] = []
    scanned = 0

    base_depth = root.rstrip(os.sep).count(os.sep)
    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath.count(os.sep) - base_depth
        if depth >= _MAX_DEPTH:
            dirnames[:] = []
            continue
        max_depth = max(max_depth, depth)
        dir_count += len(dirnames)
        for name in filenames:
            scanned += 1
            if scanned > _MAX_FILES:
                dirnames[:] = []
                break
            file_count += 1
            ext = os.path.splitext(name)[1].lower() or "(none)"
            ext_counts[ext] += 1
            if _VERSION_HINT.search(name):
                version_like.append(name)
            stem = _VERSION_HINT.sub("", os.path.splitext(name)[0]).strip().lower()
            if stem:
                stems[stem].append(name)
            try:
                mt = os.path.getmtime(os.path.join(dirpath, name))
                latest = max(latest, mt)
            except OSError:
                pass
        if scanned > _MAX_FILES:
            break

    doc_files = sum(ext_counts[e] for e in _PROJECT_DOC_EXT if e in ext_counts)
    version_clusters = {k: v for k, v in stems.items() if len(v) > 1}
    return {
        "file_count": file_count,
        "dir_count": dir_count,
        "max_depth": max_depth,
        "latest": latest,
        "ext_counts": ext_counts,
        "doc_files": doc_files,
        "version_like": version_like[:15],
        "version_clusters": version_clusters,
        "download_like": bool(_DOWNLOAD_HINT.search(os.path.basename(root))),
        "capped": scanned > _MAX_FILES,
    }


def audit_root(root: str, exclude: set[str]) -> str:
    """Produce the REAL_DOCUMENTS_AUDIT.md content for ``root`` (read-only)."""
    try:
        entries = sorted(os.scandir(root), key=lambda e: e.name.lower())
    except OSError as exc:
        return f"# Real Documents Audit\n\nUnable to scan `{root}`: {exc}\n"

    top_files: list[os.DirEntry] = []
    top_dirs: list[os.DirEntry] = []
    for e in entries:
        try:
            if e.is_dir(follow_symlinks=False):
                if e.name not in exclude:
                    top_dirs.append(e)
            elif e.is_file(follow_symlinks=False):
                top_files.append(e)
        except OSError:
            continue

    lines: list[str] = ["# Real Documents Audit\n",
                        f"Read-only, metadata-only audit of `{root}`.\n",
                        f"Generated: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}.\n",
                        "> No existing files were opened, moved, renamed, or modified. "
                        "Excludes benchmark-generated content.\n"]

    # Top-level overview
    lines.append("## Top-Level Structure\n")
    rows = []
    global_ext: Counter[str] = Counter()
    total_files = 0
    project_like: list[str] = []
    download_like: list[str] = []
    version_areas: list[str] = []

    for d in top_dirs:
        info = _scan_folder(d.path)
        total_files += info["file_count"]
        global_ext.update(info["ext_counts"])
        top_ext = ", ".join(f"{ext} {n}" for ext, n in info["ext_counts"].most_common(4)) or "—"
        rows.append([
            d.name,
            str(info["file_count"]) + ("+" if info["capped"] else ""),
            str(info["max_depth"]),
            _mtime_str(info["latest"]) if info["latest"] else "—",
            top_ext,
        ])
        if info["doc_files"] >= 5:
            project_like.append(f"{d.name} ({info['doc_files']} office documents)")
        if info["download_like"]:
            download_like.append(d.name)
        if info["version_clusters"]:
            sample = next(iter(info["version_clusters"].values()))
            version_areas.append(f"{d.name} (e.g. {', '.join(sample[:2])})")

    lines.append(_md_table(
        ["Top-Level Folder", "Files (bounded)", "Max Depth", "Latest Change", "Top File Types"],
        rows))

    if top_files:
        lines.append("\n### Loose Files in Root\n")
        loose_rows = []
        for f in top_files[:50]:
            try:
                st = f.stat(follow_symlinks=False)
                loose_rows.append([f.name, f"{st.st_size:,} B", _mtime_str(st.st_mtime)])
            except OSError:
                loose_rows.append([f.name, "—", "—"])
        lines.append(_md_table(["File", "Size", "Modified"], loose_rows))

    # File-type distribution
    lines.append("\n## File-Type Distribution (scanned folders)\n")
    lines.append(_md_table(
        ["Extension", "Count"],
        [[ext, str(n)] for ext, n in global_ext.most_common(20)] or [["—", "0"]]))
    lines.append(f"\nApproximate files scanned across top-level folders: **{total_files:,}** "
                 f"(bounded at {_MAX_FILES:,} per folder, depth {_MAX_DEPTH}).\n")

    # Observations
    lines.append("\n## Potential Project Folders\n")
    lines.append(_bullet_list(project_like) if project_like
                 else "No folders with a dense set of office documents were detected within the bounded scan.\n")

    lines.append("\n## Potentially Unorganized / Download-Like Areas\n")
    combined = download_like + [f.name for f in top_files]
    lines.append(_bullet_list(
        ([f"Download-like folder name: {n}" for n in download_like]
         + ([f"{len(top_files)} loose file(s) directly in the root"] if top_files else [])))
        if combined else "No obvious download-like areas detected.\n")

    lines.append("\n## Duplicate / Version Indicators\n")
    lines.append(_bullet_list(version_areas) if version_areas
                 else "No version-suffixed filename clusters detected within the bounded scan.\n")

    lines.append("\n## Folder-Depth Observations\n")
    depths = [int(r[2]) for r in rows] or [0]
    lines.append(f"- Deepest scanned top-level folder depth: {max(depths)} (cap {_MAX_DEPTH}).\n"
                 f"- Top-level folders scanned: {len(top_dirs)}.\n"
                 f"- Loose files directly in root: {len(top_files)}.\n")

    lines.append("\n## General Observations\n")
    obs = [
        "Organization quality varies by folder; some are dense document sets while others are shallow.",
        "Version-suffixed filenames indicate manual versioning rather than a controlled system where present.",
        "Loose files in the root are candidates for the assistant's Workflow A (existing unorganized files).",
        "This audit is structural only; document contents were not read.",
    ]
    lines.append(_bullet_list(obs))

    return "\n".join(lines)


def _md_table(header: list[str], rows: list[list[str]]) -> str:
    out = "| " + " | ".join(header) + " |\n"
    out += "| " + " | ".join(["---"] * len(header)) + " |\n"
    for row in rows:
        out += "| " + " | ".join(str(c).replace("|", "\\|") for c in row) + " |\n"
    return out


def _bullet_list(items: list[str]) -> str:
    return "".join(f"- {i}\n" for i in items)
