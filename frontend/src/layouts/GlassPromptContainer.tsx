import { useGlassPromptStore } from "@/store/glassPromptStore";
import { GlassPrompt } from "@/components/glass-prompt/GlassPrompt";
import { GlassPromptBody } from "@/components/glass-prompt/GlassPromptBody";

/**
 * Mounts the GlassPrompt overlay and connects it to the glassPromptStore.
 *
 * Kept as a thin layout wrapper so App.tsx remains declarative and the
 * GlassPrompt component stays free of store dependencies.
 */
export function GlassPromptContainer() {
  const { isOpen, close } = useGlassPromptStore();

  return (
    <GlassPrompt isOpen={isOpen} onClose={close}>
      <GlassPromptBody />
    </GlassPrompt>
  );
}
