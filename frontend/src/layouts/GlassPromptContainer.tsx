import { useEffect } from "react";
import { useGlassPromptStore } from "@/store/glassPromptStore";
import { GlassPrompt } from "@/components/glass-prompt/GlassPrompt";
import { GlassPromptBody } from "@/components/glass-prompt/GlassPromptBody";

// Tauri event API — only available inside a Tauri bundle.
// In the Vite dev server (browser context) this import is mocked or absent,
// so we guard every call behind a runtime check.
const IS_TAURI = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

/**
 * Mounts the GlassPrompt overlay and connects it to the glassPromptStore.
 *
 * Ctrl+K is wired at two levels:
 *
 * 1. In-window keydown listener (always active while the Tauri window is focused).
 *    Handles the common case with zero latency.
 *
 * 2. Tauri `toggle-glass-prompt` event (system-level, fires even when another
 *    app is in the foreground). Emitted by the Rust global-shortcut handler
 *    registered in lib.rs via tauri-plugin-global-shortcut.
 *
 * Both paths call `toggle()` on the glassPromptStore, so the prompt opens and
 * closes consistently regardless of which trigger fired.
 */
export function GlassPromptContainer() {
  const { isOpen, close, toggle } = useGlassPromptStore();

  // ── In-window Ctrl+K ────────────────────────────────────────────────────────
  // Only active in browser / Vite dev mode. In Tauri the system-level global
  // shortcut (registered in lib.rs) covers both focused and unfocused states,
  // so we skip this listener to prevent double-toggle when the window has focus.
  useEffect(() => {
    if (IS_TAURI) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.ctrlKey && e.key === "k") {
        e.preventDefault();
        toggle();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [toggle]);

  // ── System-level Ctrl+K via Tauri global shortcut ───────────────────────────
  useEffect(() => {
    if (!IS_TAURI) return;

    let unlisten: (() => void) | null = null;

    import("@tauri-apps/api/event")
      .then(({ listen }) =>
        listen("toggle-glass-prompt", () => {
          toggle();
        })
      )
      .then((fn) => {
        unlisten = fn;
      })
      .catch((err: unknown) => {
        console.warn("[GlassPromptContainer] failed to register Tauri shortcut listener:", err);
      });

    return () => {
      unlisten?.();
    };
  }, [toggle]);

  return (
    <GlassPrompt isOpen={isOpen} onClose={close}>
      <GlassPromptBody />
    </GlassPrompt>
  );
}
