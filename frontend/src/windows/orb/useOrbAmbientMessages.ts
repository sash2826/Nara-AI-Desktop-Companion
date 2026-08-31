import { useEffect, useLayoutEffect, useRef, useState } from "react";

export type AmbientMessage =
  | { kind: "greeting"; text: string }
  | { kind: "nudge"; text: string }
  | { kind: "reminder"; text: string };

type Phase = "greeting" | "nudge" | "reminder" | "cooldown";

// ---------------------------------------------------------------------------
// Message content
// ---------------------------------------------------------------------------

// Keep each nudge short enough to fit the single-line ambient pill.
const NUDGES = [
  "Ask me anything about your files",
  "Try: find documents on a topic",
  "I can suggest where new files go",
  "Ask me to summarise a document",
  "Explore your knowledge graph",
  "Try: which files relate to a project?",
  "I can audit your folder organisation",
  "Ask me to find anything you've indexed",
  "Try: what changed recently in my files",
  "Trace topics and people across files",
];

function getGreeting(): string {
  const h = new Date().getHours();
  if (h >= 5 && h < 12)
    return h < 9 ? "Good morning, ready when you are" : "Morning — what can I help you find?";
  if (h >= 12 && h < 17) return h < 14 ? "Good afternoon" : "Afternoon — what can I help with?";
  if (h >= 17 && h < 22) return h < 19 ? "Good evening" : "Evening — anything on your mind?";
  return "Still here — ready when you are";
}

function reminderText(count: number): string {
  return `You have ${count} file${count !== 1 ? "s" : ""} to organise`;
}

// ---------------------------------------------------------------------------
// Timing
// ---------------------------------------------------------------------------

const GREETING_MS = 5_000;
const NUDGE_SHOW_MS = 9_000;
const NUDGE_GAP_MS = 4_000;
const REMINDER_DELAY_MS = 800;
const COOLDOWN_NUDGES = 2;

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useOrbAmbientMessages({
  pendingCount,
  overlayMode,
}: {
  pendingCount: number;
  overlayMode: string;
}): AmbientMessage | null {
  // Initialise with the greeting so the mount effect doesn't need to call
  // setMessage synchronously (avoids react-hooks/set-state-in-effect lint error).
  const [message, setMessage] = useState<AmbientMessage | null>(() => ({
    kind: "greeting",
    text: getGreeting(),
  }));

  const pendingRef = useRef(pendingCount);
  // Sync the latest pending count into the ref after every render so the
  // state-machine callbacks always see the current value without re-subscribing.
  useLayoutEffect(() => {
    pendingRef.current = pendingCount;
  });

  const phaseRef = useRef<Phase>("greeting");
  const nudgeIndexRef = useRef(0);
  const cooldownRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const prevOverlayRef = useRef(overlayMode);

  // Stable function refs set once on mount; other effects call through them.
  const clearTimerRef = useRef<() => void>(() => {});
  const scheduleNextRef = useRef<(delayMs: number) => void>(() => {});
  const showReminderRef = useRef<() => void>(() => {});

  // Skip first render in pendingCount/overlayMode effects — mount handles startup.
  const pendingInitRef = useRef(false);
  const overlayInitRef = useRef(false);

  // ── State machine — initialised once on mount ─────────────────────────────
  useEffect(() => {
    function clearTimer() {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    }

    function showReminder() {
      const count = pendingRef.current;
      phaseRef.current = "reminder";
      setMessage({ kind: "reminder", text: reminderText(count) });
      // No auto-dismiss — reminder persists until the overlay opens.
    }

    function scheduleNext(delayMs: number) {
      clearTimer();
      timerRef.current = setTimeout(() => {
        const pending = pendingRef.current;

        if (phaseRef.current === "cooldown") {
          cooldownRef.current -= 1;
          if (cooldownRef.current <= 0 && pending > 0) {
            showReminder();
            return;
          }
          if (cooldownRef.current <= 0) phaseRef.current = "nudge";
        } else {
          phaseRef.current = "nudge";
        }

        const text = NUDGES[nudgeIndexRef.current % NUDGES.length];
        nudgeIndexRef.current += 1;
        setMessage({ kind: "nudge", text });

        timerRef.current = setTimeout(() => {
          setMessage(null);
          scheduleNext(NUDGE_GAP_MS);
        }, NUDGE_SHOW_MS);
      }, delayMs);
    }

    clearTimerRef.current = clearTimer;
    scheduleNextRef.current = scheduleNext;
    showReminderRef.current = showReminder;

    // Greeting message is already set as initial state; just schedule the dismiss.
    timerRef.current = setTimeout(() => {
      setMessage(null);
      if (pendingRef.current > 0) {
        timerRef.current = setTimeout(() => showReminder(), NUDGE_GAP_MS);
      } else {
        scheduleNext(NUDGE_GAP_MS);
      }
    }, GREETING_MS);

    return clearTimer;
  }, []);

  // ── pendingCount changes ───────────────────────────────────────────────────
  useEffect(() => {
    if (!pendingInitRef.current) {
      pendingInitRef.current = true;
      return;
    }

    const phase = phaseRef.current;

    if (pendingCount > 0 && phase !== "reminder" && phase !== "cooldown") {
      clearTimerRef.current();
      setMessage(null);
      timerRef.current = setTimeout(() => showReminderRef.current(), REMINDER_DELAY_MS);
    }

    if (pendingCount === 0 && (phase === "reminder" || phase === "cooldown")) {
      clearTimerRef.current();
      phaseRef.current = "nudge";
      setMessage(null);
      scheduleNextRef.current(NUDGE_GAP_MS);
    }
  }, [pendingCount]);

  // ── overlayMode changes ────────────────────────────────────────────────────
  useEffect(() => {
    if (!overlayInitRef.current) {
      overlayInitRef.current = true;
      prevOverlayRef.current = overlayMode;
      return;
    }

    const prev = prevOverlayRef.current;
    prevOverlayRef.current = overlayMode;

    const justOpened = prev === "none" && overlayMode !== "none";
    const justClosed = prev !== "none" && overlayMode === "none";

    if (justOpened && phaseRef.current === "reminder") {
      // Dismiss bubble while overlay is open; phase stays "reminder" so
      // when it closes we know to start cooldown.
      setMessage(null);
    }

    if (justClosed && phaseRef.current === "reminder") {
      // Closed without acting — run cooldown nudge cycles first.
      setMessage(null);
      clearTimerRef.current();
      phaseRef.current = "cooldown";
      cooldownRef.current = COOLDOWN_NUDGES;
      scheduleNextRef.current(NUDGE_GAP_MS);
    }
  }, [overlayMode]);

  return message;
}
