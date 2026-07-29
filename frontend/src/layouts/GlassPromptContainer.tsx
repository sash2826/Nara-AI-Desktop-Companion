import { useEffect } from "react";
import { useGlassPromptStore } from "@/store/glassPromptStore";
import { GlassPrompt } from "@/components/glass-prompt/GlassPrompt";
import { GlassPromptBody } from "@/components/glass-prompt/GlassPromptBody";

/**
 * Mounts the GlassPrompt overlay and connects it to the glassPromptStore.
 *
 * Also owns the Ctrl+K global keyboard shortcut. The listener is registered
 * here (not inside GlassPrompt) because GlassPromptContainer is always
 * mounted, so the shortcut works even when the prompt is closed.
 *
 * Note: this shortcut fires only while the Tauri window is focused. A
 * system-level shortcut that works from any foreground app is a Phase 01
 * Tauri global-shortcut item.
 */
export function GlassPromptContainer() {
  const { isOpen, close, toggle } = useGlassPromptStore();

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.ctrlKey && e.key === "k") {
        e.preventDefault();
        toggle();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [toggle]);

  return (
    <GlassPrompt isOpen={isOpen} onClose={close}>
      <GlassPromptBody />
    </GlassPrompt>
  );
}
