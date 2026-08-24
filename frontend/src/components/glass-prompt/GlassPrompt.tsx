import { useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface GlassPromptProps {
  /** Whether the prompt is currently visible. */
  isOpen: boolean;
  /** Called when the user requests the prompt to close (Escape, outside-click, close button). */
  onClose: () => void;
  /** Content rendered inside the prompt body (input, response area, etc.). */
  children?: React.ReactNode;
  className?: string;
}

const OVERLAY_VARIANTS = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
  exit: { opacity: 0 },
};

const PANEL_VARIANTS = {
  hidden: { opacity: 0, scale: 0.96, y: -8 },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { type: "spring" as const, stiffness: 420, damping: 30 },
  },
  exit: {
    opacity: 0,
    scale: 0.96,
    y: -8,
    transition: { duration: 0.15, ease: "easeIn" as const },
  },
};

/**
 * Glass Prompt — the primary conversational overlay of the AI Companion.
 *
 * Renders above all content in a fixed portal-style layer. Closes on Escape
 * or outside-click. Focus is trapped inside while open; the first focusable
 * child receives focus on open.
 *
 * Presentation only — no conversation logic. Conversation state is managed
 * by the parent through `children`.
 */
export function GlassPrompt({ isOpen, onClose, children, className }: GlassPromptProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Auto-focus the first focusable element inside the panel on open
  useEffect(() => {
    if (!isOpen) return;
    const panel = panelRef.current;
    if (!panel) return;
    const focusable = panel.querySelector<HTMLElement>(
      'input, textarea, button, [tabindex]:not([tabindex="-1"])'
    );
    focusable?.focus();
  }, [isOpen]);

  // Close when clicking the backdrop (outside the panel)
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          key="glass-prompt-backdrop"
          className="fixed inset-0 z-[--z-glass-prompt] flex items-start justify-center pt-[12vh]"
          variants={OVERLAY_VARIANTS}
          initial="hidden"
          animate="visible"
          exit="exit"
          transition={{ duration: 0.15 }}
          onClick={handleBackdropClick}
          aria-modal="true"
          role="dialog"
          aria-label="AI Companion prompt"
        >
          {/* Subtle backdrop tint — does not obscure desktop content */}
          <div className="absolute inset-0 bg-black/20 dark:bg-black/40" aria-hidden="true" />

          <motion.div
            ref={panelRef}
            key="glass-prompt-panel"
            variants={PANEL_VARIANTS}
            initial="hidden"
            animate="visible"
            exit="exit"
            className={cn(
              "relative z-10 w-full max-w-2xl mx-4",
              "rounded-2xl overflow-hidden",
              "border border-white/30 dark:border-white/10",
              "bg-white/90 dark:bg-neutral-900/90",
              "backdrop-blur-xl backdrop-saturate-150",
              "shadow-2xl shadow-black/25 dark:shadow-black/60",
              className
            )}
          >
            {/* Close button */}
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-3 top-3 z-10 h-7 w-7 rounded-full text-muted-foreground hover:text-foreground"
              onClick={onClose}
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </Button>

            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
