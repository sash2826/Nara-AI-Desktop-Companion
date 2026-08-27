import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { ORB_SIZE } from "@/theme/orbTheme";
import { useOrbWindowStore } from "./orbWindowStore";
import { OrbSvgFilters, OrbSphere } from "./OrbAnimationEngine";
import { OrbQueryOverlay } from "./OrbQueryOverlay";
import { OrbNotificationOverlay } from "./OrbNotificationOverlay";
import { OrbAmbientBubble } from "./OrbAmbientBubble";
import { useOrbAmbientMessages } from "./useOrbAmbientMessages";

// How long a pointer must be stationary after mousedown before we treat it as
// the start of a drag rather than a click.
const DRAG_THRESHOLD_PX = 4;
const DOUBLE_CLICK_MS = 300;
// Small margin around the interactive bounds so edge clicks aren't lost.
const HIT_REGION_PADDING = 6;

const STATUS_DOT_COLOR: Record<string, string> = {
  idle: "hsl(142 70% 45%)",
  listening: "hsl(142 70% 50%)",
  processing: "hsl(210 100% 60%)",
  notification: "hsl(38 95% 55%)",
  error: "hsl(0 84% 60%)",
};

const STATUS_LABEL: Record<string, string> = {
  idle: "Online",
  listening: "Listening",
  processing: "Processing",
  error: "Error",
};

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
    notificationsViewed,
    setOverlayMode,
    setPendingCount,
    setAnimationState,
    markNotificationsViewed,
  } = useOrbWindowStore();

  const [isHovered, setIsHovered] = useState(false);
  // True between mousedown and mouseup — the window must stay interactive for
  // the whole drag even when the cursor leaves the orb's hit region.
  const [isPointerDown, setIsPointerDown] = useState(false);
  const anchorRef = useRef<HTMLDivElement>(null);

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

    // Poll every 4s so new recommendations appear in the orb promptly.
    const pollInterval = setInterval(() => {
      invoke<number>("get_pending_recommendation_count")
        .then((count) => setPendingCount(count))
        .catch(() => {});
    }, 4_000);

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
    setIsPointerDown(true);
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
      setIsPointerDown(false);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, []);

  // ── Click-through region ───────────────────────────────────────────────────
  // The orb window is much larger than the orb itself so overlays have room.
  // Report the actual interactive bounds so Rust can make the rest of the
  // window transparent to clicks.
  useEffect(() => {
    const reportHitRegion = () => {
      const anchor = anchorRef.current;
      if (!anchor) return;

      if (isPointerDown) {
        invoke("set_orb_hit_region", {
          x: 0,
          y: 0,
          width: window.innerWidth,
          height: window.innerHeight,
        }).catch(() => {});
        return;
      }

      const base = anchor.getBoundingClientRect();
      let { left, top, right, bottom } = base;

      // Overlays are absolutely positioned, so they sit outside the anchor's box.
      anchor.querySelectorAll<HTMLElement>("[data-orb-surface]").forEach((surface) => {
        const r = surface.getBoundingClientRect();
        left = Math.min(left, r.left);
        top = Math.min(top, r.top);
        right = Math.max(right, r.right);
        bottom = Math.max(bottom, r.bottom);
      });

      invoke("set_orb_hit_region", {
        x: left - HIT_REGION_PADDING,
        y: top - HIT_REGION_PADDING,
        width: right - left + HIT_REGION_PADDING * 2,
        height: bottom - top + HIT_REGION_PADDING * 2,
      }).catch(() => {});
    };

    reportHitRegion();
    // Overlays animate open/closed, so re-measure until they settle.
    const interval = setInterval(reportHitRegion, 150);
    window.addEventListener("resize", reportHitRegion);
    return () => {
      clearInterval(interval);
      window.removeEventListener("resize", reportHitRegion);
    };
  }, [overlayMode, isPointerDown]);

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

      // After the first auto-open, single click always goes to query.
      // Suggestions are accessible via the chip inside the query overlay.
      setOverlayMode("query");
    },
    [overlayMode, setOverlayMode]
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

  // ── Ambient speech bubble ─────────────────────────────────────────────────
  const ambientMessage = useOrbAmbientMessages({ pendingCount, overlayMode });

  // ── Auto-open notification overlay on first arrival of suggestions ──────────
  useEffect(() => {
    if (pendingCount > 0 && !notificationsViewed && overlayMode === "none") {
      setOverlayMode("notifications");
      markNotificationsViewed();
    }
  }, [pendingCount, notificationsViewed, overlayMode, setOverlayMode, markNotificationsViewed]);

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
        paddingBottom: 36,
        paddingRight: 24,
        position: "relative",
        background: "transparent",
        userSelect: "none",
        WebkitUserSelect: "none",
        // Window is larger than the orb to give overlays room; only real
        // controls should capture clicks so the desktop stays reachable.
        pointerEvents: "none",
      }}
    >
      <OrbSvgFilters />

      {/* Orb hit-target + overlays anchor */}
      <div ref={anchorRef} style={{ position: "relative", pointerEvents: "auto" }}>
        {/* Ambient speech bubble — hidden while any overlay is open */}
        <AnimatePresence>
          {ambientMessage && overlayMode === "none" && (
            <OrbAmbientBubble key={ambientMessage.text} message={ambientMessage} />
          )}
        </AnimatePresence>

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
                borderRadius: 999,
                background: "hsl(38 95% 55%)",
                border: "1.5px solid hsl(0 0% 12%)",
                fontSize: 10,
                fontWeight: 700,
                color: "hsl(0 0% 10%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "0 4px",
                boxSizing: "border-box",
                fontFamily: "system-ui, sans-serif",
                pointerEvents: "none",
              }}
            >
              {pendingCount > 99 ? "99+" : pendingCount}
            </div>
          )}
        </AnimatePresence>

        {/* Status line — anchored inside the orb div so left:50% always means
            the orb's own centre, regardless of window width or paddingRight.
            Not shown for the notification state; the badge count covers it. */}
        <AnimatePresence>
          {animationState !== "notification" && (
            <div
              style={{
                position: "absolute",
                top: "calc(100% + 8px)",
                left: "50%",
                transform: "translateX(-50%)",
                pointerEvents: "none",
              }}
            >
              <motion.div
                key={animationState}
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.2 }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 5,
                  whiteSpace: "nowrap",
                }}
              >
                <motion.span
                  animate={{ opacity: animationState === "idle" ? 1 : [1, 0.25, 1] }}
                  transition={{ duration: 1.1, repeat: Infinity, ease: "easeInOut" }}
                  style={{
                    display: "inline-block",
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: STATUS_DOT_COLOR[animationState] ?? "hsl(var(--muted-foreground))",
                    flexShrink: 0,
                  }}
                />
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 500,
                    color: "hsl(var(--popover-foreground) / 0.7)",
                    fontFamily: "var(--font-sans), system-ui, sans-serif",
                    letterSpacing: "0.01em",
                  }}
                >
                  {STATUS_LABEL[animationState] ?? animationState}
                </span>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
