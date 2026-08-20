import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const THINKING_WORDS = [
  "Thinking",
  "Combobulating",
  "Reasoning",
  "Analysing",
  "Processing",
  "Considering",
];

export function TypingIndicator() {
  const [wordIndex, setWordIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setWordIndex((i) => (i + 1) % THINKING_WORDS.length);
    }, 1800);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 4 }}
      transition={{ duration: 0.18 }}
      className="flex items-center gap-2 px-4 py-3 text-sm text-muted-foreground"
      aria-label="Assistant is thinking"
      aria-live="polite"
    >
      {/* Spinning asterisk — matches Claude's ✳ thinking indicator */}
      <motion.span
        animate={{ rotate: 360 }}
        transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        className="text-primary"
        aria-hidden="true"
        style={{ display: "inline-block", fontSize: "1rem", lineHeight: 1 }}
      >
        ✳
      </motion.span>

      {/* Rotating word */}
      <span className="relative h-5 overflow-hidden" style={{ minWidth: "7rem" }}>
        <AnimatePresence mode="wait">
          <motion.span
            key={wordIndex}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="absolute inset-0 flex items-center"
          >
            {THINKING_WORDS[wordIndex]}
            <span className="ml-px">…</span>
          </motion.span>
        </AnimatePresence>
      </span>
    </motion.div>
  );
}
