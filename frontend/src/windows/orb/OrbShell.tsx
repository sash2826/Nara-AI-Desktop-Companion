import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { ORB_SIZE } from "@/theme/orbTheme";
import { useOrbWindowStore } from "./orbWindowStore";
import { OrbSvgFilters, OrbSphere } from "./OrbAnimationEngine";
import { OrbQueryOverlay } from "./OrbQueryOverlay";
import { OrbNotificationOverlay } from "./OrbNotificationOverlay";

// How long a pointer must be stationary after mousedown before we treat it as
// the start of a drag rather than a click.
const DRAG_THRESHOLD_PX = 4;
const DOUBLE_CLICK_MS = 300;

/**
 * OrbShell — the root visual and interaction layer for the standalone orb window.
 *
 * Responsibilities:
 *   - Drag handling (updates orb position via Tauri set_position)
 *   - Click detection (single vs double)
 *   - Overlay switching (query vs notifications)
 *   - Listening for backend events (pending_count_changed)
 *   - Compositing: Liquid Glass backdrop + OrbSphere + overlay
 */
export function OrbShell() {
  const {
    animationState,
    overlayMode,
    pendingCount,
    setOverlayMode,
    setPendingCount,
    setAnimationState,
  } = useOrbWindowStore();

  const [isHovered, setIsHovered] = useState(false);

  // ── Drag state ─────────────────────────────────────────────────────────────
  // Cached orb window position — avoids an IPC round-trip on every mousedown.
  const orbPos = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const dragStart = useRef<{
    screenX: number;
    screenY: number;
    windowX: number;
    windowY: number;
  } | null>(null);
  const isDragging = useRef(false);
  const rafPending = useRef(false);
  // Screen position recorded on mousedown — used to detect drag vs click.
  const dragStartScreen = useRef<{ x: number; y: number } | null>(null);
  const lastClickTime = useRef(0);

  // ── Backend event listener for pending recommendation count ────────────────
  useEffect(() => {
    let unlistenFn: (() => void) | null = null;

    listen<number>("orb-pending-count", (event) => {
      setPendingCount(event.payload);
    }).then((unlisten) => {
      unlistenFn = unlisten;
    });

    // Fetch initial count on mount
    invoke<number>("get_pending_recommendation_count")
      .then((count) => setPendingCount(count))
      .catch(() => {
        /* sidecar not yet ready — ignore */
      });

    // Poll every 30s so the amber badge appears without needing a Tauri event push.
    const pollInterval = setInterval(() => {
      invoke<number>("get_pending_recommendation_count")
        .then((count) => setPendingCount(count))
        .catch(() => {});
    }, 30_000);

    return () => {
      unlistenFn?.();
      clearInterval(pollInterval);
    };
  }, [setPendingCount]);

  // ── Seed orb position cache on mount ──────────────────────────────────────
  useEffect(() => {
    invoke<{ x: number; y: number }>("get_orb_position")
      .then((pos) => {
        orbPos.current = pos;
      })
      .catch(() => {});
  }, []);

  // ── Drag handlers ──────────────────────────────────────────────────────────
  // Position is cached so mousedown is instant (no IPC wait).
  // Mousemove updates are throttled via rAF and fire-and-forget so there is no
  // growing backlog of awaited IPC calls at 125 Hz.

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return;
    e.preventDefault();
    dragStartScreen.current = { x: e.screenX, y: e.screenY };
    dragStart.current = {
      screenX: e.screenX,
      screenY: e.screenY,
      windowX: orbPos.current.x,
      windowY: orbPos.current.y,
    };
    isDragging.current = false;
  }, []);

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!dragStart.current) return;

      // Use screenX/Y — absolute screen coords that don't shift as the window moves.
      const dx = e.screenX - dragStart.current.screenX;
      const dy = e.screenY - dragStart.current.screenY;

      if (!isDragging.current) {
        if (Math.abs(dx) < DRAG_THRESHOLD_PX && Math.abs(dy) < DRAG_THRESHOLD_PX) return;
        isDragging.current = true;
      }

      // Update local cache immediately so the next rAF sends the freshest position.
      orbPos.current = {
        x: dragStart.current.windowX + dx,
        y: dragStart.current.windowY + dy,
      };

      // Throttle IPC calls to one per animation frame — fire-and-forget.
      if (!rafPending.current) {
        rafPending.current = true;
        requestAnimationFrame(() => {
          rafPending.current = false;
          invoke("set_orb_position", {
            x: Math.round(orbPos.current.x),
            y: Math.round(orbPos.current.y),
          }).catch(() => {});
        });
      }
    };

    const onMouseUp = () => {
      dragStart.current = null;
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, []);

  // ── Click handlers ─────────────────────────────────────────────────────────

  const handleClick = useCallback(
    (e?: React.MouseEvent) => {
      // Ignore click if the cursor moved significantly (drag ended here)
      if (dragStartScreen.current) {
        const dx = Math.abs((e?.screenX ?? 0) - dragStartScreen.current.x);
        const dy = Math.abs((e?.screenY ?? 0) - dragStartScreen.current.y);
        dragStartScreen.current = null;
        if (dx > DRAG_THRESHOLD_PX || dy > DRAG_THRESHOLD_PX) return;
      }

      const now = Date.now();
      const timeSinceLastClick = now - lastClickTime.current;
      lastClickTime.current = now;

      if (timeSinceLastClick < DOUBLE_CLICK_MS) {
        // Double-click → focus main window
        invoke("focus_main_window").catch(() => {});
        setOverlayMode("none");
        return;
      }

      // Single click logic
      if (overlayMode !== "none") {
        // Toggle off
        setOverlayMode("none");
        return;
      }

      if (pendingCount > 0 && animationState === "notification") {
        setOverlayMode("notifications");
      } else {
        setOverlayMode("query");
      }
    },
    [animationState, overlayMode, pendingCount, setOverlayMode]
  );

  // ── Keyboard activation (accessibility) ───────────────────────────────────

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleClick();
      }
    },
    [handleClick]
  );

  // ── Error recovery: reset error state after 2s ─────────────────────────────
  useEffect(() => {
    if (animationState !== "error") return;
    const t = setTimeout(() => {
      setAnimationState(pendingCount > 0 ? "notification" : "idle");
    }, 2000);
    return () => clearTimeout(t);
  }, [animationState, pendingCount, setAnimationState]);

  return (
    /*
     * Outer wrapper fills the entire transparent orb window.
     * The orb sphere sits in the bottom-right corner; overlays expand
     * leftward into the remaining window width.
     */
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "flex-end",
        paddingBottom: 8,
        paddingRight: 8,
        position: "relative",
        background: "transparent",
        userSelect: "none",
        WebkitUserSelect: "none",
      }}
    >
      <OrbSvgFilters />

      {/* Orb hit-target + overlays anchor */}
      <div style={{ position: "relative" }}>
        {/* Overlays rendered above the orb */}
        <AnimatePresence>
          {overlayMode === "query" && <OrbQueryOverlay key="query" />}
          {overlayMode === "notifications" && <OrbNotificationOverlay key="notifications" />}
        </AnimatePresence>

        {/* The draggable orb button */}
        <button
          type="button"
          aria-label="Nara"
          data-orb-state={animationState}
          onMouseDown={handleMouseDown}
          onClick={handleClick}
          onKeyDown={handleKeyDown}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          onFocus={() => setIsHovered(true)}
          onBlur={() => setIsHovered(false)}
          style={{
            position: "relative",
            width: ORB_SIZE,
            height: ORB_SIZE,
            borderRadius: "50%",
            background: "transparent",
            border: "none",
            padding: 0,
            cursor: "grab",
            outline: "none",
          }}
        >
          {/* Liquid Glass backdrop ring — frosted glass effect around the sphere */}
          <div
            aria-hidden="true"
            style={{
              position: "absolute",
              inset: -4,
              borderRadius: "50%",
              background: "hsl(0 0% 100% / 0.06)",
              backdropFilter: "blur(12px) saturate(160%)",
              WebkitBackdropFilter: "blur(12px) saturate(160%)",
              border: "1px solid hsl(0 0% 100% / 0.12)",
              boxShadow: "inset 0 1px 0 hsl(0 0% 100% / 0.18)",
              transition: "opacity 0.3s ease",
              opacity: isHovered ? 1 : 0.7,
            }}
          />
          {/* Animated sphere */}
          <OrbSphere state={animationState} isHovered={isHovered} />
        </button>

        {/* Notification badge (pending count) */}
        <AnimatePresence>
          {pendingCount > 0 && (
            <div
              style={{
                position: "absolute",
                top: -2,
                right: -2,
                minWidth: 16,
                height: 16,
                borderRadius: 8,
                background: "hsl(38 95% 55%)",
                border: "1.5px solid hsl(0 0% 12%)",
                fontSize: 10,
                fontWeight: 700,
                color: "hsl(0 0% 10%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "0 3px",
                fontFamily: "system-ui, sans-serif",
                pointerEvents: "none",
              }}
            >
              {pendingCount > 9 ? "9+" : pendingCount}
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
