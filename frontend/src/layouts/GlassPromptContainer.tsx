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
 * The toggle shortcut is wired at two levels:
 *
 * 1. In Tauri: Ctrl+Shift+Space registered via tauri-plugin-global-shortcut
 *    (lib.rs). Fires even when another app is in the foreground. Ctrl+K was
 *    abandoned because it is owned exclusively by Teams/Slack via Win32
 *    RegisterHotKey and cannot be overridden.
 *
 * 2. In browser / Vite dev mode: Ctrl+Shift+Space via document keydown.
 *
 * Both paths call `toggle()` on the glassPromptStore.
 */
export function GlassPromptContainer() {
  const { isOpen, close, toggle } = useGlassPromptStore();

  // ── In-window shortcut (browser / Vite dev only) ────────────────────────────
  // Skipped in Tauri — the system-level global shortcut covers all states and
  // a second listener would cause double-toggle when the window has focus.
  useEffect(() => {
    if (IS_TAURI) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.ctrlKey && e.shiftKey && e.code === "Space") {
        e.preventDefault();
        toggle();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [toggle]);

  // ── System-level Ctrl+Shift+Space via Tauri global shortcut ─────────────────
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
