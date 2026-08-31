# Phase 08: Orb Native Shell

**Phase:** 08

**Status:** Planned

**Estimated Duration:** 3–5 Days

---

# Purpose

This phase transforms the Living Orb from an element inside the Document-Management-RAG-Graph-Agent Tauri window into a standalone always-on-top desktop widget that remains visible regardless of whether the main application is open.

The orb is the primary ambient interface surface for the Document-Management-RAG-Graph-Agent. All file organisation prompts, AI query shortcuts, and notification states are delivered through it.

---

# Objectives

Upon completion of this phase the application should provide:

* A separate always-on-top Tauri WebviewWindow for the orb.
* Liquid Glass visual design applied to the orb shell and all floating overlays.
* Five distinct animation states reflecting system activity.
* Single-click to open an inline query overlay growing out of the orb.
* Double-click to open or focus the full Document-Management-RAG-Graph-Agent main window.
* Inline response rendering with an "Open in Document-Management-RAG-Graph-Agent" escalation button.
* Amber notification glow state when file placement recommendations are pending.
* Orb auto-starts with Windows on login.
* Orb persists across main window close/open cycles.
* Orb position persisted per-monitor; freely draggable across monitors.

---

# Prerequisites

Before beginning this phase:

* Phases 00 through 06 must be complete.
* Pre-08 SQLite graph correctness fixes must be applied.
* The existing orbStore and OrbContainer components must be understood before refactoring.

---

# Design Decisions

All decisions below were settled during the Phase 08 grilling session (2026-08-11).

## Window Architecture

The orb runs as a second Tauri `WebviewWindow` distinct from the main application window.

Properties:
* `always_on_top: true`
* `decorations: false`
* `transparent: true`
* `skip_taskbar: true`
* Window size matches the orb bounding box plus overlay expansion space.

The main window and orb window communicate via Tauri IPC events, not shared React state.

## Visual Design — Liquid Glass

The orb, its query overlay, and all floating notification prompts use the Liquid Glass aesthetic:
* Frosted glass backdrop (`backdrop-filter: blur`)
* Subtle border highlight simulating glass edge refraction
* Translucent fill that picks up the desktop wallpaper colour

The main Document-Management-RAG-Graph-Agent application window retains its current dark theme. Liquid Glass applies only to the orb shell layer. The Volvo/Scandinavian main app design is a separate decision deferred to a later phase.

## Animation States

| State | Trigger | Visual |
|---|---|---|
| Idle | Document-Management-RAG-Graph-Agent running, nothing pending | Slow breathing pulse, fixed circle |
| Listening | User clicked orb, overlay open | Energetic wave/ripple, morphing blob |
| Processing | Query submitted, awaiting response | Spinning/morphing, morphing blob |
| Notification Pending | File placement recommendations waiting | Gentle persistent amber glow, fixed circle |
| Error | Backend unreachable or query failed | Brief red pulse, fixed circle |

Technology: CSS animations + SVG filters + Framer Motion for state transitions. The orb morphs between circle and blob form for Listening and Processing states only.

## Interaction Model

* **Single click** → compact query overlay grows out of the orb. Stays floating. Dismisses on submit or Escape.
* **Double click** → open/focus the main Document-Management-RAG-Graph-Agent window.
* **Click when Notification Pending** → overlay shows pending file placement recommendations list instead of query input.
* **Drag** → orb repositions; position persisted to orbStore per-monitor.

## Query Overlay

* Compact text input attached visually to the orb.
* Response rendered inline below the input (max ~5 lines before scroll).
* "Open in Document-Management-RAG-Graph-Agent" button escalates the conversation to the full main window.
* Overlay does not persist — dismissed after response is acknowledged or on Escape.

## Startup Behaviour

The orb process registers itself in the Windows startup registry (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`) on first launch. It remains running as a background process when the main Document-Management-RAG-Graph-Agent window is closed.

---

# Architecture

## New Files

```
frontend/src/windows/orb/
    OrbWindow.tsx               — Root component for the standalone orb window
    OrbShell.tsx                — Liquid Glass shell, drag handling, animation state machine
    OrbAnimationEngine.tsx      — SVG filter definitions + Framer Motion variants for 5 states
    OrbQueryOverlay.tsx         — Inline query input + response renderer
    OrbNotificationOverlay.tsx  — Pending recommendations list overlay
    orbWindowStore.ts           — Zustand store for orb window state (animation state, pending count)
frontend/src-tauri/src/
    orb_window.rs               — Tauri command to create/focus the orb WebviewWindow
```

## Modified Files

```
frontend/src-tauri/tauri.conf.json      — Register second window
frontend/src-tauri/src/lib.rs           — Wire orb_window commands, startup registration
frontend/src/store/orbStore.ts          — Extend with per-monitor position persistence
frontend/src/components/orb/            — Retain for in-app fallback only; orb logic moves to windows/orb/
```

---

# Deliverables

* Standalone always-on-top orb WebviewWindow.
* Liquid Glass visual shell.
* Five-state animation engine.
* Click/double-click interaction model.
* Inline query overlay with escalation.
* Notification pending state wired to file organisation recommendation count.
* Windows startup registration.
* Multi-monitor position persistence.

---

# Completion Criteria

* Orb remains visible above all other application windows.
* Orb survives main Document-Management-RAG-Graph-Agent window close and reopen.
* Orb starts automatically on Windows login.
* All five animation states trigger correctly.
* Single click opens query overlay; response renders inline.
* Double click opens main Document-Management-RAG-Graph-Agent window.
* Orb position is remembered per monitor.
* Amber glow appears when file placement recommendations are pending.
* Liquid Glass visual is applied to orb and overlays.

---

# Dependencies

Requires:
* Phase 00 through Phase 06
* Pre-08 graph correctness fixes

Provides the notification surface for:
* Phase 09 (file placement recommendations)
* Phase 10 (passive reorganisation suggestions)

---

# Related Documentation

* `docs/decisions/ADR-001-Desktop-Architecture.md`
* `docs/decisions/ADR-007-IPC-Communication.md`
* `docs/implementation/Phase-09-File-Organisation-New-Files.md`

---

# Next Phase

After completing this phase, proceed to:

**Phase 09: File Organisation — New Files**
