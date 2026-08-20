import { motion } from "framer-motion";
import volvoLogo from "@/assets/volvo-logo.svg";

interface EmptyChatStateProps {
  onQuickPrompt: (text: string) => void;
}

export function EmptyChatState({ onQuickPrompt: _ }: EmptyChatStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center select-none"
    >
      {/* Volvo logo */}
      <motion.img
        src={volvoLogo}
        alt="Volvo"
        aria-hidden="true"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, delay: 0.05, ease: "easeOut" }}
        className="h-10 w-10 opacity-25 dark:invert"
      />

      {/* Brand name */}
      <motion.h1
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.35, delay: 0.15 }}
        className="text-2xl font-semibold tracking-tight text-foreground"
      >
        Nara
      </motion.h1>

      {/* Tagline */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.35, delay: 0.25 }}
        className="text-sm text-muted-foreground/60"
      >
        Your workspace, within reach.
      </motion.p>
    </motion.div>
  );
}
